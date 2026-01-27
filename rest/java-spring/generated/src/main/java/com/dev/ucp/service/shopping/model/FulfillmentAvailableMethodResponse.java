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
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.openapitools.jackson.nullable.JsonNullable;
import org.springframework.lang.Nullable;
import java.util.NoSuchElementException;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

import java.util.Map;
import java.util.HashMap;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
/**
 * Inventory availability hint for a fulfillment method type.
 */

@Schema(name = "Fulfillment_Available_Method_Response", description = "Inventory availability hint for a fulfillment method type.")
@JsonTypeName("Fulfillment_Available_Method_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentAvailableMethodResponse {

  /**
   * Fulfillment method type this availability applies to.
   */
  public enum TypeEnum {
    SHIPPING("shipping"),
    
    PICKUP("pickup");

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

  @Valid
  private List<String> lineItemIds = new ArrayList<>();

  private JsonNullable<String> fulfillableOn = JsonNullable.<String>undefined();

  private @Nullable String description;

  public FulfillmentAvailableMethodResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentAvailableMethodResponse(TypeEnum type, List<String> lineItemIds) {
    this.type = type;
    this.lineItemIds = lineItemIds;
  }

  public FulfillmentAvailableMethodResponse type(TypeEnum type) {
    this.type = type;
    return this;
  }

  /**
   * Fulfillment method type this availability applies to.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Fulfillment method type this availability applies to.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public TypeEnum getType() {
    return type;
  }

  public void setType(TypeEnum type) {
    this.type = type;
  }

  public FulfillmentAvailableMethodResponse lineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
    return this;
  }

  public FulfillmentAvailableMethodResponse addLineItemIdsItem(String lineItemIdsItem) {
    if (this.lineItemIds == null) {
      this.lineItemIds = new ArrayList<>();
    }
    this.lineItemIds.add(lineItemIdsItem);
    return this;
  }

  /**
   * Line items available for this fulfillment method.
   * @return lineItemIds
   */
  @NotNull 
  @Schema(name = "line_item_ids", description = "Line items available for this fulfillment method.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_item_ids")
  public List<String> getLineItemIds() {
    return lineItemIds;
  }

  public void setLineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
  }

  public FulfillmentAvailableMethodResponse fulfillableOn(String fulfillableOn) {
    this.fulfillableOn = JsonNullable.of(fulfillableOn);
    return this;
  }

  /**
   * 'now' for immediate availability, or ISO 8601 date for future (preorders, transfers).
   * @return fulfillableOn
   */
  
  @Schema(name = "fulfillable_on", description = "'now' for immediate availability, or ISO 8601 date for future (preorders, transfers).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("fulfillable_on")
  public JsonNullable<String> getFulfillableOn() {
    return fulfillableOn;
  }

  public void setFulfillableOn(JsonNullable<String> fulfillableOn) {
    this.fulfillableOn = fulfillableOn;
  }

  public FulfillmentAvailableMethodResponse description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Human-readable availability info (e.g., 'Available for pickup at Downtown Store today').
   * @return description
   */
  
  @Schema(name = "description", description = "Human-readable availability info (e.g., 'Available for pickup at Downtown Store today').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  public void setDescription(@Nullable String description) {
    this.description = description;
  }
    /**
    * A container for additional, undeclared properties.
    * This is a holder for any undeclared properties as specified with
    * the 'additionalProperties' keyword in the OAS document.
    */
    private Map<String, JsonNode> additionalProperties;

    /**
    * Set the additional (undeclared) property with the specified name and value.
    * If the property does not already exist, create it otherwise replace it.
    */
    @JsonAnySetter
    public FulfillmentAvailableMethodResponse putAdditionalProperty(String key, JsonNode value) {
        if (this.additionalProperties == null) {
            this.additionalProperties = new HashMap<String, JsonNode>();
        }
        this.additionalProperties.put(key, value);
        return this;
    }

    /**
    * Return the additional (undeclared) property.
    */
    @JsonAnyGetter
    public Map<String, JsonNode> getAdditionalProperties() {
        return additionalProperties;
    }

    /**
    * Return the additional (undeclared) property with the specified name.
    */
    public JsonNode getAdditionalProperty(String key) {
        if (this.additionalProperties == null) {
            return null;
        }
        return this.additionalProperties.get(key);
    }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FulfillmentAvailableMethodResponse fulfillmentAvailableMethodResponse = (FulfillmentAvailableMethodResponse) o;
    return Objects.equals(this.type, fulfillmentAvailableMethodResponse.type) &&
        Objects.equals(this.lineItemIds, fulfillmentAvailableMethodResponse.lineItemIds) &&
        equalsNullable(this.fulfillableOn, fulfillmentAvailableMethodResponse.fulfillableOn) &&
        Objects.equals(this.description, fulfillmentAvailableMethodResponse.description) &&
    Objects.equals(this.additionalProperties, fulfillmentAvailableMethodResponse.additionalProperties);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, lineItemIds, hashCodeNullable(fulfillableOn), description, additionalProperties);
  }

  private static <T> int hashCodeNullable(JsonNullable<T> a) {
    if (a == null) {
      return 1;
    }
    return a.isPresent() ? Arrays.deepHashCode(new Object[]{a.get()}) : 31;
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentAvailableMethodResponse {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    lineItemIds: ").append(toIndentedString(lineItemIds)).append("\n");
    sb.append("    fulfillableOn: ").append(toIndentedString(fulfillableOn)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    
    sb.append("    additionalProperties: ").append(toIndentedString(additionalProperties)).append("\n");
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

    private FulfillmentAvailableMethodResponse instance;

    public Builder() {
      this(new FulfillmentAvailableMethodResponse());
    }

    protected Builder(FulfillmentAvailableMethodResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentAvailableMethodResponse value) { 
      this.instance.setType(value.type);
      this.instance.setLineItemIds(value.lineItemIds);
      this.instance.setFulfillableOn(value.fulfillableOn);
      this.instance.setDescription(value.description);
      return this;
    }

    public FulfillmentAvailableMethodResponse.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public FulfillmentAvailableMethodResponse.Builder lineItemIds(List<String> lineItemIds) {
      this.instance.lineItemIds(lineItemIds);
      return this;
    }
    
    public FulfillmentAvailableMethodResponse.Builder fulfillableOn(String fulfillableOn) {
      this.instance.fulfillableOn(fulfillableOn);
      return this;
    }
    
    public FulfillmentAvailableMethodResponse.Builder fulfillableOn(JsonNullable<String> fulfillableOn) {
      this.instance.fulfillableOn = fulfillableOn;
      return this;
    }
    
    public FulfillmentAvailableMethodResponse.Builder description(String description) {
      this.instance.description(description);
      return this;
    }
    
    public FulfillmentAvailableMethodResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built FulfillmentAvailableMethodResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentAvailableMethodResponse build() {
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
  public static FulfillmentAvailableMethodResponse.Builder builder() {
    return new FulfillmentAvailableMethodResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentAvailableMethodResponse.Builder toBuilder() {
    FulfillmentAvailableMethodResponse.Builder builder = new FulfillmentAvailableMethodResponse.Builder();
    return builder.copyOf(this);
  }

}

