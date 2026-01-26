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
 * Breakdown of how a discount amount was allocated to a specific target.
 */

@Schema(name = "discount_request_applied_inner_allocations_inner", description = "Breakdown of how a discount amount was allocated to a specific target.")
@JsonTypeName("discount_request_applied_inner_allocations_inner")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class DiscountRequestAppliedInnerAllocationsInner {

  private String path;

  private Integer amount;

  public DiscountRequestAppliedInnerAllocationsInner() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public DiscountRequestAppliedInnerAllocationsInner(String path, Integer amount) {
    this.path = path;
    this.amount = amount;
  }

  public DiscountRequestAppliedInnerAllocationsInner path(String path) {
    this.path = path;
    return this;
  }

  /**
   * JSONPath to the allocation target (e.g., '$.line_items[0]', '$.totals.shipping').
   * @return path
   */
  @NotNull 
  @Schema(name = "path", description = "JSONPath to the allocation target (e.g., '$.line_items[0]', '$.totals.shipping').", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("path")
  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public DiscountRequestAppliedInnerAllocationsInner amount(Integer amount) {
    this.amount = amount;
    return this;
  }

  /**
   * Amount allocated to this target in minor (cents) currency units.
   * minimum: 0
   * @return amount
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "amount", description = "Amount allocated to this target in minor (cents) currency units.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("amount")
  public Integer getAmount() {
    return amount;
  }

  public void setAmount(Integer amount) {
    this.amount = amount;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    DiscountRequestAppliedInnerAllocationsInner discountRequestAppliedInnerAllocationsInner = (DiscountRequestAppliedInnerAllocationsInner) o;
    return Objects.equals(this.path, discountRequestAppliedInnerAllocationsInner.path) &&
        Objects.equals(this.amount, discountRequestAppliedInnerAllocationsInner.amount);
  }

  @Override
  public int hashCode() {
    return Objects.hash(path, amount);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class DiscountRequestAppliedInnerAllocationsInner {\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    amount: ").append(toIndentedString(amount)).append("\n");
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

    private DiscountRequestAppliedInnerAllocationsInner instance;

    public Builder() {
      this(new DiscountRequestAppliedInnerAllocationsInner());
    }

    protected Builder(DiscountRequestAppliedInnerAllocationsInner instance) {
      this.instance = instance;
    }

    protected Builder copyOf(DiscountRequestAppliedInnerAllocationsInner value) { 
      this.instance.setPath(value.path);
      this.instance.setAmount(value.amount);
      return this;
    }

    public DiscountRequestAppliedInnerAllocationsInner.Builder path(String path) {
      this.instance.path(path);
      return this;
    }
    
    public DiscountRequestAppliedInnerAllocationsInner.Builder amount(Integer amount) {
      this.instance.amount(amount);
      return this;
    }
    
    /**
    * returns a built DiscountRequestAppliedInnerAllocationsInner instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public DiscountRequestAppliedInnerAllocationsInner build() {
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
  public static DiscountRequestAppliedInnerAllocationsInner.Builder builder() {
    return new DiscountRequestAppliedInnerAllocationsInner.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public DiscountRequestAppliedInnerAllocationsInner.Builder toBuilder() {
    DiscountRequestAppliedInnerAllocationsInner.Builder builder = new DiscountRequestAppliedInnerAllocationsInner.Builder();
    return builder.copyOf(this);
  }

}

