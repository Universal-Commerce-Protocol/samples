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
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * Quantity tracking. Both total and fulfilled are derived from events.
 */

@Schema(name = "Order_Line_Item_quantity", description = "Quantity tracking. Both total and fulfilled are derived from events.")
@JsonTypeName("Order_Line_Item_quantity")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderLineItemQuantity {

  private Integer total;

  private Integer fulfilled;

  public OrderLineItemQuantity() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public OrderLineItemQuantity(Integer total, Integer fulfilled) {
    this.total = total;
    this.fulfilled = fulfilled;
  }

  public OrderLineItemQuantity total(Integer total) {
    this.total = total;
    return this;
  }

  /**
   * Current total quantity.
   * minimum: 0
   * @return total
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "total", description = "Current total quantity.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("total")
  public Integer getTotal() {
    return total;
  }

  public void setTotal(Integer total) {
    this.total = total;
  }

  public OrderLineItemQuantity fulfilled(Integer fulfilled) {
    this.fulfilled = fulfilled;
    return this;
  }

  /**
   * Quantity fulfilled (sum from fulfillment events).
   * minimum: 0
   * @return fulfilled
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "fulfilled", description = "Quantity fulfilled (sum from fulfillment events).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("fulfilled")
  public Integer getFulfilled() {
    return fulfilled;
  }

  public void setFulfilled(Integer fulfilled) {
    this.fulfilled = fulfilled;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OrderLineItemQuantity orderLineItemQuantity = (OrderLineItemQuantity) o;
    return Objects.equals(this.total, orderLineItemQuantity.total) &&
        Objects.equals(this.fulfilled, orderLineItemQuantity.fulfilled);
  }

  @Override
  public int hashCode() {
    return Objects.hash(total, fulfilled);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderLineItemQuantity {\n");
    sb.append("    total: ").append(toIndentedString(total)).append("\n");
    sb.append("    fulfilled: ").append(toIndentedString(fulfilled)).append("\n");
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

    private OrderLineItemQuantity instance;

    public Builder() {
      this(new OrderLineItemQuantity());
    }

    protected Builder(OrderLineItemQuantity instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderLineItemQuantity value) { 
      this.instance.setTotal(value.total);
      this.instance.setFulfilled(value.fulfilled);
      return this;
    }

    public OrderLineItemQuantity.Builder total(Integer total) {
      this.instance.total(total);
      return this;
    }
    
    public OrderLineItemQuantity.Builder fulfilled(Integer fulfilled) {
      this.instance.fulfilled(fulfilled);
      return this;
    }
    
    /**
    * returns a built OrderLineItemQuantity instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderLineItemQuantity build() {
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
  public static OrderLineItemQuantity.Builder builder() {
    return new OrderLineItemQuantity.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderLineItemQuantity.Builder toBuilder() {
    OrderLineItemQuantity.Builder builder = new OrderLineItemQuantity.Builder();
    return builder.copyOf(this);
  }

}

