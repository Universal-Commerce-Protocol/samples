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
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CheckoutUpdateRequest;
import com.dev.ucp.service.shopping.model.PaymentResponse;
import com.dev.ucp.service.shopping.model.PaymentUpdateRequest;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/** Service for updating an existing checkout session. */
@Service
public class UpdateCheckoutAction extends BaseCheckoutAction<CheckoutUpdateRequest> {

  @Autowired private ExtensionsHelper extensionsHelper;
  @Autowired private InventoryManager inventoryManager;
  @Autowired private LineItemConverter lineItemConverter;

  public CheckoutResponse updateCheckout(
      String checkoutId, UUID idempotencyKey, CheckoutUpdateRequest checkout) {
    checkout.setId(checkoutId); // Ensure ID consistency
    return execute(idempotencyKey, checkout);
  }

  @Override
  protected CheckoutResponse executeAction(CheckoutUpdateRequest request) {
    CheckoutResponse checkout = loadCheckoutSession(request.getId());

    ensureModifiable(checkout);

    checkout.setMessages(new ArrayList<>());
    checkout.setBuyer(request.getBuyer());
    checkout.setCurrency(request.getCurrency());
    checkout.setPayment(convertPayment(checkout, request.getPayment()));
    checkout.setLineItems(lineItemConverter.convertFromUpdateRequest(request.getLineItems()));
    initTotals(checkout);
    inventoryManager.validate(checkout);

    fulfillmentManager.handleFulfillment(checkout, extensionsHelper.getFulfillmentRequest(request));
    recalculateTotals(checkout, extensionsHelper.getDiscount(request));
    updateStatus(checkout);

    saveCheckoutSession(checkout.getId(), checkout.getStatus().toString(), checkout);

    return checkout;
  }

  private PaymentResponse convertPayment(
      CheckoutResponse checkout, PaymentUpdateRequest paymentRequest) {
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

  @Override
  protected String getEndpoint() {
    return "/checkout-sessions/{id}";
  }
}