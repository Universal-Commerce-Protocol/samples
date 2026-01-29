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
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Service for retrieving an existing checkout session. */
@Service
@Transactional
public class GetCheckoutAction extends BaseCheckoutAction<String> {

  public CheckoutResponse getCheckout(String checkoutId) {
    return execute(null, checkoutId);
  }

  @Override
  protected CheckoutResponse executeAction(String request) {
    return loadCheckoutSession(request);
  }

  @Override
  protected String getEndpoint() {
    return "/checkout-sessions/{id}";
  }
}
