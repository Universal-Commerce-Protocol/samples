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
package com.dev.ucp.service.shopping.model;

import java.net.URI;
import java.util.Objects;
import com.dev.ucp.service.shopping.model.Buyer;
import com.dev.ucp.service.shopping.model.LineItemUpdateRequest;
import com.dev.ucp.service.shopping.model.PaymentUpdateRequest;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

import java.util.Map;
import java.util.HashMap;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
/**
 * Base checkout schema. Extensions compose onto this using allOf.
 */

@Schema(name = "checkout_update_request", description = "Base checkout schema. Extensions compose onto this using allOf.")
@JsonTypeName("checkout_update_request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CheckoutUpdateRequest {

  private String id;

  @Valid
  private List<@Valid LineItemUpdateRequest> lineItems = new ArrayList<>();

  private @Nullable Buyer buyer;

  private String currency;

  private PaymentUpdateRequest payment;

  public CheckoutUpdateRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public CheckoutUpdateRequest(String id, List<@Valid LineItemUpdateRequest> lineItems, String currency, PaymentUpdateRequest payment) {
    this.id = id;
    this.lineItems = lineItems;
    this.currency = currency;
    this.payment = payment;
  }

  public CheckoutUpdateRequest id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Unique identifier of the checkout session.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Unique identifier of the checkout session.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public CheckoutUpdateRequest lineItems(List<@Valid LineItemUpdateRequest> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public CheckoutUpdateRequest addLineItemsItem(LineItemUpdateRequest lineItemsItem) {
    if (this.lineItems == null) {
      this.lineItems = new ArrayList<>();
    }
    this.lineItems.add(lineItemsItem);
    return this;
  }

  /**
   * List of line items being checked out.
   * @return lineItems
   */
  @NotNull @Valid 
  @Schema(name = "line_items", description = "List of line items being checked out.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_items")
  public List<@Valid LineItemUpdateRequest> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid LineItemUpdateRequest> lineItems) {
    this.lineItems = lineItems;
  }

  public CheckoutUpdateRequest buyer(@Nullable Buyer buyer) {
    this.buyer = buyer;
    return this;
  }

  /**
   * Get buyer
   * @return buyer
   */
  @Valid 
  @Schema(name = "buyer", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("buyer")
  public @Nullable Buyer getBuyer() {
    return buyer;
  }

  public void setBuyer(@Nullable Buyer buyer) {
    this.buyer = buyer;
  }

  public CheckoutUpdateRequest currency(String currency) {
    this.currency = currency;
    return this;
  }

  /**
   * ISO 4217 currency code.
   * @return currency
   */
  @NotNull 
  @Schema(name = "currency", description = "ISO 4217 currency code.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("currency")
  public String getCurrency() {
    return currency;
  }

  public void setCurrency(String currency) {
    this.currency = currency;
  }

  public CheckoutUpdateRequest payment(PaymentUpdateRequest payment) {
    this.payment = payment;
    return this;
  }

  /**
   * Get payment
   * @return payment
   */
  @NotNull @Valid 
  @Schema(name = "payment", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("payment")
  public PaymentUpdateRequest getPayment() {
    return payment;
  }

  public void setPayment(PaymentUpdateRequest payment) {
    this.payment = payment;
  }
    /**
    * A container for additional, undeclared properties.
    * This is a holder for any undeclared properties as specified with
    * the 'additionalProperties' keyword in the OAS document.
    */
    private Map<String, JsonNode> additionalProperties;

    /**
    * Set the additional (undeclared) property with the specified name and value.
    * If the property does not already exist, create it otherwise replace it.
    */
    @JsonAnySetter
    public CheckoutUpdateRequest putAdditionalProperty(String key, JsonNode value) {
        if (this.additionalProperties == null) {
            this.additionalProperties = new HashMap<String, JsonNode>();
        }
        this.additionalProperties.put(key, value);
        return this;
    }

    /**
    * Return the additional (undeclared) property.
    */
    @JsonAnyGetter
    public Map<String, JsonNode> getAdditionalProperties() {
        return additionalProperties;
    }

    /**
    * Return the additional (undeclared) property with the specified name.
    */
    public JsonNode getAdditionalProperty(String key) {
        if (this.additionalProperties == null) {
            return null;
        }
        return this.additionalProperties.get(key);
    }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    CheckoutUpdateRequest checkoutUpdateRequest = (CheckoutUpdateRequest) o;
    return Objects.equals(this.id, checkoutUpdateRequest.id) &&
        Objects.equals(this.lineItems, checkoutUpdateRequest.lineItems) &&
        Objects.equals(this.buyer, checkoutUpdateRequest.buyer) &&
        Objects.equals(this.currency, checkoutUpdateRequest.currency) &&
        Objects.equals(this.payment, checkoutUpdateRequest.payment) &&
    Objects.equals(this.additionalProperties, checkoutUpdateRequest.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, lineItems, buyer, currency, payment, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CheckoutUpdateRequest {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    buyer: ").append(toIndentedString(buyer)).append("\n");
    sb.append("    currency: ").append(toIndentedString(currency)).append("\n");
    sb.append("    payment: ").append(toIndentedString(payment)).append("\n");
    
    sb.append("    additionalProperties: ").append(toIndentedString(additionalProperties)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }
  
  public static class Builder {

    private CheckoutUpdateRequest instance;

    public Builder() {
      this(new CheckoutUpdateRequest());
    }

    protected Builder(CheckoutUpdateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CheckoutUpdateRequest value) { 
      this.instance.setId(value.id);
      this.instance.setLineItems(value.lineItems);
      this.instance.setBuyer(value.buyer);
      this.instance.setCurrency(value.currency);
      this.instance.setPayment(value.payment);
      return this;
    }

    public CheckoutUpdateRequest.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public CheckoutUpdateRequest.Builder lineItems(List<LineItemUpdateRequest> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public CheckoutUpdateRequest.Builder buyer(Buyer buyer) {
      this.instance.buyer(buyer);
      return this;
    }
    
    public CheckoutUpdateRequest.Builder currency(String currency) {
      this.instance.currency(currency);
      return this;
    }
    
    public CheckoutUpdateRequest.Builder payment(PaymentUpdateRequest payment) {
      this.instance.payment(payment);
      return this;
    }
    
    public CheckoutUpdateRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built CheckoutUpdateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CheckoutUpdateRequest build() {
      try {
        return this.instance;
      } finally {
        // ensure that this.instance is not reused
        this.instance = null;
      }
    }

    @Override
    public String toString() {
      return getClass() + "=(" + instance + ")";
    }
  }

  /**
  * Create a builder with no initialized field (except for the default values).
  */
  public static CheckoutUpdateRequest.Builder builder() {
    return new CheckoutUpdateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CheckoutUpdateRequest.Builder toBuilder() {
    CheckoutUpdateRequest.Builder builder = new CheckoutUpdateRequest.Builder();
    return builder.copyOf(this);
  }

}

