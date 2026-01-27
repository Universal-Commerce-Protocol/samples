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
import com.dev.ucp.service.shopping.model.FulfillmentDestinationRequest;
import com.dev.ucp.service.shopping.model.FulfillmentGroupCreateRequest;
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
 * A fulfillment method (shipping or pickup) with destinations and groups.
 */

@Schema(name = "Fulfillment_Method_Create_Request", description = "A fulfillment method (shipping or pickup) with destinations and groups.")
@JsonTypeName("Fulfillment_Method_Create_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentMethodCreateRequest {

  /**
   * Fulfillment method type.
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

  @Valid
  private List<@Valid FulfillmentDestinationRequest> destinations = new ArrayList<>();

  private JsonNullable<String> selectedDestinationId = JsonNullable.<String>undefined();

  @Valid
  private List<FulfillmentGroupCreateRequest> groups = new ArrayList<>();

  public FulfillmentMethodCreateRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentMethodCreateRequest(TypeEnum type) {
    this.type = type;
  }

  public FulfillmentMethodCreateRequest type(TypeEnum type) {
    this.type = type;
    return this;
  }

  /**
   * Fulfillment method type.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Fulfillment method type.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public TypeEnum getType() {
    return type;
  }

  public void setType(TypeEnum type) {
    this.type = type;
  }

  public FulfillmentMethodCreateRequest lineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
    return this;
  }

  public FulfillmentMethodCreateRequest addLineItemIdsItem(String lineItemIdsItem) {
    if (this.lineItemIds == null) {
      this.lineItemIds = new ArrayList<>();
    }
    this.lineItemIds.add(lineItemIdsItem);
    return this;
  }

  /**
   * Line item IDs fulfilled via this method.
   * @return lineItemIds
   */
  
  @Schema(name = "line_item_ids", description = "Line item IDs fulfilled via this method.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("line_item_ids")
  public List<String> getLineItemIds() {
    return lineItemIds;
  }

  public void setLineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
  }

  public FulfillmentMethodCreateRequest destinations(List<@Valid FulfillmentDestinationRequest> destinations) {
    this.destinations = destinations;
    return this;
  }

  public FulfillmentMethodCreateRequest addDestinationsItem(FulfillmentDestinationRequest destinationsItem) {
    if (this.destinations == null) {
      this.destinations = new ArrayList<>();
    }
    this.destinations.add(destinationsItem);
    return this;
  }

  /**
   * Available destinations. For shipping: addresses. For pickup: retail locations.
   * @return destinations
   */
  @Valid 
  @Schema(name = "destinations", description = "Available destinations. For shipping: addresses. For pickup: retail locations.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("destinations")
  public List<@Valid FulfillmentDestinationRequest> getDestinations() {
    return destinations;
  }

  public void setDestinations(List<@Valid FulfillmentDestinationRequest> destinations) {
    this.destinations = destinations;
  }

  public FulfillmentMethodCreateRequest selectedDestinationId(String selectedDestinationId) {
    this.selectedDestinationId = JsonNullable.of(selectedDestinationId);
    return this;
  }

  /**
   * ID of the selected destination.
   * @return selectedDestinationId
   */
  
  @Schema(name = "selected_destination_id", description = "ID of the selected destination.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("selected_destination_id")
  public JsonNullable<String> getSelectedDestinationId() {
    return selectedDestinationId;
  }

  public void setSelectedDestinationId(JsonNullable<String> selectedDestinationId) {
    this.selectedDestinationId = selectedDestinationId;
  }

  public FulfillmentMethodCreateRequest groups(List<FulfillmentGroupCreateRequest> groups) {
    this.groups = groups;
    return this;
  }

  public FulfillmentMethodCreateRequest addGroupsItem(FulfillmentGroupCreateRequest groupsItem) {
    if (this.groups == null) {
      this.groups = new ArrayList<>();
    }
    this.groups.add(groupsItem);
    return this;
  }

  /**
   * Fulfillment groups for selecting options. Agent sets selected_option_id on groups to choose shipping method.
   * @return groups
   */
  @Valid 
  @Schema(name = "groups", description = "Fulfillment groups for selecting options. Agent sets selected_option_id on groups to choose shipping method.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("groups")
  public List<FulfillmentGroupCreateRequest> getGroups() {
    return groups;
  }

  public void setGroups(List<FulfillmentGroupCreateRequest> groups) {
    this.groups = groups;
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
    public FulfillmentMethodCreateRequest putAdditionalProperty(String key, JsonNode value) {
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
    FulfillmentMethodCreateRequest fulfillmentMethodCreateRequest = (FulfillmentMethodCreateRequest) o;
    return Objects.equals(this.type, fulfillmentMethodCreateRequest.type) &&
        Objects.equals(this.lineItemIds, fulfillmentMethodCreateRequest.lineItemIds) &&
        Objects.equals(this.destinations, fulfillmentMethodCreateRequest.destinations) &&
        equalsNullable(this.selectedDestinationId, fulfillmentMethodCreateRequest.selectedDestinationId) &&
        Objects.equals(this.groups, fulfillmentMethodCreateRequest.groups) &&
    Objects.equals(this.additionalProperties, fulfillmentMethodCreateRequest.additionalProperties);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, lineItemIds, destinations, hashCodeNullable(selectedDestinationId), groups, additionalProperties);
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
    sb.append("class FulfillmentMethodCreateRequest {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    lineItemIds: ").append(toIndentedString(lineItemIds)).append("\n");
    sb.append("    destinations: ").append(toIndentedString(destinations)).append("\n");
    sb.append("    selectedDestinationId: ").append(toIndentedString(selectedDestinationId)).append("\n");
    sb.append("    groups: ").append(toIndentedString(groups)).append("\n");
    
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

    private FulfillmentMethodCreateRequest instance;

    public Builder() {
      this(new FulfillmentMethodCreateRequest());
    }

    protected Builder(FulfillmentMethodCreateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentMethodCreateRequest value) { 
      this.instance.setType(value.type);
      this.instance.setLineItemIds(value.lineItemIds);
      this.instance.setDestinations(value.destinations);
      this.instance.setSelectedDestinationId(value.selectedDestinationId);
      this.instance.setGroups(value.groups);
      return this;
    }

    public FulfillmentMethodCreateRequest.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder lineItemIds(List<String> lineItemIds) {
      this.instance.lineItemIds(lineItemIds);
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder destinations(List<FulfillmentDestinationRequest> destinations) {
      this.instance.destinations(destinations);
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder selectedDestinationId(String selectedDestinationId) {
      this.instance.selectedDestinationId(selectedDestinationId);
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder selectedDestinationId(JsonNullable<String> selectedDestinationId) {
      this.instance.selectedDestinationId = selectedDestinationId;
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder groups(List<FulfillmentGroupCreateRequest> groups) {
      this.instance.groups(groups);
      return this;
    }
    
    public FulfillmentMethodCreateRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built FulfillmentMethodCreateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentMethodCreateRequest build() {
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
  public static FulfillmentMethodCreateRequest.Builder builder() {
    return new FulfillmentMethodCreateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentMethodCreateRequest.Builder toBuilder() {
    FulfillmentMethodCreateRequest.Builder builder = new FulfillmentMethodCreateRequest.Builder();
    return builder.copyOf(this);
  }

}

