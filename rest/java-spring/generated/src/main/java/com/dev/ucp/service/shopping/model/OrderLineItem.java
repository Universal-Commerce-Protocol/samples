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
import com.dev.ucp.service.shopping.model.ItemResponse;
import com.dev.ucp.service.shopping.model.OrderLineItemQuantity;
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
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
 * OrderLineItem
 */

@JsonTypeName("Order_Line_Item")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderLineItem {

  private String id;

  private ItemResponse item;

  private OrderLineItemQuantity quantity;

  @Valid
  private List<@Valid TotalResponse> totals = new ArrayList<>();

  /**
   * Derived status: fulfilled if quantity.fulfilled == quantity.total, partial if quantity.fulfilled > 0, otherwise processing.
   */
  public enum StatusEnum {
    PROCESSING("processing"),
    
    PARTIAL("partial"),
    
    FULFILLED("fulfilled");

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

  private @Nullable String parentId;

  public OrderLineItem() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public OrderLineItem(String id, ItemResponse item, OrderLineItemQuantity quantity, List<@Valid TotalResponse> totals, StatusEnum status) {
    this.id = id;
    this.item = item;
    this.quantity = quantity;
    this.totals = totals;
    this.status = status;
  }

  public OrderLineItem id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Line item identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Line item identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public OrderLineItem item(ItemResponse item) {
    this.item = item;
    return this;
  }

  /**
   * Get item
   * @return item
   */
  @NotNull @Valid 
  @Schema(name = "item", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("item")
  public ItemResponse getItem() {
    return item;
  }

  public void setItem(ItemResponse item) {
    this.item = item;
  }

  public OrderLineItem quantity(OrderLineItemQuantity quantity) {
    this.quantity = quantity;
    return this;
  }

  /**
   * Get quantity
   * @return quantity
   */
  @NotNull @Valid 
  @Schema(name = "quantity", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("quantity")
  public OrderLineItemQuantity getQuantity() {
    return quantity;
  }

  public void setQuantity(OrderLineItemQuantity quantity) {
    this.quantity = quantity;
  }

  public OrderLineItem totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public OrderLineItem addTotalsItem(TotalResponse totalsItem) {
    if (this.totals == null) {
      this.totals = new ArrayList<>();
    }
    this.totals.add(totalsItem);
    return this;
  }

  /**
   * Line item totals breakdown.
   * @return totals
   */
  @NotNull @Valid 
  @Schema(name = "totals", description = "Line item totals breakdown.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("totals")
  public List<@Valid TotalResponse> getTotals() {
    return totals;
  }

  public void setTotals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
  }

  public OrderLineItem status(StatusEnum status) {
    this.status = status;
    return this;
  }

  /**
   * Derived status: fulfilled if quantity.fulfilled == quantity.total, partial if quantity.fulfilled > 0, otherwise processing.
   * @return status
   */
  @NotNull 
  @Schema(name = "status", description = "Derived status: fulfilled if quantity.fulfilled == quantity.total, partial if quantity.fulfilled > 0, otherwise processing.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("status")
  public StatusEnum getStatus() {
    return status;
  }

  public void setStatus(StatusEnum status) {
    this.status = status;
  }

  public OrderLineItem parentId(@Nullable String parentId) {
    this.parentId = parentId;
    return this;
  }

  /**
   * Parent line item identifier for any nested structures.
   * @return parentId
   */
  
  @Schema(name = "parent_id", description = "Parent line item identifier for any nested structures.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("parent_id")
  public @Nullable String getParentId() {
    return parentId;
  }

  public void setParentId(@Nullable String parentId) {
    this.parentId = parentId;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OrderLineItem orderLineItem = (OrderLineItem) o;
    return Objects.equals(this.id, orderLineItem.id) &&
        Objects.equals(this.item, orderLineItem.item) &&
        Objects.equals(this.quantity, orderLineItem.quantity) &&
        Objects.equals(this.totals, orderLineItem.totals) &&
        Objects.equals(this.status, orderLineItem.status) &&
        Objects.equals(this.parentId, orderLineItem.parentId);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, item, quantity, totals, status, parentId);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderLineItem {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    item: ").append(toIndentedString(item)).append("\n");
    sb.append("    quantity: ").append(toIndentedString(quantity)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
    sb.append("    status: ").append(toIndentedString(status)).append("\n");
    sb.append("    parentId: ").append(toIndentedString(parentId)).append("\n");
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

    private OrderLineItem instance;

    public Builder() {
      this(new OrderLineItem());
    }

    protected Builder(OrderLineItem instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderLineItem value) { 
      this.instance.setId(value.id);
      this.instance.setItem(value.item);
      this.instance.setQuantity(value.quantity);
      this.instance.setTotals(value.totals);
      this.instance.setStatus(value.status);
      this.instance.setParentId(value.parentId);
      return this;
    }

    public OrderLineItem.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public OrderLineItem.Builder item(ItemResponse item) {
      this.instance.item(item);
      return this;
    }
    
    public OrderLineItem.Builder quantity(OrderLineItemQuantity quantity) {
      this.instance.quantity(quantity);
      return this;
    }
    
    public OrderLineItem.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    public OrderLineItem.Builder status(StatusEnum status) {
      this.instance.status(status);
      return this;
    }
    
    public OrderLineItem.Builder parentId(String parentId) {
      this.instance.parentId(parentId);
      return this;
    }
    
    /**
    * returns a built OrderLineItem instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderLineItem build() {
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
  public static OrderLineItem.Builder builder() {
    return new OrderLineItem.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderLineItem.Builder toBuilder() {
    OrderLineItem.Builder builder = new OrderLineItem.Builder();
    return builder.copyOf(this);
  }

}

