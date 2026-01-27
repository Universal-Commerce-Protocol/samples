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

import com.dev.ucp.entities.CheckoutSessionEntity;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
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
public class CancelCheckoutActionTest {

  @Autowired private CancelCheckoutAction cancelCheckoutAction;

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
  public void testCancelCheckout_happyPath() {
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result = cancelCheckoutAction.cancelCheckout(checkoutId, idempotencyKey);

    assertNotNull(result);
    assertEquals(checkoutId, result.getId());
    assertEquals(CheckoutResponse.StatusEnum.CANCELED, result.getStatus());
  }

  @Test
  public void testCancelCheckout_idempotency() {
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result1 = cancelCheckoutAction.cancelCheckout(checkoutId, idempotencyKey);
    CheckoutResponse result2 = cancelCheckoutAction.cancelCheckout(checkoutId, idempotencyKey);

    assertEquals(result1, result2);
  }
}
