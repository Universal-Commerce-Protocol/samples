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

import com.dev.ucp.ExtensionsHelper;
import com.dev.ucp.entities.CheckoutSessionEntity;
import com.dev.ucp.service.shopping.model.CardPaymentInstrument;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CompleteCheckoutRequest;
import com.dev.ucp.service.shopping.model.FulfillmentGroupResponse;
import com.dev.ucp.service.shopping.model.FulfillmentMethodResponse;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.dev.ucp.service.shopping.model.TokenCredentialResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.TextNode;
import java.util.Collections;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.openapitools.jackson.nullable.JsonNullable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@Transactional
public class CompleteCheckoutActionTest {

  @Autowired private CompleteCheckoutAction completeCheckoutAction;

  @Autowired private CheckoutSessionEntity.Repository checkoutSessionRepository;

  @Autowired private ExtensionsHelper extensionsHelper;

  private final ObjectMapper objectMapper = new ObjectMapper();

  private String checkoutId;

  @BeforeEach
  public void setup() throws JsonProcessingException {
    checkoutId = UUID.randomUUID().toString();
    CheckoutResponse checkout = new CheckoutResponse();
    checkout.setId(checkoutId);
    checkout.setStatus(CheckoutResponse.StatusEnum.READY_FOR_COMPLETE);

    FulfillmentGroupResponse group = new FulfillmentGroupResponse();
    group.setSelectedOptionId(JsonNullable.of("shipping-standard"));

    FulfillmentMethodResponse method = new FulfillmentMethodResponse();
    method.setType(FulfillmentMethodResponse.TypeEnum.SHIPPING);
    method.setSelectedDestinationId(JsonNullable.of("dest-1"));
    method.setGroups(Collections.singletonList(group));

    FulfillmentResponse fulfillment = new FulfillmentResponse();
    fulfillment.setMethods(Collections.singletonList(method));
    extensionsHelper.setFulfillment(checkout, fulfillment);

    CheckoutSessionEntity entity = new CheckoutSessionEntity();
    entity.setId(checkoutId);
    entity.setStatus(checkout.getStatus().toString());
    entity.setData(objectMapper.writeValueAsString(checkout));
    checkoutSessionRepository.save(entity);
  }

  @Test
  public void testCompleteCheckout_happyPath() {
    UUID idempotencyKey = UUID.randomUUID();
    CompleteCheckoutRequest request = new CompleteCheckoutRequest();
    request.setPaymentData(createValidPaymentInstrument());

    CheckoutResponse result =
        completeCheckoutAction.completeCheckout(checkoutId, idempotencyKey, request, null);

    assertNotNull(result);
    assertNotNull(result.getOrder().getId());
    assertNotNull(result.getOrder().getPermalinkUrl());
  }

  @Test
  public void testCompleteCheckout_idempotency() {
    UUID idempotencyKey = UUID.randomUUID();
    CompleteCheckoutRequest request = new CompleteCheckoutRequest();
    request.setPaymentData(createValidPaymentInstrument());

    CheckoutResponse result1 =
        completeCheckoutAction.completeCheckout(checkoutId, idempotencyKey, request, null);
    CheckoutResponse result2 =
        completeCheckoutAction.completeCheckout(checkoutId, idempotencyKey, request, null);

    assertEquals(result1, result2);
  }

  private CardPaymentInstrument createValidPaymentInstrument() {
    CardPaymentInstrument instrument = new CardPaymentInstrument();
    instrument.setId("instr-1");
    instrument.setHandlerId("mock_payment_handler");
    instrument.setType(CardPaymentInstrument.TypeEnum.CARD);
    instrument.setBrand("Visa");
    instrument.setLastDigits("1111");

    TokenCredentialResponse credential = new TokenCredentialResponse();
    credential.setType("mock_token");
    credential.putAdditionalProperty("token", new TextNode("success_token"));
    instrument.setCredential(credential);

    return instrument;
  }
}
