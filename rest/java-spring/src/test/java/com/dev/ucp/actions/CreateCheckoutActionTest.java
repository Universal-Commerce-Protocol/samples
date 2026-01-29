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
import com.dev.ucp.entities.IdempotencyRecordEntity;
import com.dev.ucp.exceptions.IdempotencyConflictException;
import com.dev.ucp.service.shopping.model.Buyer;
import com.dev.ucp.service.shopping.model.CheckoutCreateRequest;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.ItemCreateRequest;
import com.dev.ucp.service.shopping.model.LineItemCreateRequest;
import com.dev.ucp.service.shopping.model.PaymentCreateRequest;
import java.util.Collections;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@Transactional
@Sql(scripts = "/data.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/cleanup.sql", executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
public class CreateCheckoutActionTest {

  @Autowired private CreateCheckoutAction createCheckoutAction;

  @Autowired private IdempotencyRecordEntity.Repository idempotencyRecordRepository;

  @Autowired private CheckoutSessionEntity.Repository checkoutSessionRepository;

  @Test
  public void testCreateCheckoutSession_happyPath() {

    CheckoutCreateRequest checkout = new CheckoutCreateRequest();

    Buyer buyer = new Buyer();

    buyer.setEmail("john.doe@example.com");

    checkout.setBuyer(buyer);

    checkout.setCurrency("USD");

    LineItemCreateRequest lineItem = new LineItemCreateRequest();
    ItemCreateRequest item = new ItemCreateRequest();
    item.setId("bouquet_roses");
    lineItem.setItem(item);
    lineItem.setQuantity(1);
    checkout.setLineItems(Collections.singletonList(lineItem));
    checkout.setPayment(new PaymentCreateRequest());

    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result = createCheckoutAction.createCheckoutSession(idempotencyKey, checkout);

    assertNotNull(result);
    assertEquals(CheckoutResponse.StatusEnum.READY_FOR_COMPLETE, result.getStatus());
    assertNotNull(result.getId());
    assertEquals(1, result.getLineItems().size());

    assertEquals(1, idempotencyRecordRepository.count());
    assertEquals(1, checkoutSessionRepository.count());
  }

  @Test
  public void testCreateCheckoutSession_idempotency() {

    CheckoutCreateRequest checkout = new CheckoutCreateRequest();

    Buyer buyer = new Buyer();

    buyer.setEmail("john.doe@example.com");

    checkout.setBuyer(buyer);

    checkout.setCurrency("USD");

    LineItemCreateRequest lineItem = new LineItemCreateRequest();
    ItemCreateRequest item = new ItemCreateRequest();
    item.setId("bouquet_roses");
    lineItem.setItem(item);
    lineItem.setQuantity(1);
    checkout.setLineItems(Collections.singletonList(lineItem));
    checkout.setPayment(new PaymentCreateRequest());
    UUID idempotencyKey = UUID.randomUUID();

    CheckoutResponse result1 = createCheckoutAction.createCheckoutSession(idempotencyKey, checkout);
    CheckoutResponse result2 = createCheckoutAction.createCheckoutSession(idempotencyKey, checkout);

    assertEquals(result1.getId(), result2.getId());
    assertEquals(result1.getLineItems().size(), result2.getLineItems().size());
    assertEquals(1, idempotencyRecordRepository.count());
    assertEquals(1, checkoutSessionRepository.count());
  }

  @Test
  public void testCreateCheckoutSession_idempotencyKeyReusedWithDifferentPayload() {
    UUID idempotencyKey = UUID.randomUUID();
    CheckoutCreateRequest checkout1 = new CheckoutCreateRequest();
    Buyer buyer1 = new Buyer();
    buyer1.setEmail("test1@example.com");
    checkout1.setBuyer(buyer1);
    checkout1.setCurrency("USD");
    LineItemCreateRequest lineItem1 = new LineItemCreateRequest();
    ItemCreateRequest item1 = new ItemCreateRequest();
    item1.setId("bouquet_roses");
    lineItem1.setItem(item1);
    lineItem1.setQuantity(1);
    checkout1.setLineItems(Collections.singletonList(lineItem1));
    checkout1.setPayment(new PaymentCreateRequest());

    createCheckoutAction.createCheckoutSession(idempotencyKey, checkout1);

    CheckoutCreateRequest checkout2 = new CheckoutCreateRequest();
    Buyer buyer2 = new Buyer();
    buyer2.setEmail("test2@example.com");
    checkout2.setBuyer(buyer2);
    checkout2.setCurrency("USD");
    LineItemCreateRequest lineItem2 = new LineItemCreateRequest();
    ItemCreateRequest item2 = new ItemCreateRequest();
    item2.setId("bouquet_roses");
    lineItem2.setItem(item2);
    lineItem2.setQuantity(1);
    checkout2.setLineItems(Collections.singletonList(lineItem2));
    checkout2.setPayment(new PaymentCreateRequest());

    assertThrows(
        IdempotencyConflictException.class,
        () -> {
          createCheckoutAction.createCheckoutSession(idempotencyKey, checkout2);
        });
  }
}