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

package com.dev.ucp;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.dev.ucp.service.shopping.model.CardCredential;
import com.dev.ucp.service.shopping.model.FulfillmentDestinationRequest;
import com.dev.ucp.service.shopping.model.FulfillmentDestinationResponse;
import com.dev.ucp.service.shopping.model.Message;
import com.dev.ucp.service.shopping.model.MessageError;
import com.dev.ucp.service.shopping.model.MessageInfo;
import com.dev.ucp.service.shopping.model.MessageWarning;
import com.dev.ucp.service.shopping.model.PaymentCredential;
import com.dev.ucp.service.shopping.model.RetailLocationRequest;
import com.dev.ucp.service.shopping.model.RetailLocationResponse;
import com.dev.ucp.service.shopping.model.ShippingDestinationRequest;
import com.dev.ucp.service.shopping.model.ShippingDestinationResponse;
import com.dev.ucp.service.shopping.model.TokenCredentialResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.openapitools.jackson.nullable.JsonNullable;

public class JacksonConfigTest {

  private ObjectMapper objectMapper;

  @BeforeEach
  public void setUp() {
    JacksonConfig config = new JacksonConfig();
    objectMapper = new ObjectMapper();
    objectMapper.registerModule(config.jsonNullableModule());
    objectMapper.registerModule(config.ucpPolymorphicModule());
  }

  /** Helper class for testing JsonNullable fields. */
  private static class NullableWrapper {
    public JsonNullable<String> value = JsonNullable.undefined();
  }

  @Test
  public void testJsonNullable() throws Exception {
    String json = "{\"value\": null}";
    NullableWrapper wrapper = objectMapper.readValue(json, NullableWrapper.class);
    assertTrue(wrapper.value.isPresent());
    assertNull(wrapper.value.get());

    json = "{}";
    wrapper = objectMapper.readValue(json, NullableWrapper.class);
    assertFalse(wrapper.value.isPresent());
  }

  @Test
  public void testPaymentCredentialPolymorphism() throws Exception {
    // 1. CardCredential (identified by card_number_type)
    String cardJson = "{\"card_number_type\": \"fpan\", \"number\": \"1234\"}";
    PaymentCredential card = objectMapper.readValue(cardJson, PaymentCredential.class);
    assertInstanceOf(CardCredential.class, card);

    // 2. TokenCredentialResponse (fallback)
    String tokenJson = "{\"token\": \"some-token\", \"type\": \"mock\"}";
    PaymentCredential token = objectMapper.readValue(tokenJson, PaymentCredential.class);
    assertInstanceOf(TokenCredentialResponse.class, token);
  }

  @Test
  public void testMessagePolymorphism() throws Exception {
    // 1. Error
    String errorJson = "{\"type\": \"error\", \"code\": \"err_code\"}";
    Message error = objectMapper.readValue(errorJson, Message.class);
    assertInstanceOf(MessageError.class, error);
    assertEquals("err_code", ((MessageError) error).getCode());

    // 2. Warning
    String warningJson = "{\"type\": \"warning\", \"content\": \"warn\"}";
    Message warning = objectMapper.readValue(warningJson, Message.class);
    assertInstanceOf(MessageWarning.class, warning);

    // 3. Info
    String infoJson = "{\"type\": \"info\", \"content\": \"info\"}";
    Message info = objectMapper.readValue(infoJson, Message.class);
    assertInstanceOf(MessageInfo.class, info);
  }

  @Test
  public void testFulfillmentDestinationResponsePolymorphism() throws Exception {
    // 1. RetailLocationResponse (has 'name')
    String retailJson = "{\"id\": \"loc-1\", \"name\": \"Store 1\"}";
    FulfillmentDestinationResponse retail =
        objectMapper.readValue(retailJson, FulfillmentDestinationResponse.class);
    assertInstanceOf(RetailLocationResponse.class, retail);
    assertEquals("Store 1", ((RetailLocationResponse) retail).getName());

    // 2. ShippingDestinationResponse (no 'name')
    String shippingJson = "{\"id\": \"dest-1\", \"address_country\": \"US\"}";
    FulfillmentDestinationResponse shipping =
        objectMapper.readValue(shippingJson, FulfillmentDestinationResponse.class);
    assertInstanceOf(ShippingDestinationResponse.class, shipping);
    assertEquals("dest-1", ((ShippingDestinationResponse) shipping).getId());
  }

  @Test
  public void testFulfillmentDestinationRequestPolymorphism() throws Exception {
    // 1. RetailLocationRequest (has 'name')
    String retailJson = "{\"name\": \"Store 1\"}";
    FulfillmentDestinationRequest retail =
        objectMapper.readValue(retailJson, FulfillmentDestinationRequest.class);
    assertInstanceOf(RetailLocationRequest.class, retail);

    // 2. ShippingDestinationRequest (no 'name')
    String shippingJson = "{\"address_country\": \"CA\"}";
    FulfillmentDestinationRequest shipping =
        objectMapper.readValue(shippingJson, FulfillmentDestinationRequest.class);
    assertInstanceOf(ShippingDestinationRequest.class, shipping);
  }
}
