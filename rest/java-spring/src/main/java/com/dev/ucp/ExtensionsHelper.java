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

import com.dev.ucp.exceptions.ExtensionValidationException;
import com.dev.ucp.service.shopping.model.CheckoutCreateRequest;
import com.dev.ucp.service.shopping.model.CheckoutResponse;
import com.dev.ucp.service.shopping.model.CheckoutUpdateRequest;
import com.dev.ucp.service.shopping.model.DiscountRequest;
import com.dev.ucp.service.shopping.model.DiscountResponse;
import com.dev.ucp.service.shopping.model.FulfillmentResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import java.util.Set;
import java.util.function.BiConsumer;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Utility class for managing UCP extension fields in request and response objects.
 *
 * <p>This class provides methods for accessing and modifying the fulfillment and discounts
 * extensions within the checkout request and response objects. It allows for business logic to be
 * decoupled from json serialization details.
 */
@Component
public class ExtensionsHelper {

  private static final String FULFILLMENT_PROPERTY = "fulfillment";
  private static final String DISCOUNTS_PROPERTY = "discounts";

  private static final Predicate<ConstraintViolation<?>> IGNORE_ID_FILTER =
      v -> !v.getPropertyPath().toString().endsWith(".id") && !v.getPropertyPath().toString().equals("id");

  @Autowired private ObjectMapper objectMapper;
  @Autowired private Validator validator;

  public ExtensionsHelper() {}

  public FulfillmentResponse getFulfillmentRequest(CheckoutCreateRequest request) {
    // Parse request as response since this part of schema is unstable and there are proposed fixes in flight.
    // Create request is missing id fields, reponse has all fields needed.
    // TODO: Make proper conversion later.
    return getAdditionalProperty(
        request::getAdditionalProperty,
        FULFILLMENT_PROPERTY,
        FulfillmentResponse.class,
        IGNORE_ID_FILTER);
  }

  public FulfillmentResponse getFulfillmentRequest(CheckoutUpdateRequest request) {
    // Parse request as response since this part of schema is unstable and there are proposed fixes in flight.
    // Create request is missing id fields, reponse has all fields needed.
    // TODO: Make proper conversion later.
    return getAdditionalProperty(
        request::getAdditionalProperty,
        FULFILLMENT_PROPERTY,
        FulfillmentResponse.class,
        IGNORE_ID_FILTER);
  }

  public FulfillmentResponse getFulfillmentResponse(CheckoutResponse checkout) {
    return getAdditionalProperty(
        checkout::getAdditionalProperty,
        FULFILLMENT_PROPERTY,
        FulfillmentResponse.class,
        IGNORE_ID_FILTER);
  }

  public DiscountRequest getDiscount(CheckoutCreateRequest request) {
    return getAdditionalProperty(
        request::getAdditionalProperty, DISCOUNTS_PROPERTY, DiscountRequest.class, v -> true);
  }

  public DiscountRequest getDiscount(CheckoutUpdateRequest request) {
    return getAdditionalProperty(
        request::getAdditionalProperty, DISCOUNTS_PROPERTY, DiscountRequest.class, v -> true);
  }

  public void setFulfillment(CheckoutResponse checkout, FulfillmentResponse fulfillmentResponse) {
    setAdditionalProperty(checkout::putAdditionalProperty, FULFILLMENT_PROPERTY, fulfillmentResponse);
  }

  public void setDiscount(CheckoutResponse checkout, DiscountResponse discount) {
    setAdditionalProperty(checkout::putAdditionalProperty, DISCOUNTS_PROPERTY, discount);
  }

  private <T> T getAdditionalProperty(
      Function<String, JsonNode> getter,
      String propertyName,
      Class<T> valueType,
      Predicate<ConstraintViolation<?>> violationFilter) {
    try {
      JsonNode node = getter.apply(propertyName);
      if (node == null) {
        return null;
      }
      T value = objectMapper.treeToValue(node, valueType);

      Set<ConstraintViolation<T>> violations =
          validator.validate(value).stream()
              .filter(violationFilter)
              .collect(Collectors.toSet());

      if (!violations.isEmpty()) {
        throw new ExtensionValidationException((Set<ConstraintViolation<?>>) (Set<?>) violations);
      }

      return value;
    } catch (JsonProcessingException e) {
      throw new RuntimeException("Error processing " + propertyName + " extension", e);
    }
  }

  private <T> void setAdditionalProperty(BiConsumer<String, JsonNode> setter, String propertyName, T value) {
    try {
      JsonNode node = objectMapper.valueToTree(value);
      setter.accept(propertyName, node);
    } catch (IllegalArgumentException e) {
      throw new RuntimeException("Error setting " + propertyName + " extension", e);
    }
  }
}