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
import com.dev.ucp.exceptions.ResourceNotFoundException;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@Transactional
public class GetCheckoutActionTest {

  @Autowired private GetCheckoutAction getCheckoutAction;

  @Autowired private CheckoutSessionEntity.Repository checkoutSessionRepository;

  private final ObjectMapper objectMapper = new ObjectMapper();

  @Test
  public void testGetCheckout_found() throws JsonProcessingException {
    String checkoutId = UUID.randomUUID().toString();
    CheckoutResponse checkout = new CheckoutResponse();
    checkout.setId(checkoutId);

    CheckoutSessionEntity entity = new CheckoutSessionEntity();
    entity.setId(checkoutId);
    entity.setData(objectMapper.writeValueAsString(checkout));
    checkoutSessionRepository.save(entity);

    CheckoutResponse result = getCheckoutAction.getCheckout(checkoutId);

    assertNotNull(result);
    assertEquals(checkoutId, result.getId());
  }

  @Test
  public void testGetCheckout_notFound() {
    assertThrows(
        ResourceNotFoundException.class,
        () -> {
          getCheckoutAction.getCheckout(UUID.randomUUID().toString());
        });
  }
}
