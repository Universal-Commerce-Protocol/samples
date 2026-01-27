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
import com.dev.ucp.service.shopping.model.Adjustment;
import com.dev.ucp.service.shopping.model.OrderFulfillment;
import com.dev.ucp.service.shopping.model.OrderLineItem;
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.dev.ucp.service.shopping.model.UCPOrderResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
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
 * OrderEventWebhookRequest
 */

@JsonTypeName("order_event_webhook_request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderEventWebhookRequest {

  private UCPOrderResponse ucp;

  private String id;

  private String checkoutId;

  private URI permalinkUrl;

  @Valid
  private List<@Valid OrderLineItem> lineItems = new ArrayList<>();

  private OrderFulfillment fulfillment;

  @Valid
  private List<@Valid Adjustment> adjustments = new ArrayList<>();

  @Valid
  private List<@Valid TotalResponse> totals = new ArrayList<>();

  private String eventId;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private OffsetDateTime createdTime;

  public OrderEventWebhookRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public OrderEventWebhookRequest(UCPOrderResponse ucp, String id, String checkoutId, URI permalinkUrl, List<@Valid OrderLineItem> lineItems, OrderFulfillment fulfillment, List<@Valid TotalResponse> totals, String eventId, OffsetDateTime createdTime) {
    this.ucp = ucp;
    this.id = id;
    this.checkoutId = checkoutId;
    this.permalinkUrl = permalinkUrl;
    this.lineItems = lineItems;
    this.fulfillment = fulfillment;
    this.totals = totals;
    this.eventId = eventId;
    this.createdTime = createdTime;
  }

  public OrderEventWebhookRequest ucp(UCPOrderResponse ucp) {
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
  public UCPOrderResponse getUcp() {
    return ucp;
  }

  public void setUcp(UCPOrderResponse ucp) {
    this.ucp = ucp;
  }

  public OrderEventWebhookRequest id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Unique order identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Unique order identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public OrderEventWebhookRequest checkoutId(String checkoutId) {
    this.checkoutId = checkoutId;
    return this;
  }

  /**
   * Associated checkout ID for reconciliation.
   * @return checkoutId
   */
  @NotNull 
  @Schema(name = "checkout_id", description = "Associated checkout ID for reconciliation.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("checkout_id")
  public String getCheckoutId() {
    return checkoutId;
  }

  public void setCheckoutId(String checkoutId) {
    this.checkoutId = checkoutId;
  }

  public OrderEventWebhookRequest permalinkUrl(URI permalinkUrl) {
    this.permalinkUrl = permalinkUrl;
    return this;
  }

  /**
   * Permalink to access the order on merchant site.
   * @return permalinkUrl
   */
  @NotNull @Valid 
  @Schema(name = "permalink_url", description = "Permalink to access the order on merchant site.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("permalink_url")
  public URI getPermalinkUrl() {
    return permalinkUrl;
  }

  public void setPermalinkUrl(URI permalinkUrl) {
    this.permalinkUrl = permalinkUrl;
  }

  public OrderEventWebhookRequest lineItems(List<@Valid OrderLineItem> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public OrderEventWebhookRequest addLineItemsItem(OrderLineItem lineItemsItem) {
    if (this.lineItems == null) {
      this.lineItems = new ArrayList<>();
    }
    this.lineItems.add(lineItemsItem);
    return this;
  }

  /**
   * Immutable line items — source of truth for what was ordered.
   * @return lineItems
   */
  @NotNull @Valid 
  @Schema(name = "line_items", description = "Immutable line items — source of truth for what was ordered.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_items")
  public List<@Valid OrderLineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public OrderEventWebhookRequest fulfillment(OrderFulfillment fulfillment) {
    this.fulfillment = fulfillment;
    return this;
  }

  /**
   * Get fulfillment
   * @return fulfillment
   */
  @NotNull @Valid 
  @Schema(name = "fulfillment", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("fulfillment")
  public OrderFulfillment getFulfillment() {
    return fulfillment;
  }

  public void setFulfillment(OrderFulfillment fulfillment) {
    this.fulfillment = fulfillment;
  }

  public OrderEventWebhookRequest adjustments(List<@Valid Adjustment> adjustments) {
    this.adjustments = adjustments;
    return this;
  }

  public OrderEventWebhookRequest addAdjustmentsItem(Adjustment adjustmentsItem) {
    if (this.adjustments == null) {
      this.adjustments = new ArrayList<>();
    }
    this.adjustments.add(adjustmentsItem);
    return this;
  }

  /**
   * Append-only event log of money movements (refunds, returns, credits, disputes, cancellations, etc.) that exist independently of fulfillment.
   * @return adjustments
   */
  @Valid 
  @Schema(name = "adjustments", description = "Append-only event log of money movements (refunds, returns, credits, disputes, cancellations, etc.) that exist independently of fulfillment.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("adjustments")
  public List<@Valid Adjustment> getAdjustments() {
    return adjustments;
  }

  public void setAdjustments(List<@Valid Adjustment> adjustments) {
    this.adjustments = adjustments;
  }

  public OrderEventWebhookRequest totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public OrderEventWebhookRequest addTotalsItem(TotalResponse totalsItem) {
    if (this.totals == null) {
      this.totals = new ArrayList<>();
    }
    this.totals.add(totalsItem);
    return this;
  }

  /**
   * Different totals for the order.
   * @return totals
   */
  @NotNull @Valid 
  @Schema(name = "totals", description = "Different totals for the order.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("totals")
  public List<@Valid TotalResponse> getTotals() {
    return totals;
  }

  public void setTotals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
  }

  public OrderEventWebhookRequest eventId(String eventId) {
    this.eventId = eventId;
    return this;
  }

  /**
   * Unique event identifier.
   * @return eventId
   */
  @NotNull 
  @Schema(name = "event_id", description = "Unique event identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("event_id")
  public String getEventId() {
    return eventId;
  }

  public void setEventId(String eventId) {
    this.eventId = eventId;
  }

  public OrderEventWebhookRequest createdTime(OffsetDateTime createdTime) {
    this.createdTime = createdTime;
    return this;
  }

  /**
   * Event creation timestamp in RFC 3339 format.
   * @return createdTime
   */
  @NotNull @Valid 
  @Schema(name = "created_time", description = "Event creation timestamp in RFC 3339 format.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("created_time")
  public OffsetDateTime getCreatedTime() {
    return createdTime;
  }

  public void setCreatedTime(OffsetDateTime createdTime) {
    this.createdTime = createdTime;
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
    public OrderEventWebhookRequest putAdditionalProperty(String key, JsonNode value) {
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
    OrderEventWebhookRequest orderEventWebhookRequest = (OrderEventWebhookRequest) o;
    return Objects.equals(this.ucp, orderEventWebhookRequest.ucp) &&
        Objects.equals(this.id, orderEventWebhookRequest.id) &&
        Objects.equals(this.checkoutId, orderEventWebhookRequest.checkoutId) &&
        Objects.equals(this.permalinkUrl, orderEventWebhookRequest.permalinkUrl) &&
        Objects.equals(this.lineItems, orderEventWebhookRequest.lineItems) &&
        Objects.equals(this.fulfillment, orderEventWebhookRequest.fulfillment) &&
        Objects.equals(this.adjustments, orderEventWebhookRequest.adjustments) &&
        Objects.equals(this.totals, orderEventWebhookRequest.totals) &&
        Objects.equals(this.eventId, orderEventWebhookRequest.eventId) &&
        Objects.equals(this.createdTime, orderEventWebhookRequest.createdTime) &&
    Objects.equals(this.additionalProperties, orderEventWebhookRequest.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(ucp, id, checkoutId, permalinkUrl, lineItems, fulfillment, adjustments, totals, eventId, createdTime, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderEventWebhookRequest {\n");
    sb.append("    ucp: ").append(toIndentedString(ucp)).append("\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    checkoutId: ").append(toIndentedString(checkoutId)).append("\n");
    sb.append("    permalinkUrl: ").append(toIndentedString(permalinkUrl)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    fulfillment: ").append(toIndentedString(fulfillment)).append("\n");
    sb.append("    adjustments: ").append(toIndentedString(adjustments)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
    sb.append("    eventId: ").append(toIndentedString(eventId)).append("\n");
    sb.append("    createdTime: ").append(toIndentedString(createdTime)).append("\n");
    
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

    private OrderEventWebhookRequest instance;

    public Builder() {
      this(new OrderEventWebhookRequest());
    }

    protected Builder(OrderEventWebhookRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderEventWebhookRequest value) { 
      this.instance.setUcp(value.ucp);
      this.instance.setId(value.id);
      this.instance.setCheckoutId(value.checkoutId);
      this.instance.setPermalinkUrl(value.permalinkUrl);
      this.instance.setLineItems(value.lineItems);
      this.instance.setFulfillment(value.fulfillment);
      this.instance.setAdjustments(value.adjustments);
      this.instance.setTotals(value.totals);
      this.instance.setEventId(value.eventId);
      this.instance.setCreatedTime(value.createdTime);
      return this;
    }

    public OrderEventWebhookRequest.Builder ucp(UCPOrderResponse ucp) {
      this.instance.ucp(ucp);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder checkoutId(String checkoutId) {
      this.instance.checkoutId(checkoutId);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder permalinkUrl(URI permalinkUrl) {
      this.instance.permalinkUrl(permalinkUrl);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder lineItems(List<OrderLineItem> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder fulfillment(OrderFulfillment fulfillment) {
      this.instance.fulfillment(fulfillment);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder adjustments(List<Adjustment> adjustments) {
      this.instance.adjustments(adjustments);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder eventId(String eventId) {
      this.instance.eventId(eventId);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder createdTime(OffsetDateTime createdTime) {
      this.instance.createdTime(createdTime);
      return this;
    }
    
    public OrderEventWebhookRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built OrderEventWebhookRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderEventWebhookRequest build() {
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
  public static OrderEventWebhookRequest.Builder builder() {
    return new OrderEventWebhookRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderEventWebhookRequest.Builder toBuilder() {
    OrderEventWebhookRequest.Builder builder = new OrderEventWebhookRequest.Builder();
    return builder.copyOf(this);
  }

}

