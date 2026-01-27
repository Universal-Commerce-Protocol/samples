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
import com.dev.ucp.FulfillmentManager;
import com.dev.ucp.LineItemConverter;
import com.dev.ucp.entities.CheckoutSessionEntity;
import com.dev.ucp.entities.DiscountEntity;
import com.dev.ucp.exceptions.CheckoutNotModifiableException;
import com.dev.ucp.exceptions.ResourceNotFoundException;
import com.dev.ucp.service.shopping.model.CardPaymentInstrument;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.DiscountRequest;
import com.dev.ucp.service.shopping.model.DiscountRequestAppliedInner;
import com.dev.ucp.service.shopping.model.DiscountResponse;
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.Message;
import com.dev.ucp.service.shopping.model.MessageError;
import com.dev.ucp.service.shopping.model.PaymentHandlerResponse;
import com.dev.ucp.service.shopping.model.PaymentResponse;
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;

/**
 * Base class for actions specifically targeting the UCP checkout session lifecycle.
 *
 * <p>Provides centralized logic for loading/saving checkout sessions, validating session state,
 * recalculating totals, and managing checkout status based on validation errors.
 *
 * @param <T> The type of the request payload.
 */
public abstract class BaseCheckoutAction<T> extends BaseAction<T, CheckoutResponse> {

  @Autowired protected CheckoutSessionEntity.Repository checkoutSessionRepository;
  @Autowired protected DiscountEntity.Repository discountRepository;
  @Autowired protected ExtensionsHelper extensionsHelper;
  @Autowired protected LineItemConverter lineItemConverter;
  @Autowired protected FulfillmentManager fulfillmentManager;

  @Override
  protected Class<CheckoutResponse> getResponseType() {
    return CheckoutResponse.class;
  }

  protected void ensureModifiable(CheckoutResponse checkout) {
    if (checkout.getStatus() == CheckoutResponse.StatusEnum.COMPLETED
        || checkout.getStatus() == CheckoutResponse.StatusEnum.CANCELED) {
      throw new CheckoutNotModifiableException(
          "Cannot update checkout in state " + checkout.getStatus());
    }
  }

  protected CheckoutResponse loadCheckoutSession(String checkoutId) {
    CheckoutSessionEntity entity =
        checkoutSessionRepository
            .findById(checkoutId)
            .orElseThrow(() -> new ResourceNotFoundException("Checkout session not found"));
    try {
      return objectMapper.readValue(entity.getData(), CheckoutResponse.class);
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error processing checkout data", e);
    }
  }

  protected void saveCheckoutSession(String id, String status, CheckoutResponse checkoutResponse) {
    CheckoutSessionEntity entity =
        checkoutSessionRepository.findById(id).orElse(new CheckoutSessionEntity());
    entity.setId(id);
    entity.setStatus(status);
    try {
      entity.setData(objectMapper.writeValueAsString(checkoutResponse));
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error processing checkout response", e);
    }
    checkoutSessionRepository.save(entity);
  }

  protected PaymentResponse convertPayment(
      CheckoutResponse checkout,
      List<CardPaymentInstrument> instruments,
      String selectedInstrumentId) {
    PaymentResponse resp = new PaymentResponse();
    resp.setSelectedInstrumentId(selectedInstrumentId);

    // Load handlers from discovery_profile.json
    try (InputStream inputStream =
        new ClassPathResource("discovery_profile.json").getInputStream()) {
      JsonNode discoveryProfile = objectMapper.readTree(inputStream);
      JsonNode paymentNode = discoveryProfile.get("payment");
      if (paymentNode != null && paymentNode.has("handlers")) {
        List<PaymentHandlerResponse> handlers = new ArrayList<>();
        for (JsonNode handlerNode : paymentNode.get("handlers")) {
          handlers.add(objectMapper.treeToValue(handlerNode, PaymentHandlerResponse.class));
        }
        resp.setHandlers(handlers);
      }
    } catch (IOException e) {
      throw new RuntimeException("Error reading discovery_profile.json for payment handlers", e);
    }

    resp.setInstruments(instruments);

    return resp;
  }

  /**
   * Initializes the totals for the checkout session with a subtotal calculated from the line items.
   *
   * @param checkout The {@link CheckoutResponse} object to initialize totals for.
   */
  protected void initTotals(CheckoutResponse checkout) {
    long subtotal = 0;
    if (checkout.getLineItems() != null) {
      subtotal =
          checkout.getLineItems().stream()
              .filter(li -> li.getTotals() != null)
              .flatMap(li -> li.getTotals().stream())
              .filter(t -> t.getType() == TotalResponse.TypeEnum.SUBTOTAL)
              .mapToLong(TotalResponse::getAmount)
              .sum();
    }
    List<TotalResponse> totals = new ArrayList<>();
    totals.add(
        new TotalResponse()
            .type(TotalResponse.TypeEnum.SUBTOTAL)
            .amount(Math.toIntExact(subtotal)));
    checkout.setTotals(totals);
  }

  /**
   * Recalculates the totals for the checkout session, including line item subtotals, grand total,
   * and applying discounts. This method relies on the {@link LineItemResponse} objects in the
   * checkout already having authoritative pricing and title information.
   *
   * @param checkout The {@link CheckoutResponse} object to recalculate totals for.
   * @param discountRequest The {@link DiscountRequest} containing any discount codes to apply.
   */
  protected void recalculateTotals(CheckoutResponse checkout, DiscountRequest discountRequest) {
    long currentGrandTotal = 0;
    for (LineItemResponse lineItem : checkout.getLineItems()) {
      if (lineItem.getTotals() != null) {
        for (TotalResponse total : lineItem.getTotals()) {
          if (total.getType() == TotalResponse.TypeEnum.SUBTOTAL) {
            currentGrandTotal += total.getAmount();
          }
        }
      }
    }

    checkout.setTotals(new ArrayList<>());
    checkout.addTotalsItem(
        new TotalResponse()
            .type(TotalResponse.TypeEnum.SUBTOTAL)
            .amount(Math.toIntExact(currentGrandTotal)));

    DiscountResponse discountResponse = new DiscountResponse();

    if (discountRequest != null && discountRequest.getCodes() != null) {
      for (String code : discountRequest.getCodes()) {
        Optional<DiscountEntity> discountEntityOpt = discountRepository.findById(code);
        if (discountEntityOpt.isPresent()) {
          DiscountEntity discountEntity = discountEntityOpt.get();
          long discountAmount = 0;
          if ("percentage".equals(discountEntity.getType())) {
            discountAmount = currentGrandTotal * discountEntity.getValue() / 100;
          } else if ("fixed_amount".equals(discountEntity.getType())) {
            discountAmount = discountEntity.getValue();
          }

          if (discountAmount > 0) {
            currentGrandTotal -= discountAmount;
            checkout.addTotalsItem(
                new TotalResponse()
                    .type(TotalResponse.TypeEnum.DISCOUNT)
                    .amount(Math.toIntExact(discountAmount)));
            if (discountResponse.getApplied() == null) {
              discountResponse.setApplied(new ArrayList<>());
            }
            discountResponse
                .getApplied()
                .add(
                    new DiscountRequestAppliedInner()
                        .code(code)
                        .title(discountEntity.getDescription())
                        .amount(Math.toIntExact(discountAmount)));
          }
        }
      }
    }

    long fulfillmentCost = fulfillmentManager.recalculateFulfillmentTotals(checkout);
    if (fulfillmentCost > 0) {
      checkout.addTotalsItem(
          new TotalResponse()
              .type(TotalResponse.TypeEnum.FULFILLMENT)
              .amount(Math.toIntExact(fulfillmentCost)));
      currentGrandTotal += fulfillmentCost;
    }

    checkout.addTotalsItem(
        new TotalResponse()
            .type(TotalResponse.TypeEnum.TOTAL)
            .amount(Math.toIntExact(currentGrandTotal)));
    extensionsHelper.setDiscount(checkout, discountResponse);
  }

  /**
   * Updates the checkout session's status based on the messages present in the checkout response.
   * The status is determined by the highest severity message:
   *
   * <p>- If any message has a severity of `REQUIRES_BUYER_INPUT` or `REQUIRES_BUYER_REVIEW`, the
   * status is set to `REQUIRES_ESCALATION`.
   *
   * <p>- Otherwise, if any message is an `ERROR` with `RECOVERABLE` severity, the status is set to
   * `INCOMPLETE`.
   *
   * <p>- If no error messages are present (only informational or warning messages, or no messages
   * at all), the status defaults to `READY_FOR_COMPLETE`.
   *
   * @param checkout The {@link CheckoutResponse} object whose status is to be updated.
   */
  protected void updateStatus(CheckoutResponse checkout) {
    // Default to ready, this will be the status if no errors are found.
    checkout.setStatus(CheckoutResponse.StatusEnum.READY_FOR_COMPLETE);

    if (checkout.getMessages() == null || checkout.getMessages().isEmpty()) {
      return;
    }

    for (Message message : checkout.getMessages()) {
      if (message instanceof MessageError error) {

        // Escalation errors take the highest precedence.
        if (requiresEscalation(error)) {
          checkout.setStatus(CheckoutResponse.StatusEnum.REQUIRES_ESCALATION);
          return; // Exit immediately, as this is the highest priority status.
        }

        // Any other error makes the checkout incomplete.
        checkout.setStatus(CheckoutResponse.StatusEnum.INCOMPLETE);
      }
    }
  }

  /**
   * Checks if a given {@link MessageError} indicates a requirement for buyer escalation. This is
   * true if the error's severity is either `REQUIRES_BUYER_INPUT` or `REQUIRES_BUYER_REVIEW`.
   *
   * @param error The {@link MessageError} to check.
   * @return `true` if the error requires buyer escalation, `false` otherwise.
   */
  private boolean requiresEscalation(MessageError error) {
    return error.getSeverity() == MessageError.SeverityEnum.REQUIRES_BUYER_INPUT
        || error.getSeverity() == MessageError.SeverityEnum.REQUIRES_BUYER_REVIEW;
  }


}
