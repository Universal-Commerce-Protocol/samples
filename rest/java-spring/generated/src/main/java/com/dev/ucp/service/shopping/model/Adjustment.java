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
import com.dev.ucp.service.shopping.model.AdjustmentLineItemsInner;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * Append-only event that exists independently of fulfillment. Typically represents money movements but can be any post-order change. Polymorphic type that can optionally reference line items.
 */

@Schema(name = "Adjustment", description = "Append-only event that exists independently of fulfillment. Typically represents money movements but can be any post-order change. Polymorphic type that can optionally reference line items.")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class Adjustment {

  private String id;

  private String type;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private OffsetDateTime occurredAt;

  /**
   * Adjustment status.
   */
  public enum StatusEnum {
    PENDING("pending"),
    
    COMPLETED("completed"),
    
    FAILED("failed");

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

  @Valid
  private List<@Valid AdjustmentLineItemsInner> lineItems = new ArrayList<>();

  private @Nullable Integer amount;

  private @Nullable String description;

  public Adjustment() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public Adjustment(String id, String type, OffsetDateTime occurredAt, StatusEnum status) {
    this.id = id;
    this.type = type;
    this.occurredAt = occurredAt;
    this.status = status;
  }

  public Adjustment id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Adjustment event identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Adjustment event identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public Adjustment type(String type) {
    this.type = type;
    return this;
  }

  /**
   * Type of adjustment (open string). Typically money-related like: refund, return, credit, price_adjustment, dispute, cancellation. Can be any value that makes sense for the merchant's business.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Type of adjustment (open string). Typically money-related like: refund, return, credit, price_adjustment, dispute, cancellation. Can be any value that makes sense for the merchant's business.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public Adjustment occurredAt(OffsetDateTime occurredAt) {
    this.occurredAt = occurredAt;
    return this;
  }

  /**
   * RFC 3339 timestamp when this adjustment occurred.
   * @return occurredAt
   */
  @NotNull @Valid 
  @Schema(name = "occurred_at", description = "RFC 3339 timestamp when this adjustment occurred.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("occurred_at")
  public OffsetDateTime getOccurredAt() {
    return occurredAt;
  }

  public void setOccurredAt(OffsetDateTime occurredAt) {
    this.occurredAt = occurredAt;
  }

  public Adjustment status(StatusEnum status) {
    this.status = status;
    return this;
  }

  /**
   * Adjustment status.
   * @return status
   */
  @NotNull 
  @Schema(name = "status", description = "Adjustment status.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("status")
  public StatusEnum getStatus() {
    return status;
  }

  public void setStatus(StatusEnum status) {
    this.status = status;
  }

  public Adjustment lineItems(List<@Valid AdjustmentLineItemsInner> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public Adjustment addLineItemsItem(AdjustmentLineItemsInner lineItemsItem) {
    if (this.lineItems == null) {
      this.lineItems = new ArrayList<>();
    }
    this.lineItems.add(lineItemsItem);
    return this;
  }

  /**
   * Which line items and quantities are affected (optional).
   * @return lineItems
   */
  @Valid 
  @Schema(name = "line_items", description = "Which line items and quantities are affected (optional).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("line_items")
  public List<@Valid AdjustmentLineItemsInner> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid AdjustmentLineItemsInner> lineItems) {
    this.lineItems = lineItems;
  }

  public Adjustment amount(@Nullable Integer amount) {
    this.amount = amount;
    return this;
  }

  /**
   * Amount in minor units (cents) for refunds, credits, price adjustments (optional).
   * @return amount
   */
  
  @Schema(name = "amount", description = "Amount in minor units (cents) for refunds, credits, price adjustments (optional).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("amount")
  public @Nullable Integer getAmount() {
    return amount;
  }

  public void setAmount(@Nullable Integer amount) {
    this.amount = amount;
  }

  public Adjustment description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Human-readable reason or description (e.g., 'Defective item', 'Customer requested').
   * @return description
   */
  
  @Schema(name = "description", description = "Human-readable reason or description (e.g., 'Defective item', 'Customer requested').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  public void setDescription(@Nullable String description) {
    this.description = description;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    Adjustment adjustment = (Adjustment) o;
    return Objects.equals(this.id, adjustment.id) &&
        Objects.equals(this.type, adjustment.type) &&
        Objects.equals(this.occurredAt, adjustment.occurredAt) &&
        Objects.equals(this.status, adjustment.status) &&
        Objects.equals(this.lineItems, adjustment.lineItems) &&
        Objects.equals(this.amount, adjustment.amount) &&
        Objects.equals(this.description, adjustment.description);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, type, occurredAt, status, lineItems, amount, description);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Adjustment {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    occurredAt: ").append(toIndentedString(occurredAt)).append("\n");
    sb.append("    status: ").append(toIndentedString(status)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    amount: ").append(toIndentedString(amount)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
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

    private Adjustment instance;

    public Builder() {
      this(new Adjustment());
    }

    protected Builder(Adjustment instance) {
      this.instance = instance;
    }

    protected Builder copyOf(Adjustment value) { 
      this.instance.setId(value.id);
      this.instance.setType(value.type);
      this.instance.setOccurredAt(value.occurredAt);
      this.instance.setStatus(value.status);
      this.instance.setLineItems(value.lineItems);
      this.instance.setAmount(value.amount);
      this.instance.setDescription(value.description);
      return this;
    }

    public Adjustment.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public Adjustment.Builder type(String type) {
      this.instance.type(type);
      return this;
    }
    
    public Adjustment.Builder occurredAt(OffsetDateTime occurredAt) {
      this.instance.occurredAt(occurredAt);
      return this;
    }
    
    public Adjustment.Builder status(StatusEnum status) {
      this.instance.status(status);
      return this;
    }
    
    public Adjustment.Builder lineItems(List<AdjustmentLineItemsInner> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public Adjustment.Builder amount(Integer amount) {
      this.instance.amount(amount);
      return this;
    }
    
    public Adjustment.Builder description(String description) {
      this.instance.description(description);
      return this;
    }
    
    /**
    * returns a built Adjustment instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public Adjustment build() {
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
  public static Adjustment.Builder builder() {
    return new Adjustment.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public Adjustment.Builder toBuilder() {
    Adjustment.Builder builder = new Adjustment.Builder();
    return builder.copyOf(this);
  }

}

