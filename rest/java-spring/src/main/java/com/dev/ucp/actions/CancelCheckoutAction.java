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

import com.dev.ucp.service.shopping.model.CheckoutResponse;
import java.util.UUID;
import org.springframework.stereotype.Service;

/** Service for canceling a checkout session. */
@Service
public class CancelCheckoutAction extends BaseCheckoutAction<String> {

  public CheckoutResponse cancelCheckout(String checkoutId, UUID idempotencyKey) {
    return execute(idempotencyKey, checkoutId);
  }

  @Override
  protected CheckoutResponse executeAction(String checkoutId) {
    CheckoutResponse checkout = loadCheckoutSession(checkoutId);
    ensureModifiable(checkout);
    checkout.setStatus(CheckoutResponse.StatusEnum.CANCELED);
    saveCheckoutSession(checkoutId, checkout.getStatus().toString(), checkout);
    return checkout;
  }

  @Override
  protected String getEndpoint() {
    return "/checkout-sessions/{id}/cancel";
  }
}
