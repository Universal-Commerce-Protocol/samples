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
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
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
 * Line item object. Expected to use the currency of the parent object.
 */

@Schema(name = "Line_Item_Response", description = "Line item object. Expected to use the currency of the parent object.")
@JsonTypeName("Line_Item_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class LineItemResponse {

  private String id;

  private ItemResponse item;

  private Integer quantity;

  @Valid
  private List<@Valid TotalResponse> totals = new ArrayList<>();

  private @Nullable String parentId;

  public LineItemResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public LineItemResponse(String id, ItemResponse item, Integer quantity, List<@Valid TotalResponse> totals) {
    this.id = id;
    this.item = item;
    this.quantity = quantity;
    this.totals = totals;
  }

  public LineItemResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Get id
   * @return id
   */
  @NotNull 
  @Schema(name = "id", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public LineItemResponse item(ItemResponse item) {
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

  public LineItemResponse quantity(Integer quantity) {
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

  public LineItemResponse totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public LineItemResponse addTotalsItem(TotalResponse totalsItem) {
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

  public LineItemResponse parentId(@Nullable String parentId) {
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
    LineItemResponse lineItemResponse = (LineItemResponse) o;
    return Objects.equals(this.id, lineItemResponse.id) &&
        Objects.equals(this.item, lineItemResponse.item) &&
        Objects.equals(this.quantity, lineItemResponse.quantity) &&
        Objects.equals(this.totals, lineItemResponse.totals) &&
        Objects.equals(this.parentId, lineItemResponse.parentId);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, item, quantity, totals, parentId);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class LineItemResponse {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    item: ").append(toIndentedString(item)).append("\n");
    sb.append("    quantity: ").append(toIndentedString(quantity)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
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

    private LineItemResponse instance;

    public Builder() {
      this(new LineItemResponse());
    }

    protected Builder(LineItemResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(LineItemResponse value) { 
      this.instance.setId(value.id);
      this.instance.setItem(value.item);
      this.instance.setQuantity(value.quantity);
      this.instance.setTotals(value.totals);
      this.instance.setParentId(value.parentId);
      return this;
    }

    public LineItemResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public LineItemResponse.Builder item(ItemResponse item) {
      this.instance.item(item);
      return this;
    }
    
    public LineItemResponse.Builder quantity(Integer quantity) {
      this.instance.quantity(quantity);
      return this;
    }
    
    public LineItemResponse.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    public LineItemResponse.Builder parentId(String parentId) {
      this.instance.parentId(parentId);
      return this;
    }
    
    /**
    * returns a built LineItemResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public LineItemResponse build() {
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
  public static LineItemResponse.Builder builder() {
    return new LineItemResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public LineItemResponse.Builder toBuilder() {
    LineItemResponse.Builder builder = new LineItemResponse.Builder();
    return builder.copyOf(this);
  }

}

