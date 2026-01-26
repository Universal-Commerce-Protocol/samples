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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.dev.ucp.entities.CheckoutSessionEntity;
import com.dev.ucp.exceptions.IdempotencyConflictException;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CheckoutUpdateRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@Transactional
public class UpdateCheckoutActionTest {

  @Autowired private UpdateCheckoutAction updateCheckoutAction;

  @Autowired private CheckoutSessionEntity.Repository checkoutSessionRepository;

  private final ObjectMapper objectMapper = new ObjectMapper();

  private String checkoutId;

  @BeforeEach
  public void setup() throws JsonProcessingException {
    checkoutId = UUID.randomUUID().toString();
    CheckoutResponse checkout = new CheckoutResponse();
    checkout.setId(checkoutId);
    checkout.setStatus(CheckoutResponse.StatusEnum.READY_FOR_COMPLETE);

    CheckoutSessionEntity entity = new CheckoutSessionEntity();
    entity.setId(checkoutId);
    entity.setStatus(checkout.getStatus().toString());
    entity.setData(objectMapper.writeValueAsString(checkout));
    checkoutSessionRepository.save(entity);
  }

  @Test
  public void testUpdateCheckout_happyPath() {
    CheckoutUpdateRequest updatedCheckout = new CheckoutUpdateRequest();
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result =
        updateCheckoutAction.updateCheckout(checkoutId, idempotencyKey, updatedCheckout);

    assertNotNull(result);
    assertEquals(checkoutId, result.getId());
  }

  @Test
  public void testUpdateCheckout_idempotency() {
    CheckoutUpdateRequest updatedCheckout = new CheckoutUpdateRequest();
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result1 =
        updateCheckoutAction.updateCheckout(checkoutId, idempotencyKey, updatedCheckout);
    CheckoutResponse result2 =
        updateCheckoutAction.updateCheckout(checkoutId, idempotencyKey, updatedCheckout);

    assertEquals(result1, result2);
  }

  @Test
  public void testUpdateCheckout_idempotencyKeyReusedWithDifferentPayload() {
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutUpdateRequest checkout1 = new CheckoutUpdateRequest();
    updateCheckoutAction.updateCheckout(checkoutId, idempotencyKey, checkout1);

    CheckoutUpdateRequest checkout2 = new CheckoutUpdateRequest();
    checkout2.setCurrency("USD");

    assertThrows(
        IdempotencyConflictException.class,
        () -> {
          updateCheckoutAction.updateCheckout(checkoutId, idempotencyKey, checkout2);
        });
  }
}
