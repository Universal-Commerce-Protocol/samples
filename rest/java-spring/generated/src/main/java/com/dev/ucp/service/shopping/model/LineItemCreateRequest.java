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
import com.dev.ucp.service.shopping.model.ItemCreateRequest;
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
 * Line item object. Expected to use the currency of the parent object.
 */

@Schema(name = "Line_Item_Create_Request", description = "Line item object. Expected to use the currency of the parent object.")
@JsonTypeName("Line_Item_Create_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class LineItemCreateRequest {

  private ItemCreateRequest item;

  private Integer quantity;

  public LineItemCreateRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public LineItemCreateRequest(ItemCreateRequest item, Integer quantity) {
    this.item = item;
    this.quantity = quantity;
  }

  public LineItemCreateRequest item(ItemCreateRequest item) {
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
  public ItemCreateRequest getItem() {
    return item;
  }

  public void setItem(ItemCreateRequest item) {
    this.item = item;
  }

  public LineItemCreateRequest quantity(Integer quantity) {
    this.quantity = quantity;
    return this;
  }

  /**
   * Quantity of the item being purchased.
   * minimum: 1
   * @return quantity
   */
  @NotNull @Min(value = 1) 
  @Schema(name = "quantity", description = "Quantity of the item being purchased.", requiredMode = Schema.RequiredMode.REQUIRED)
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
    LineItemCreateRequest lineItemCreateRequest = (LineItemCreateRequest) o;
    return Objects.equals(this.item, lineItemCreateRequest.item) &&
        Objects.equals(this.quantity, lineItemCreateRequest.quantity);
  }

  @Override
  public int hashCode() {
    return Objects.hash(item, quantity);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class LineItemCreateRequest {\n");
    sb.append("    item: ").append(toIndentedString(item)).append("\n");
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

    private LineItemCreateRequest instance;

    public Builder() {
      this(new LineItemCreateRequest());
    }

    protected Builder(LineItemCreateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(LineItemCreateRequest value) { 
      this.instance.setItem(value.item);
      this.instance.setQuantity(value.quantity);
      return this;
    }

    public LineItemCreateRequest.Builder item(ItemCreateRequest item) {
      this.instance.item(item);
      return this;
    }
    
    public LineItemCreateRequest.Builder quantity(Integer quantity) {
      this.instance.quantity(quantity);
      return this;
    }
    
    /**
    * returns a built LineItemCreateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public LineItemCreateRequest build() {
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
  public static LineItemCreateRequest.Builder builder() {
    return new LineItemCreateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public LineItemCreateRequest.Builder toBuilder() {
    LineItemCreateRequest.Builder builder = new LineItemCreateRequest.Builder();
    return builder.copyOf(this);
  }

}

