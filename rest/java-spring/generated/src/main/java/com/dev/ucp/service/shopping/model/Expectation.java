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
import com.dev.ucp.service.shopping.model.ExpectationLineItemsInner;
import com.dev.ucp.service.shopping.model.PostalAddress;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
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
 * Buyer-facing fulfillment expectation representing logical groupings of items (e.g., &#39;package&#39;). Can be split, merged, or adjusted post-order to set buyer expectations for when/how items arrive.
 */

@Schema(name = "Expectation", description = "Buyer-facing fulfillment expectation representing logical groupings of items (e.g., 'package'). Can be split, merged, or adjusted post-order to set buyer expectations for when/how items arrive.")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class Expectation {

  private String id;

  @Valid
  private List<@Valid ExpectationLineItemsInner> lineItems = new ArrayList<>();

  /**
   * Delivery method type (shipping, pickup, digital).
   */
  public enum MethodTypeEnum {
    SHIPPING("shipping"),
    
    PICKUP("pickup"),
    
    DIGITAL("digital");

    private final String value;

    MethodTypeEnum(String value) {
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
    public static MethodTypeEnum fromValue(String value) {
      for (MethodTypeEnum b : MethodTypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private MethodTypeEnum methodType;

  private PostalAddress destination;

  private @Nullable String description;

  private @Nullable String fulfillableOn;

  public Expectation() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public Expectation(String id, List<@Valid ExpectationLineItemsInner> lineItems, MethodTypeEnum methodType, PostalAddress destination) {
    this.id = id;
    this.lineItems = lineItems;
    this.methodType = methodType;
    this.destination = destination;
  }

  public Expectation id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Expectation identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Expectation identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public Expectation lineItems(List<@Valid ExpectationLineItemsInner> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public Expectation addLineItemsItem(ExpectationLineItemsInner lineItemsItem) {
    if (this.lineItems == null) {
      this.lineItems = new ArrayList<>();
    }
    this.lineItems.add(lineItemsItem);
    return this;
  }

  /**
   * Which line items and quantities are in this expectation.
   * @return lineItems
   */
  @NotNull @Valid 
  @Schema(name = "line_items", description = "Which line items and quantities are in this expectation.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_items")
  public List<@Valid ExpectationLineItemsInner> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid ExpectationLineItemsInner> lineItems) {
    this.lineItems = lineItems;
  }

  public Expectation methodType(MethodTypeEnum methodType) {
    this.methodType = methodType;
    return this;
  }

  /**
   * Delivery method type (shipping, pickup, digital).
   * @return methodType
   */
  @NotNull 
  @Schema(name = "method_type", description = "Delivery method type (shipping, pickup, digital).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("method_type")
  public MethodTypeEnum getMethodType() {
    return methodType;
  }

  public void setMethodType(MethodTypeEnum methodType) {
    this.methodType = methodType;
  }

  public Expectation destination(PostalAddress destination) {
    this.destination = destination;
    return this;
  }

  /**
   * Get destination
   * @return destination
   */
  @NotNull @Valid 
  @Schema(name = "destination", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("destination")
  public PostalAddress getDestination() {
    return destination;
  }

  public void setDestination(PostalAddress destination) {
    this.destination = destination;
  }

  public Expectation description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Human-readable delivery description (e.g., 'Arrives in 5-8 business days').
   * @return description
   */
  
  @Schema(name = "description", description = "Human-readable delivery description (e.g., 'Arrives in 5-8 business days').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  public void setDescription(@Nullable String description) {
    this.description = description;
  }

  public Expectation fulfillableOn(@Nullable String fulfillableOn) {
    this.fulfillableOn = fulfillableOn;
    return this;
  }

  /**
   * When this expectation can be fulfilled: 'now' or ISO 8601 timestamp for future date (backorder, pre-order).
   * @return fulfillableOn
   */
  
  @Schema(name = "fulfillable_on", description = "When this expectation can be fulfilled: 'now' or ISO 8601 timestamp for future date (backorder, pre-order).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("fulfillable_on")
  public @Nullable String getFulfillableOn() {
    return fulfillableOn;
  }

  public void setFulfillableOn(@Nullable String fulfillableOn) {
    this.fulfillableOn = fulfillableOn;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    Expectation expectation = (Expectation) o;
    return Objects.equals(this.id, expectation.id) &&
        Objects.equals(this.lineItems, expectation.lineItems) &&
        Objects.equals(this.methodType, expectation.methodType) &&
        Objects.equals(this.destination, expectation.destination) &&
        Objects.equals(this.description, expectation.description) &&
        Objects.equals(this.fulfillableOn, expectation.fulfillableOn);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, lineItems, methodType, destination, description, fulfillableOn);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Expectation {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    methodType: ").append(toIndentedString(methodType)).append("\n");
    sb.append("    destination: ").append(toIndentedString(destination)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    fulfillableOn: ").append(toIndentedString(fulfillableOn)).append("\n");
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

    private Expectation instance;

    public Builder() {
      this(new Expectation());
    }

    protected Builder(Expectation instance) {
      this.instance = instance;
    }

    protected Builder copyOf(Expectation value) { 
      this.instance.setId(value.id);
      this.instance.setLineItems(value.lineItems);
      this.instance.setMethodType(value.methodType);
      this.instance.setDestination(value.destination);
      this.instance.setDescription(value.description);
      this.instance.setFulfillableOn(value.fulfillableOn);
      return this;
    }

    public Expectation.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public Expectation.Builder lineItems(List<ExpectationLineItemsInner> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public Expectation.Builder methodType(MethodTypeEnum methodType) {
      this.instance.methodType(methodType);
      return this;
    }
    
    public Expectation.Builder destination(PostalAddress destination) {
      this.instance.destination(destination);
      return this;
    }
    
    public Expectation.Builder description(String description) {
      this.instance.description(description);
      return this;
    }
    
    public Expectation.Builder fulfillableOn(String fulfillableOn) {
      this.instance.fulfillableOn(fulfillableOn);
      return this;
    }
    
    /**
    * returns a built Expectation instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public Expectation build() {
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
  public static Expectation.Builder builder() {
    return new Expectation.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public Expectation.Builder toBuilder() {
    Expectation.Builder builder = new Expectation.Builder();
    return builder.copyOf(this);
  }

}

