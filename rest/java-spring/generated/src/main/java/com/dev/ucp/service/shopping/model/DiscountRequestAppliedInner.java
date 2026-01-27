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
import com.dev.ucp.service.shopping.model.DiscountRequestAppliedInnerAllocationsInner;
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
 * A discount that was successfully applied.
 */

@Schema(name = "discount_request_applied_inner", description = "A discount that was successfully applied.")
@JsonTypeName("discount_request_applied_inner")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class DiscountRequestAppliedInner {

  private @Nullable String code;

  private String title;

  private Integer amount;

  private Boolean automatic = false;

  /**
   * Allocation method. 'each' = applied independently per item. 'across' = split proportionally by value.
   */
  public enum MethodEnum {
    EACH("each"),
    
    ACROSS("across");

    private final String value;

    MethodEnum(String value) {
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
    public static MethodEnum fromValue(String value) {
      for (MethodEnum b : MethodEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private @Nullable MethodEnum method;

  private @Nullable Integer priority;

  @Valid
  private List<@Valid DiscountRequestAppliedInnerAllocationsInner> allocations = new ArrayList<>();

  public DiscountRequestAppliedInner() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public DiscountRequestAppliedInner(String title, Integer amount) {
    this.title = title;
    this.amount = amount;
  }

  public DiscountRequestAppliedInner code(@Nullable String code) {
    this.code = code;
    return this;
  }

  /**
   * The discount code. Omitted for automatic discounts.
   * @return code
   */
  
  @Schema(name = "code", description = "The discount code. Omitted for automatic discounts.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("code")
  public @Nullable String getCode() {
    return code;
  }

  public void setCode(@Nullable String code) {
    this.code = code;
  }

  public DiscountRequestAppliedInner title(String title) {
    this.title = title;
    return this;
  }

  /**
   * Human-readable discount name (e.g., 'Summer Sale 20% Off').
   * @return title
   */
  @NotNull 
  @Schema(name = "title", description = "Human-readable discount name (e.g., 'Summer Sale 20% Off').", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("title")
  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public DiscountRequestAppliedInner amount(Integer amount) {
    this.amount = amount;
    return this;
  }

  /**
   * Total discount amount in minor (cents) currency units.
   * minimum: 0
   * @return amount
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "amount", description = "Total discount amount in minor (cents) currency units.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("amount")
  public Integer getAmount() {
    return amount;
  }

  public void setAmount(Integer amount) {
    this.amount = amount;
  }

  public DiscountRequestAppliedInner automatic(Boolean automatic) {
    this.automatic = automatic;
    return this;
  }

  /**
   * True if applied automatically by merchant rules (no code required).
   * @return automatic
   */
  
  @Schema(name = "automatic", description = "True if applied automatically by merchant rules (no code required).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("automatic")
  public Boolean getAutomatic() {
    return automatic;
  }

  public void setAutomatic(Boolean automatic) {
    this.automatic = automatic;
  }

  public DiscountRequestAppliedInner method(@Nullable MethodEnum method) {
    this.method = method;
    return this;
  }

  /**
   * Allocation method. 'each' = applied independently per item. 'across' = split proportionally by value.
   * @return method
   */
  
  @Schema(name = "method", description = "Allocation method. 'each' = applied independently per item. 'across' = split proportionally by value.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("method")
  public @Nullable MethodEnum getMethod() {
    return method;
  }

  public void setMethod(@Nullable MethodEnum method) {
    this.method = method;
  }

  public DiscountRequestAppliedInner priority(@Nullable Integer priority) {
    this.priority = priority;
    return this;
  }

  /**
   * Stacking order for discount calculation. Lower numbers applied first (1 = first).
   * minimum: 1
   * @return priority
   */
  @Min(value = 1) 
  @Schema(name = "priority", description = "Stacking order for discount calculation. Lower numbers applied first (1 = first).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("priority")
  public @Nullable Integer getPriority() {
    return priority;
  }

  public void setPriority(@Nullable Integer priority) {
    this.priority = priority;
  }

  public DiscountRequestAppliedInner allocations(List<@Valid DiscountRequestAppliedInnerAllocationsInner> allocations) {
    this.allocations = allocations;
    return this;
  }

  public DiscountRequestAppliedInner addAllocationsItem(DiscountRequestAppliedInnerAllocationsInner allocationsItem) {
    if (this.allocations == null) {
      this.allocations = new ArrayList<>();
    }
    this.allocations.add(allocationsItem);
    return this;
  }

  /**
   * Breakdown of where this discount was allocated. Sum of allocation amounts equals total amount.
   * @return allocations
   */
  @Valid 
  @Schema(name = "allocations", description = "Breakdown of where this discount was allocated. Sum of allocation amounts equals total amount.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("allocations")
  public List<@Valid DiscountRequestAppliedInnerAllocationsInner> getAllocations() {
    return allocations;
  }

  public void setAllocations(List<@Valid DiscountRequestAppliedInnerAllocationsInner> allocations) {
    this.allocations = allocations;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    DiscountRequestAppliedInner discountRequestAppliedInner = (DiscountRequestAppliedInner) o;
    return Objects.equals(this.code, discountRequestAppliedInner.code) &&
        Objects.equals(this.title, discountRequestAppliedInner.title) &&
        Objects.equals(this.amount, discountRequestAppliedInner.amount) &&
        Objects.equals(this.automatic, discountRequestAppliedInner.automatic) &&
        Objects.equals(this.method, discountRequestAppliedInner.method) &&
        Objects.equals(this.priority, discountRequestAppliedInner.priority) &&
        Objects.equals(this.allocations, discountRequestAppliedInner.allocations);
  }

  @Override
  public int hashCode() {
    return Objects.hash(code, title, amount, automatic, method, priority, allocations);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class DiscountRequestAppliedInner {\n");
    sb.append("    code: ").append(toIndentedString(code)).append("\n");
    sb.append("    title: ").append(toIndentedString(title)).append("\n");
    sb.append("    amount: ").append(toIndentedString(amount)).append("\n");
    sb.append("    automatic: ").append(toIndentedString(automatic)).append("\n");
    sb.append("    method: ").append(toIndentedString(method)).append("\n");
    sb.append("    priority: ").append(toIndentedString(priority)).append("\n");
    sb.append("    allocations: ").append(toIndentedString(allocations)).append("\n");
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

    private DiscountRequestAppliedInner instance;

    public Builder() {
      this(new DiscountRequestAppliedInner());
    }

    protected Builder(DiscountRequestAppliedInner instance) {
      this.instance = instance;
    }

    protected Builder copyOf(DiscountRequestAppliedInner value) { 
      this.instance.setCode(value.code);
      this.instance.setTitle(value.title);
      this.instance.setAmount(value.amount);
      this.instance.setAutomatic(value.automatic);
      this.instance.setMethod(value.method);
      this.instance.setPriority(value.priority);
      this.instance.setAllocations(value.allocations);
      return this;
    }

    public DiscountRequestAppliedInner.Builder code(String code) {
      this.instance.code(code);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder title(String title) {
      this.instance.title(title);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder amount(Integer amount) {
      this.instance.amount(amount);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder automatic(Boolean automatic) {
      this.instance.automatic(automatic);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder method(MethodEnum method) {
      this.instance.method(method);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder priority(Integer priority) {
      this.instance.priority(priority);
      return this;
    }
    
    public DiscountRequestAppliedInner.Builder allocations(List<DiscountRequestAppliedInnerAllocationsInner> allocations) {
      this.instance.allocations(allocations);
      return this;
    }
    
    /**
    * returns a built DiscountRequestAppliedInner instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public DiscountRequestAppliedInner build() {
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
  public static DiscountRequestAppliedInner.Builder builder() {
    return new DiscountRequestAppliedInner.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public DiscountRequestAppliedInner.Builder toBuilder() {
    DiscountRequestAppliedInner.Builder builder = new DiscountRequestAppliedInner.Builder();
    return builder.copyOf(this);
  }

}

