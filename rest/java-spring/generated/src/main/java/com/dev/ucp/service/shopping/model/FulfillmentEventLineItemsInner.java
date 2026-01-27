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
 * FulfillmentEventLineItemsInner
 */

@JsonTypeName("Fulfillment_Event_line_items_inner")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentEventLineItemsInner {

  private String id;

  private Integer quantity;

  public FulfillmentEventLineItemsInner() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentEventLineItemsInner(String id, Integer quantity) {
    this.id = id;
    this.quantity = quantity;
  }

  public FulfillmentEventLineItemsInner id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Line item ID reference.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Line item ID reference.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public FulfillmentEventLineItemsInner quantity(Integer quantity) {
    this.quantity = quantity;
    return this;
  }

  /**
   * Quantity fulfilled in this event.
   * minimum: 1
   * @return quantity
   */
  @NotNull @Min(value = 1) 
  @Schema(name = "quantity", description = "Quantity fulfilled in this event.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("quantity")
  public Integer getQuantity() {
    return quantity;
  }

  public void setQuantity(Integer quantity) {
    this.quantity = quantity;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FulfillmentEventLineItemsInner fulfillmentEventLineItemsInner = (FulfillmentEventLineItemsInner) o;
    return Objects.equals(this.id, fulfillmentEventLineItemsInner.id) &&
        Objects.equals(this.quantity, fulfillmentEventLineItemsInner.quantity);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, quantity);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentEventLineItemsInner {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    quantity: ").append(toIndentedString(quantity)).append("\n");
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

    private FulfillmentEventLineItemsInner instance;

    public Builder() {
      this(new FulfillmentEventLineItemsInner());
    }

    protected Builder(FulfillmentEventLineItemsInner instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentEventLineItemsInner value) { 
      this.instance.setId(value.id);
      this.instance.setQuantity(value.quantity);
      return this;
    }

    public FulfillmentEventLineItemsInner.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public FulfillmentEventLineItemsInner.Builder quantity(Integer quantity) {
      this.instance.quantity(quantity);
      return this;
    }
    
    /**
    * returns a built FulfillmentEventLineItemsInner instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentEventLineItemsInner build() {
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
  public static FulfillmentEventLineItemsInner.Builder builder() {
    return new FulfillmentEventLineItemsInner.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentEventLineItemsInner.Builder toBuilder() {
    FulfillmentEventLineItemsInner.Builder builder = new FulfillmentEventLineItemsInner.Builder();
    return builder.copyOf(this);
  }

}

