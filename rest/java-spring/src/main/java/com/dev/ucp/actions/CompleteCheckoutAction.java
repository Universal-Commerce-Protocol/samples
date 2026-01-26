/*
 * Copyright 2026 UCP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.dev.ucp.actions;

import com.dev.ucp.ExtensionsHelper;
import com.dev.ucp.InventoryManager;
import com.dev.ucp.OrderWebHookNotifier;
import com.dev.ucp.entities.OrderEntity;
import com.dev.ucp.exceptions.InvalidRequestException;
import com.dev.ucp.exceptions.PaymentFailedException;
import com.dev.ucp.service.shopping.model.CardPaymentInstrument;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CompleteCheckoutRequest;
import com.dev.ucp.service.shopping.model.FulfillmentGroupResponse;
import com.dev.ucp.service.shopping.model.FulfillmentMethodResponse;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.dev.ucp.service.shopping.model.MessageError;
import com.dev.ucp.service.shopping.model.OrderConfirmation;
import com.dev.ucp.service.shopping.model.PaymentCredential;
import com.dev.ucp.service.shopping.model.TokenCredentialResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/** Service for completing a checkout session, finalizing payment and creating an order. */
@Service
public class CompleteCheckoutAction
    extends BaseCheckoutAction<Map.Entry<String, CompleteCheckoutRequest>> {

  @Autowired private OrderEntity.Repository orderRepository;
  @Autowired private ExtensionsHelper extensionsHelper;
  @Autowired private InventoryManager inventoryManager;
  @Autowired private OrderWebHookNotifier webhookNotifier;

  public CheckoutResponse completeCheckout(
      String checkoutId,
      UUID idempotencyKey,
      CompleteCheckoutRequest completeCheckoutRequest,
      String webhookUrl) {
    CheckoutResponse checkout =
        execute(idempotencyKey, Map.entry(checkoutId, completeCheckoutRequest));
    webhookNotifier.notify(webhookUrl, checkout);
    return checkout;
  }

  @Override
  protected CheckoutResponse executeAction(Map.Entry<String, CompleteCheckoutRequest> params) {
    String checkoutId = params.getKey();
    CompleteCheckoutRequest request = params.getValue();
    CheckoutResponse checkout = loadCheckoutSession(checkoutId);
    ensureModifiable(checkout);

    if (checkout.getStatus() != CheckoutResponse.StatusEnum.READY_FOR_COMPLETE) {
      throw new InvalidRequestException("Checkout is not in ready to complete.");
    }

    processPayment(request);
    inventoryManager.reserveInventory(checkout);
    updateStatus(checkout);

    if (checkout.getStatus() != CheckoutResponse.StatusEnum.READY_FOR_COMPLETE) {
      saveCheckoutSession(checkoutId, checkout.getStatus().toString(), checkout);
      return checkout;
    }

    checkout.setStatus(CheckoutResponse.StatusEnum.COMPLETED);
    String orderId = UUID.randomUUID().toString();
    OrderConfirmation orderConfirmation = new OrderConfirmation();
    orderConfirmation.setId(orderId);
    try {
      orderConfirmation.setPermalinkUrl(new URI("https://example.com/orders/" + orderId));
    } catch (URISyntaxException e) {
      throw new RuntimeException("Error creating permalink URL", e);
    }
    checkout.setOrder(orderConfirmation);

    saveCheckoutSession(checkoutId, checkout.getStatus().toString(), checkout);
    saveOrder(orderId, checkout);

    return checkout;
  }

  private void processPayment(CompleteCheckoutRequest request) {
    CardPaymentInstrument instrument = request.getPaymentData();
    if (instrument == null) {
      throw new InvalidRequestException("Missing payment data");
    }

    String handlerId = instrument.getHandlerId();
    PaymentCredential credential = instrument.getCredential();

    if ("mock_payment_handler".equals(handlerId)) {
      if (credential instanceof TokenCredentialResponse tokenCredential) {
        JsonNode tokenNode = tokenCredential.getAdditionalProperty("token");
        if (tokenNode != null && "fail_token".equals(tokenNode.asText())) {
          throw new PaymentFailedException("Payment Failed: Insufficient Funds (Mock)");
        }
      }
    }
  }

  private void validateFulfillment(CheckoutResponse checkout) {
    FulfillmentResponse fulfillment = extensionsHelper.getFulfillmentResponse(checkout);
    boolean hasFulfillmentErrors = false;

    if (fulfillment == null
        || fulfillment.getMethods() == null
        || fulfillment.getMethods().isEmpty()) {
      MessageError error =
          new MessageError()
              .type(MessageError.TypeEnum.ERROR)
              .severity(MessageError.SeverityEnum.RECOVERABLE)
              .code("missing_fulfillment_info")
              .content("Fulfillment address and option must be selected")
              .path("$.fulfillment");
      checkout.addMessagesItem(error);
      hasFulfillmentErrors = true;
    } else {
      boolean optionSelected = false;
      for (FulfillmentMethodResponse method : fulfillment.getMethods()) {
        // If shipping type, check if selectedDestinationId is present
        if ("shipping".equals(method.getType()) && method.getSelectedDestinationId() == null) {
          // This is a potential error, but we want to collect all errors, so we don't return here.
          // Instead, we will add an error message and continue.
          MessageError error =
              new MessageError()
                  .type(MessageError.TypeEnum.ERROR)
                  .severity(MessageError.SeverityEnum.RECOVERABLE)
                  .code("missing_shipping_destination")
                  .content("Shipping destination must be selected for method: " + method.getId())
                  .path(
                      "$.fulfillment.methods[?(@.id=='"
                          + method.getId()
                          + "')].selected_destination_id");
          checkout.addMessagesItem(error);
          hasFulfillmentErrors = true;
        }

        // Check if an option is selected within any group for this method
        if (method.getGroups() != null) {
          for (FulfillmentGroupResponse group : method.getGroups()) {
            if (group.getSelectedOptionId() != null) {
              optionSelected = true;
              break;
            }
          }
        }
      }
      // If no option was selected across all methods/groups and no specific destination error was
      // already flagged
      if (!optionSelected && !hasFulfillmentErrors) {
        MessageError error =
            new MessageError()
                .type(MessageError.TypeEnum.ERROR)
                .severity(MessageError.SeverityEnum.RECOVERABLE)
                .code("missing_fulfillment_option")
                .content("At least one fulfillment option must be selected.")
                .path("$.fulfillment.methods"); // General path if no specific method is missing
        // options
        checkout.addMessagesItem(error);
        hasFulfillmentErrors = true;
      }
    }

    if (hasFulfillmentErrors) {
      checkout.setStatus(CheckoutResponse.StatusEnum.INCOMPLETE);
    }
  }

  private void saveOrder(String id, CheckoutResponse checkoutResponse) {
    OrderEntity entity = new OrderEntity();
    entity.setId(id);
    try {
      entity.setData(objectMapper.writeValueAsString(checkoutResponse));
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error processing checkout response", e);
    }
    orderRepository.save(entity);
  }

  @Override
  protected String getEndpoint() {
    return "/checkout-sessions/{id}/complete";
  }
}
