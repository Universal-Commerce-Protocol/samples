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
import com.dev.ucp.service.shopping.model.ItemUpdateRequest;
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

@Schema(name = "Line_Item_Update_Request", description = "Line item object. Expected to use the currency of the parent object.")
@JsonTypeName("Line_Item_Update_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class LineItemUpdateRequest {

  private @Nullable String id;

  private ItemUpdateRequest item;

  private Integer quantity;

  private @Nullable String parentId;

  public LineItemUpdateRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public LineItemUpdateRequest(ItemUpdateRequest item, Integer quantity) {
    this.item = item;
    this.quantity = quantity;
  }

  public LineItemUpdateRequest id(@Nullable String id) {
    this.id = id;
    return this;
  }

  /**
   * Get id
   * @return id
   */
  
  @Schema(name = "id", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("id")
  public @Nullable String getId() {
    return id;
  }

  public void setId(@Nullable String id) {
    this.id = id;
  }

  public LineItemUpdateRequest item(ItemUpdateRequest item) {
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
  public ItemUpdateRequest getItem() {
    return item;
  }

  public void setItem(ItemUpdateRequest item) {
    this.item = item;
  }

  public LineItemUpdateRequest quantity(Integer quantity) {
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

  public LineItemUpdateRequest parentId(@Nullable String parentId) {
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
    LineItemUpdateRequest lineItemUpdateRequest = (LineItemUpdateRequest) o;
    return Objects.equals(this.id, lineItemUpdateRequest.id) &&
        Objects.equals(this.item, lineItemUpdateRequest.item) &&
        Objects.equals(this.quantity, lineItemUpdateRequest.quantity) &&
        Objects.equals(this.parentId, lineItemUpdateRequest.parentId);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, item, quantity, parentId);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class LineItemUpdateRequest {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    item: ").append(toIndentedString(item)).append("\n");
    sb.append("    quantity: ").append(toIndentedString(quantity)).append("\n");
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

    private LineItemUpdateRequest instance;

    public Builder() {
      this(new LineItemUpdateRequest());
    }

    protected Builder(LineItemUpdateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(LineItemUpdateRequest value) { 
      this.instance.setId(value.id);
      this.instance.setItem(value.item);
      this.instance.setQuantity(value.quantity);
      this.instance.setParentId(value.parentId);
      return this;
    }

    public LineItemUpdateRequest.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public LineItemUpdateRequest.Builder item(ItemUpdateRequest item) {
      this.instance.item(item);
      return this;
    }
    
    public LineItemUpdateRequest.Builder quantity(Integer quantity) {
      this.instance.quantity(quantity);
      return this;
    }
    
    public LineItemUpdateRequest.Builder parentId(String parentId) {
      this.instance.parentId(parentId);
      return this;
    }
    
    /**
    * returns a built LineItemUpdateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public LineItemUpdateRequest build() {
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
  public static LineItemUpdateRequest.Builder builder() {
    return new LineItemUpdateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public LineItemUpdateRequest.Builder toBuilder() {
    LineItemUpdateRequest.Builder builder = new LineItemUpdateRequest.Builder();
    return builder.copyOf(this);
  }

}

