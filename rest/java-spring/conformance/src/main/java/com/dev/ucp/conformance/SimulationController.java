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

package com.dev.ucp.conformance;

import com.dev.ucp.OrderWebHookNotifier;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

/**
 * Optional testing controller part of the UCP conformance extension.
 *
 * <p>This controller provides endpoints to simulate post-checkout lifecycle events that would
 * normally occur within internal merchant systems (like ERP or WMS). It is intended only for
 * protocol verification and automated conformance testing.
 *
 * <p>This controller is only active when the 'conformance' Maven profile is enabled.
 */
@RestController
public class SimulationController {

  private static final String SIMULATION_SECRET = "super-secret-sim-key";

  @Autowired private OrderWebHookNotifier webhookNotifier;

  /**
   * Manually triggers the 'order_shipped' webhook event for a given order.
   *
   * <p>The request must include a valid 'Simulation-Secret' header to be authorized.
   *
   * @param orderId the unique identifier of the order to simulate shipping for.
   * @param secret the secret key provided in the 'Simulation-Secret' request header.
   * @return a {@link ResponseEntity} with {@code 200 OK} if successful, or {@code 403 Forbidden} if
   *     the secret is invalid.
   */
  @PostMapping("/testing/simulate-shipping/{orderId}")
  public ResponseEntity<Void> simulateShipping(
      @PathVariable String orderId,
      @RequestHeader(value = "Simulation-Secret", required = false) String secret) {

    if (!SIMULATION_SECRET.equals(secret)) {
      return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
    }

    webhookNotifier.triggerShipping(orderId);
    return ResponseEntity.ok().build();
  }
}
