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
import java.net.URI;
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

/**
 * Order schema with immutable line items, buyer-facing fulfillment expectations, and append-only event logs.
 */

@Schema(name = "order", description = "Order schema with immutable line items, buyer-facing fulfillment expectations, and append-only event logs.")
@JsonTypeName("order")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class Order {

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

  public Order() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public Order(UCPOrderResponse ucp, String id, String checkoutId, URI permalinkUrl, List<@Valid OrderLineItem> lineItems, OrderFulfillment fulfillment, List<@Valid TotalResponse> totals) {
    this.ucp = ucp;
    this.id = id;
    this.checkoutId = checkoutId;
    this.permalinkUrl = permalinkUrl;
    this.lineItems = lineItems;
    this.fulfillment = fulfillment;
    this.totals = totals;
  }

  public Order ucp(UCPOrderResponse ucp) {
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

  public Order id(String id) {
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

  public Order checkoutId(String checkoutId) {
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

  public Order permalinkUrl(URI permalinkUrl) {
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

  public Order lineItems(List<@Valid OrderLineItem> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public Order addLineItemsItem(OrderLineItem lineItemsItem) {
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

  public Order fulfillment(OrderFulfillment fulfillment) {
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

  public Order adjustments(List<@Valid Adjustment> adjustments) {
    this.adjustments = adjustments;
    return this;
  }

  public Order addAdjustmentsItem(Adjustment adjustmentsItem) {
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

  public Order totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public Order addTotalsItem(TotalResponse totalsItem) {
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

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    Order order = (Order) o;
    return Objects.equals(this.ucp, order.ucp) &&
        Objects.equals(this.id, order.id) &&
        Objects.equals(this.checkoutId, order.checkoutId) &&
        Objects.equals(this.permalinkUrl, order.permalinkUrl) &&
        Objects.equals(this.lineItems, order.lineItems) &&
        Objects.equals(this.fulfillment, order.fulfillment) &&
        Objects.equals(this.adjustments, order.adjustments) &&
        Objects.equals(this.totals, order.totals);
  }

  @Override
  public int hashCode() {
    return Objects.hash(ucp, id, checkoutId, permalinkUrl, lineItems, fulfillment, adjustments, totals);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Order {\n");
    sb.append("    ucp: ").append(toIndentedString(ucp)).append("\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    checkoutId: ").append(toIndentedString(checkoutId)).append("\n");
    sb.append("    permalinkUrl: ").append(toIndentedString(permalinkUrl)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    fulfillment: ").append(toIndentedString(fulfillment)).append("\n");
    sb.append("    adjustments: ").append(toIndentedString(adjustments)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
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

    private Order instance;

    public Builder() {
      this(new Order());
    }

    protected Builder(Order instance) {
      this.instance = instance;
    }

    protected Builder copyOf(Order value) { 
      this.instance.setUcp(value.ucp);
      this.instance.setId(value.id);
      this.instance.setCheckoutId(value.checkoutId);
      this.instance.setPermalinkUrl(value.permalinkUrl);
      this.instance.setLineItems(value.lineItems);
      this.instance.setFulfillment(value.fulfillment);
      this.instance.setAdjustments(value.adjustments);
      this.instance.setTotals(value.totals);
      return this;
    }

    public Order.Builder ucp(UCPOrderResponse ucp) {
      this.instance.ucp(ucp);
      return this;
    }
    
    public Order.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public Order.Builder checkoutId(String checkoutId) {
      this.instance.checkoutId(checkoutId);
      return this;
    }
    
    public Order.Builder permalinkUrl(URI permalinkUrl) {
      this.instance.permalinkUrl(permalinkUrl);
      return this;
    }
    
    public Order.Builder lineItems(List<OrderLineItem> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public Order.Builder fulfillment(OrderFulfillment fulfillment) {
      this.instance.fulfillment(fulfillment);
      return this;
    }
    
    public Order.Builder adjustments(List<Adjustment> adjustments) {
      this.instance.adjustments(adjustments);
      return this;
    }
    
    public Order.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    /**
    * returns a built Order instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public Order build() {
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
  public static Order.Builder builder() {
    return new Order.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public Order.Builder toBuilder() {
    Order.Builder builder = new Order.Builder();
    return builder.copyOf(this);
  }

}

