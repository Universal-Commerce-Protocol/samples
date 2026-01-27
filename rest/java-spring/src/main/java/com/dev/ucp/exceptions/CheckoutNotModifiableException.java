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

package com.dev.ucp.exceptions;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * Exception thrown when an attempt is made to modify a checkout session that is in a terminal state
 * (e.g., COMPLETED or CANCELED).
 *
 * <p>This exception results in an HTTP 409 Conflict response.
 *
 * <p>Reference: <a href="https://ucp.dev/specification/checkout-rest/#status-codes">UCP Checkout
 * REST - Status Codes</a>
 */
@ResponseStatus(value = HttpStatus.CONFLICT)
public class CheckoutNotModifiableException extends RuntimeException {
  public CheckoutNotModifiableException(String message) {
    super(message);
  }
}
