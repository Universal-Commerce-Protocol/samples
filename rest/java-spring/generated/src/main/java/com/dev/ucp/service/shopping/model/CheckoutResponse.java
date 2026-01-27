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
import com.dev.ucp.service.shopping.model.LineItemResponse;
import com.dev.ucp.service.shopping.model.Link;
import com.dev.ucp.service.shopping.model.Message;
import com.dev.ucp.service.shopping.model.OrderConfirmation;
import com.dev.ucp.service.shopping.model.PaymentResponse;
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.dev.ucp.service.shopping.model.UCPCheckoutResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.net.URI;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
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

@Schema(name = "checkout_response", description = "Base checkout schema. Extensions compose onto this using allOf.")
@JsonTypeName("checkout_response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CheckoutResponse {

  private UCPCheckoutResponse ucp;

  private String id;

  @Valid
  private List<@Valid LineItemResponse> lineItems = new ArrayList<>();

  private @Nullable Buyer buyer;

  /**
   * Checkout state indicating the current phase and required action. See Checkout Status lifecycle documentation for state transition details.
   */
  public enum StatusEnum {
    INCOMPLETE("incomplete"),
    
    REQUIRES_ESCALATION("requires_escalation"),
    
    READY_FOR_COMPLETE("ready_for_complete"),
    
    COMPLETE_IN_PROGRESS("complete_in_progress"),
    
    COMPLETED("completed"),
    
    CANCELED("canceled");

    private final String value;

    StatusEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static StatusEnum fromValue(String value) {
      for (StatusEnum b : StatusEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private StatusEnum status;

  private String currency;

  @Valid
  private List<@Valid TotalResponse> totals = new ArrayList<>();

  @Valid
  private List<@Valid Message> messages = new ArrayList<>();

  @Valid
  private List<@Valid Link> links = new ArrayList<>();

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private @Nullable OffsetDateTime expiresAt;

  private @Nullable URI continueUrl;

  private PaymentResponse payment;

  private @Nullable OrderConfirmation order;

  public CheckoutResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public CheckoutResponse(UCPCheckoutResponse ucp, String id, List<@Valid LineItemResponse> lineItems, StatusEnum status, String currency, List<@Valid TotalResponse> totals, List<@Valid Link> links, PaymentResponse payment) {
    this.ucp = ucp;
    this.id = id;
    this.lineItems = lineItems;
    this.status = status;
    this.currency = currency;
    this.totals = totals;
    this.links = links;
    this.payment = payment;
  }

  public CheckoutResponse ucp(UCPCheckoutResponse ucp) {
    this.ucp = ucp;
    return this;
  }

  /**
   * Get ucp
   * @return ucp
   */
  @NotNull @Valid 
  @Schema(name = "ucp", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("ucp")
  public UCPCheckoutResponse getUcp() {
    return ucp;
  }

  public void setUcp(UCPCheckoutResponse ucp) {
    this.ucp = ucp;
  }

  public CheckoutResponse id(String id) {
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

  public CheckoutResponse lineItems(List<@Valid LineItemResponse> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public CheckoutResponse addLineItemsItem(LineItemResponse lineItemsItem) {
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
  public List<@Valid LineItemResponse> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid LineItemResponse> lineItems) {
    this.lineItems = lineItems;
  }

  public CheckoutResponse buyer(@Nullable Buyer buyer) {
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

  public CheckoutResponse status(StatusEnum status) {
    this.status = status;
    return this;
  }

  /**
   * Checkout state indicating the current phase and required action. See Checkout Status lifecycle documentation for state transition details.
   * @return status
   */
  @NotNull 
  @Schema(name = "status", description = "Checkout state indicating the current phase and required action. See Checkout Status lifecycle documentation for state transition details.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("status")
  public StatusEnum getStatus() {
    return status;
  }

  public void setStatus(StatusEnum status) {
    this.status = status;
  }

  public CheckoutResponse currency(String currency) {
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

  public CheckoutResponse totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public CheckoutResponse addTotalsItem(TotalResponse totalsItem) {
    if (this.totals == null) {
      this.totals = new ArrayList<>();
    }
    this.totals.add(totalsItem);
    return this;
  }

  /**
   * Different cart totals.
   * @return totals
   */
  @NotNull @Valid 
  @Schema(name = "totals", description = "Different cart totals.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("totals")
  public List<@Valid TotalResponse> getTotals() {
    return totals;
  }

  public void setTotals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
  }

  public CheckoutResponse messages(List<@Valid Message> messages) {
    this.messages = messages;
    return this;
  }

  public CheckoutResponse addMessagesItem(Message messagesItem) {
    if (this.messages == null) {
      this.messages = new ArrayList<>();
    }
    this.messages.add(messagesItem);
    return this;
  }

  /**
   * List of messages with error and info about the checkout session state.
   * @return messages
   */
  @Valid 
  @Schema(name = "messages", description = "List of messages with error and info about the checkout session state.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("messages")
  public List<@Valid Message> getMessages() {
    return messages;
  }

  public void setMessages(List<@Valid Message> messages) {
    this.messages = messages;
  }

  public CheckoutResponse links(List<@Valid Link> links) {
    this.links = links;
    return this;
  }

  public CheckoutResponse addLinksItem(Link linksItem) {
    if (this.links == null) {
      this.links = new ArrayList<>();
    }
    this.links.add(linksItem);
    return this;
  }

  /**
   * Links to be displayed by the platform (Privacy Policy, TOS). Mandatory for legal compliance.
   * @return links
   */
  @NotNull @Valid 
  @Schema(name = "links", description = "Links to be displayed by the platform (Privacy Policy, TOS). Mandatory for legal compliance.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("links")
  public List<@Valid Link> getLinks() {
    return links;
  }

  public void setLinks(List<@Valid Link> links) {
    this.links = links;
  }

  public CheckoutResponse expiresAt(@Nullable OffsetDateTime expiresAt) {
    this.expiresAt = expiresAt;
    return this;
  }

  /**
   * RFC 3339 expiry timestamp. Default TTL is 6 hours from creation if not sent.
   * @return expiresAt
   */
  @Valid 
  @Schema(name = "expires_at", description = "RFC 3339 expiry timestamp. Default TTL is 6 hours from creation if not sent.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("expires_at")
  public @Nullable OffsetDateTime getExpiresAt() {
    return expiresAt;
  }

  public void setExpiresAt(@Nullable OffsetDateTime expiresAt) {
    this.expiresAt = expiresAt;
  }

  public CheckoutResponse continueUrl(@Nullable URI continueUrl) {
    this.continueUrl = continueUrl;
    return this;
  }

  /**
   * URL for checkout handoff and session recovery. MUST be provided when status is requires_escalation. See specification for format and availability requirements.
   * @return continueUrl
   */
  @Valid 
  @Schema(name = "continue_url", description = "URL for checkout handoff and session recovery. MUST be provided when status is requires_escalation. See specification for format and availability requirements.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("continue_url")
  public @Nullable URI getContinueUrl() {
    return continueUrl;
  }

  public void setContinueUrl(@Nullable URI continueUrl) {
    this.continueUrl = continueUrl;
  }

  public CheckoutResponse payment(PaymentResponse payment) {
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
  public PaymentResponse getPayment() {
    return payment;
  }

  public void setPayment(PaymentResponse payment) {
    this.payment = payment;
  }

  public CheckoutResponse order(@Nullable OrderConfirmation order) {
    this.order = order;
    return this;
  }

  /**
   * Get order
   * @return order
   */
  @Valid 
  @Schema(name = "order", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("order")
  public @Nullable OrderConfirmation getOrder() {
    return order;
  }

  public void setOrder(@Nullable OrderConfirmation order) {
    this.order = order;
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
    public CheckoutResponse putAdditionalProperty(String key, JsonNode value) {
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
    CheckoutResponse checkoutResponse = (CheckoutResponse) o;
    return Objects.equals(this.ucp, checkoutResponse.ucp) &&
        Objects.equals(this.id, checkoutResponse.id) &&
        Objects.equals(this.lineItems, checkoutResponse.lineItems) &&
        Objects.equals(this.buyer, checkoutResponse.buyer) &&
        Objects.equals(this.status, checkoutResponse.status) &&
        Objects.equals(this.currency, checkoutResponse.currency) &&
        Objects.equals(this.totals, checkoutResponse.totals) &&
        Objects.equals(this.messages, checkoutResponse.messages) &&
        Objects.equals(this.links, checkoutResponse.links) &&
        Objects.equals(this.expiresAt, checkoutResponse.expiresAt) &&
        Objects.equals(this.continueUrl, checkoutResponse.continueUrl) &&
        Objects.equals(this.payment, checkoutResponse.payment) &&
        Objects.equals(this.order, checkoutResponse.order) &&
    Objects.equals(this.additionalProperties, checkoutResponse.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(ucp, id, lineItems, buyer, status, currency, totals, messages, links, expiresAt, continueUrl, payment, order, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CheckoutResponse {\n");
    sb.append("    ucp: ").append(toIndentedString(ucp)).append("\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    buyer: ").append(toIndentedString(buyer)).append("\n");
    sb.append("    status: ").append(toIndentedString(status)).append("\n");
    sb.append("    currency: ").append(toIndentedString(currency)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
    sb.append("    messages: ").append(toIndentedString(messages)).append("\n");
    sb.append("    links: ").append(toIndentedString(links)).append("\n");
    sb.append("    expiresAt: ").append(toIndentedString(expiresAt)).append("\n");
    sb.append("    continueUrl: ").append(toIndentedString(continueUrl)).append("\n");
    sb.append("    payment: ").append(toIndentedString(payment)).append("\n");
    sb.append("    order: ").append(toIndentedString(order)).append("\n");
    
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

    private CheckoutResponse instance;

    public Builder() {
      this(new CheckoutResponse());
    }

    protected Builder(CheckoutResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CheckoutResponse value) { 
      this.instance.setUcp(value.ucp);
      this.instance.setId(value.id);
      this.instance.setLineItems(value.lineItems);
      this.instance.setBuyer(value.buyer);
      this.instance.setStatus(value.status);
      this.instance.setCurrency(value.currency);
      this.instance.setTotals(value.totals);
      this.instance.setMessages(value.messages);
      this.instance.setLinks(value.links);
      this.instance.setExpiresAt(value.expiresAt);
      this.instance.setContinueUrl(value.continueUrl);
      this.instance.setPayment(value.payment);
      this.instance.setOrder(value.order);
      return this;
    }

    public CheckoutResponse.Builder ucp(UCPCheckoutResponse ucp) {
      this.instance.ucp(ucp);
      return this;
    }
    
    public CheckoutResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public CheckoutResponse.Builder lineItems(List<LineItemResponse> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public CheckoutResponse.Builder buyer(Buyer buyer) {
      this.instance.buyer(buyer);
      return this;
    }
    
    public CheckoutResponse.Builder status(StatusEnum status) {
      this.instance.status(status);
      return this;
    }
    
    public CheckoutResponse.Builder currency(String currency) {
      this.instance.currency(currency);
      return this;
    }
    
    public CheckoutResponse.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    public CheckoutResponse.Builder messages(List<Message> messages) {
      this.instance.messages(messages);
      return this;
    }
    
    public CheckoutResponse.Builder links(List<Link> links) {
      this.instance.links(links);
      return this;
    }
    
    public CheckoutResponse.Builder expiresAt(OffsetDateTime expiresAt) {
      this.instance.expiresAt(expiresAt);
      return this;
    }
    
    public CheckoutResponse.Builder continueUrl(URI continueUrl) {
      this.instance.continueUrl(continueUrl);
      return this;
    }
    
    public CheckoutResponse.Builder payment(PaymentResponse payment) {
      this.instance.payment(payment);
      return this;
    }
    
    public CheckoutResponse.Builder order(OrderConfirmation order) {
      this.instance.order(order);
      return this;
    }
    
    public CheckoutResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built CheckoutResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CheckoutResponse build() {
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
  public static CheckoutResponse.Builder builder() {
    return new CheckoutResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CheckoutResponse.Builder toBuilder() {
    CheckoutResponse.Builder builder = new CheckoutResponse.Builder();
    return builder.copyOf(this);
  }

}

