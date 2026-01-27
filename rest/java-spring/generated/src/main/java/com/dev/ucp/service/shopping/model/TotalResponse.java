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
import com.fasterxml.jackson.annotation.JsonValue;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * TotalResponse
 */

@JsonTypeName("Total_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class TotalResponse {

  /**
   * Type of total categorization.
   */
  public enum TypeEnum {
    ITEMS_DISCOUNT("items_discount"),
    
    SUBTOTAL("subtotal"),
    
    DISCOUNT("discount"),
    
    FULFILLMENT("fulfillment"),
    
    TAX("tax"),
    
    FEE("fee"),
    
    TOTAL("total");

    private final String value;

    TypeEnum(String value) {
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
    public static TypeEnum fromValue(String value) {
      for (TypeEnum b : TypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private TypeEnum type;

  private @Nullable String displayText;

  private Integer amount;

  public TotalResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public TotalResponse(TypeEnum type, Integer amount) {
    this.type = type;
    this.amount = amount;
  }

  public TotalResponse type(TypeEnum type) {
    this.type = type;
    return this;
  }

  /**
   * Type of total categorization.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Type of total categorization.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public TypeEnum getType() {
    return type;
  }

  public void setType(TypeEnum type) {
    this.type = type;
  }

  public TotalResponse displayText(@Nullable String displayText) {
    this.displayText = displayText;
    return this;
  }

  /**
   * Text to display against the amount. Should reflect appropriate method (e.g., 'Shipping', 'Delivery').
   * @return displayText
   */
  
  @Schema(name = "display_text", description = "Text to display against the amount. Should reflect appropriate method (e.g., 'Shipping', 'Delivery').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("display_text")
  public @Nullable String getDisplayText() {
    return displayText;
  }

  public void setDisplayText(@Nullable String displayText) {
    this.displayText = displayText;
  }

  public TotalResponse amount(Integer amount) {
    this.amount = amount;
    return this;
  }

  /**
   * If type == total, sums subtotal - discount + fulfillment + tax + fee. Should be >= 0. Amount in minor (cents) currency units.
   * minimum: 0
   * @return amount
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "amount", description = "If type == total, sums subtotal - discount + fulfillment + tax + fee. Should be >= 0. Amount in minor (cents) currency units.", requiredMode = Schema.RequiredMode.REQUIRED)
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
    TotalResponse totalResponse = (TotalResponse) o;
    return Objects.equals(this.type, totalResponse.type) &&
        Objects.equals(this.displayText, totalResponse.displayText) &&
        Objects.equals(this.amount, totalResponse.amount);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, displayText, amount);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TotalResponse {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    displayText: ").append(toIndentedString(displayText)).append("\n");
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

    private TotalResponse instance;

    public Builder() {
      this(new TotalResponse());
    }

    protected Builder(TotalResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(TotalResponse value) { 
      this.instance.setType(value.type);
      this.instance.setDisplayText(value.displayText);
      this.instance.setAmount(value.amount);
      return this;
    }

    public TotalResponse.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public TotalResponse.Builder displayText(String displayText) {
      this.instance.displayText(displayText);
      return this;
    }
    
    public TotalResponse.Builder amount(Integer amount) {
      this.instance.amount(amount);
      return this;
    }
    
    /**
    * returns a built TotalResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public TotalResponse build() {
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
  public static TotalResponse.Builder builder() {
    return new TotalResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public TotalResponse.Builder toBuilder() {
    TotalResponse.Builder builder = new TotalResponse.Builder();
    return builder.copyOf(this);
  }

}

