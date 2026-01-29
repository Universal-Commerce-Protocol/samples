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
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.Module;
import com.fasterxml.jackson.databind.module.SimpleModule;
import java.io.IOException;
import org.openapitools.jackson.nullable.JsonNullableModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configures Jackson Object Mapper behaviors for the UCP Spring Demo.
 *
 * <p>This configuration handles specialized JSON processing requirements such as:
 *
 * <ul>
 *   <li><b>Null Handling:</b> Integration with {@code JsonNullable}.
 *   <li><b>Polymorphism:</b> Custom deserialization for complex UCP types like {@code
 *       PaymentCredential}, {@code Message}, {@code FulfillmentDestinationResponse}, and {@code
 *       FulfillmentDestinationRequest} where standard Jackson type inference might be insufficient
 *       or requires custom logic.
 * </ul>
 */
@Configuration
public class JacksonConfig {

  /**
   * Supports the {@code JsonNullable} wrapper used by OpenAPI-generated models.
   *
   * <p>This module allows Jackson to distinguish between a field being absent (undefined),
   * explicitly set to null, or containing a value.
   *
   * @return a configured {@link JsonNullableModule}.
   */
  @Bean
  public Module jsonNullableModule() {
    return new JsonNullableModule();
  }

  /**
   * Provides a unified module for all custom polymorphic deserializers required by the UCP
   * specification.
   *
   * <p>Standard Jackson polymorphic handling (using discriminators) is often overridden by the
   * generated models or is insufficient for certain UCP union types. This module registers manual
   * discrimination logic for:
   *
   * <ul>
   *   <li>{@link PaymentCredential}: Discriminates based on {@code card_number_type}.
   *   <li>{@link Message}: Discriminates based on the {@code type} field.
   *   <li>{@link FulfillmentDestinationResponse} / {@link FulfillmentDestinationRequest}:
   *       Discriminates between Shipping (flat) and Retail (composed) based on the presence of
   *       {@code name}.
   * </ul>
   *
   * @return a {@link SimpleModule} containing all UCP polymorphic deserializers.
   */
  @Bean
  public Module ucpPolymorphicModule() {
    SimpleModule module = new SimpleModule();

    // 1. PaymentCredential Deserializer
    module.addDeserializer(
        PaymentCredential.class,
        new JsonDeserializer<PaymentCredential>() {
          @Override
          public PaymentCredential deserialize(JsonParser p, DeserializationContext ctxt)
              throws IOException {
            JsonNode node = p.readValueAsTree();
            if (node.has("card_number_type")) {
              try {
                return p.getCodec().treeToValue(node, CardCredential.class);
              } catch (Exception ignored) {
                // Fallback to token
              }
            }
            return p.getCodec().treeToValue(node, TokenCredentialResponse.class);
          }
        });

    // 2. Message Deserializer
    module.addDeserializer(
        Message.class,
        new JsonDeserializer<Message>() {
          @Override
          public Message deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
            JsonNode node = p.readValueAsTree();
            JsonNode typeNode = node.get("type");
            if (typeNode == null) {
              return null;
            }
            String type = typeNode.asText();
            return switch (type) {
              case "error" -> p.getCodec().treeToValue(node, MessageError.class);
              case "warning" -> p.getCodec().treeToValue(node, MessageWarning.class);
              case "info" -> p.getCodec().treeToValue(node, MessageInfo.class);
              default -> throw new IOException("Unknown message type: " + type);
            };
          }
        });

    // 3. FulfillmentDestinationResponse Deserializer
    module.addDeserializer(
        FulfillmentDestinationResponse.class,
        new JsonDeserializer<FulfillmentDestinationResponse>() {
          @Override
          public FulfillmentDestinationResponse deserialize(
              JsonParser p, DeserializationContext ctxt) throws IOException {
            JsonNode node = p.readValueAsTree();
            if (node.has("name")) {
              return p.getCodec().treeToValue(node, RetailLocationResponse.class);
            }
            return p.getCodec().treeToValue(node, ShippingDestinationResponse.class);
          }
        });

    // 4. FulfillmentDestinationRequest Deserializer
    module.addDeserializer(
        FulfillmentDestinationRequest.class,
        new JsonDeserializer<FulfillmentDestinationRequest>() {
          @Override
          public FulfillmentDestinationRequest deserialize(
              JsonParser p, DeserializationContext ctxt) throws IOException {
            JsonNode node = p.readValueAsTree();
            if (node.has("name")) {
              return p.getCodec().treeToValue(node, RetailLocationRequest.class);
            }
            return p.getCodec().treeToValue(node, ShippingDestinationRequest.class);
          }
        });

    return module;
  }
}
