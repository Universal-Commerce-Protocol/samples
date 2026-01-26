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
import com.dev.ucp.LineItemConverter;
import com.dev.ucp.service.shopping.model.CardPaymentInstrument;
import com.dev.ucp.service.shopping.model.CheckoutCreateRequest;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.PaymentCreateRequest;
import com.dev.ucp.service.shopping.model.PaymentResponse;
import com.dev.ucp.service.shopping.model.UCPCheckoutResponse;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Service for creating a new checkout session. */
@Service
@Transactional
public class CreateCheckoutAction extends BaseCheckoutAction<CheckoutCreateRequest> {

  @Autowired private ExtensionsHelper extensionsHelper;
  @Autowired private InventoryManager inventoryManager;
  @Autowired private LineItemConverter lineItemConverter;

  public CheckoutResponse createCheckoutSession(
      UUID idempotencyKey, CheckoutCreateRequest request) {
    return execute(idempotencyKey, request);
  }

  @Override
  protected CheckoutResponse executeAction(CheckoutCreateRequest request) {
    CheckoutResponse checkout = new CheckoutResponse();
    checkout.setUcp(createUcpCheckoutResponse());
    checkout.setId(UUID.randomUUID().toString()); // A unique ID for the checkout session itself

    checkout.setBuyer(request.getBuyer());
    checkout.setCurrency(request.getCurrency());
    checkout.setPayment(convertPayment(checkout, request.getPayment()));
    checkout.setLineItems(lineItemConverter.convertFromCreateRequest(request.getLineItems()));
    initTotals(checkout);
    inventoryManager.validate(checkout);

    fulfillmentManager.handleFulfillment(checkout, extensionsHelper.getFulfillmentRequest(request));
    recalculateTotals(checkout, extensionsHelper.getDiscount(request));
    updateStatus(checkout);

    saveCheckoutSession(checkout.getId(), checkout.getStatus().toString(), checkout);

    return checkout;
  }

  private PaymentResponse convertPayment(
      CheckoutResponse checkout, PaymentCreateRequest paymentRequest) {
    List<CardPaymentInstrument> instruments = new ArrayList<>();
    String selectedInstrumentId = null;
    if (paymentRequest != null) {
      selectedInstrumentId = paymentRequest.getSelectedInstrumentId();
      if (paymentRequest.getInstruments() != null) {
        instruments.addAll(paymentRequest.getInstruments());
      }
    }

    return super.convertPayment(checkout, instruments, selectedInstrumentId);
  }

  private UCPCheckoutResponse createUcpCheckoutResponse() {
    try (InputStream inputStream =
        new ClassPathResource("discovery_profile.json").getInputStream()) {
      JsonNode discoveryProfile = objectMapper.readTree(inputStream);
      JsonNode ucpNode = discoveryProfile.get("ucp");
      if (ucpNode != null) {
        return objectMapper.treeToValue(ucpNode, UCPCheckoutResponse.class);
      }
      return new UCPCheckoutResponse();
    } catch (IOException e) {
      throw new RuntimeException("Error reading discovery_profile.json", e);
    }
  }

  @Override
  protected String getEndpoint() {
    return "/checkout-sessions/create";
  }
}