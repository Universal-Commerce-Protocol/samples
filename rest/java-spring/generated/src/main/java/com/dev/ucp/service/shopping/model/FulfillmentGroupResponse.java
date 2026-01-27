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
import com.dev.ucp.service.shopping.model.FulfillmentOptionResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
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
 * A merchant-generated package/group of line items with fulfillment options.
 */

@Schema(name = "Fulfillment_Group_Response", description = "A merchant-generated package/group of line items with fulfillment options.")
@JsonTypeName("Fulfillment_Group_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentGroupResponse {

  private String id;

  @Valid
  private List<String> lineItemIds = new ArrayList<>();

  @Valid
  private List<FulfillmentOptionResponse> options = new ArrayList<>();

  private JsonNullable<String> selectedOptionId = JsonNullable.<String>undefined();

  public FulfillmentGroupResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentGroupResponse(String id, List<String> lineItemIds) {
    this.id = id;
    this.lineItemIds = lineItemIds;
  }

  public FulfillmentGroupResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Group identifier for referencing merchant-generated groups in updates.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Group identifier for referencing merchant-generated groups in updates.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public FulfillmentGroupResponse lineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
    return this;
  }

  public FulfillmentGroupResponse addLineItemIdsItem(String lineItemIdsItem) {
    if (this.lineItemIds == null) {
      this.lineItemIds = new ArrayList<>();
    }
    this.lineItemIds.add(lineItemIdsItem);
    return this;
  }

  /**
   * Line item IDs included in this group/package.
   * @return lineItemIds
   */
  @NotNull 
  @Schema(name = "line_item_ids", description = "Line item IDs included in this group/package.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_item_ids")
  public List<String> getLineItemIds() {
    return lineItemIds;
  }

  public void setLineItemIds(List<String> lineItemIds) {
    this.lineItemIds = lineItemIds;
  }

  public FulfillmentGroupResponse options(List<FulfillmentOptionResponse> options) {
    this.options = options;
    return this;
  }

  public FulfillmentGroupResponse addOptionsItem(FulfillmentOptionResponse optionsItem) {
    if (this.options == null) {
      this.options = new ArrayList<>();
    }
    this.options.add(optionsItem);
    return this;
  }

  /**
   * Available fulfillment options for this group.
   * @return options
   */
  @Valid 
  @Schema(name = "options", description = "Available fulfillment options for this group.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("options")
  public List<FulfillmentOptionResponse> getOptions() {
    return options;
  }

  public void setOptions(List<FulfillmentOptionResponse> options) {
    this.options = options;
  }

  public FulfillmentGroupResponse selectedOptionId(String selectedOptionId) {
    this.selectedOptionId = JsonNullable.of(selectedOptionId);
    return this;
  }

  /**
   * ID of the selected fulfillment option for this group.
   * @return selectedOptionId
   */
  
  @Schema(name = "selected_option_id", description = "ID of the selected fulfillment option for this group.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("selected_option_id")
  public JsonNullable<String> getSelectedOptionId() {
    return selectedOptionId;
  }

  public void setSelectedOptionId(JsonNullable<String> selectedOptionId) {
    this.selectedOptionId = selectedOptionId;
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
    public FulfillmentGroupResponse putAdditionalProperty(String key, JsonNode value) {
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
    FulfillmentGroupResponse fulfillmentGroupResponse = (FulfillmentGroupResponse) o;
    return Objects.equals(this.id, fulfillmentGroupResponse.id) &&
        Objects.equals(this.lineItemIds, fulfillmentGroupResponse.lineItemIds) &&
        Objects.equals(this.options, fulfillmentGroupResponse.options) &&
        equalsNullable(this.selectedOptionId, fulfillmentGroupResponse.selectedOptionId) &&
    Objects.equals(this.additionalProperties, fulfillmentGroupResponse.additionalProperties);
  }

  private static <T> boolean equalsNullable(JsonNullable<T> a, JsonNullable<T> b) {
    return a == b || (a != null && b != null && a.isPresent() && b.isPresent() && Objects.deepEquals(a.get(), b.get()));
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, lineItemIds, options, hashCodeNullable(selectedOptionId), additionalProperties);
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
    sb.append("class FulfillmentGroupResponse {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    lineItemIds: ").append(toIndentedString(lineItemIds)).append("\n");
    sb.append("    options: ").append(toIndentedString(options)).append("\n");
    sb.append("    selectedOptionId: ").append(toIndentedString(selectedOptionId)).append("\n");
    
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

    private FulfillmentGroupResponse instance;

    public Builder() {
      this(new FulfillmentGroupResponse());
    }

    protected Builder(FulfillmentGroupResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentGroupResponse value) { 
      this.instance.setId(value.id);
      this.instance.setLineItemIds(value.lineItemIds);
      this.instance.setOptions(value.options);
      this.instance.setSelectedOptionId(value.selectedOptionId);
      return this;
    }

    public FulfillmentGroupResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public FulfillmentGroupResponse.Builder lineItemIds(List<String> lineItemIds) {
      this.instance.lineItemIds(lineItemIds);
      return this;
    }
    
    public FulfillmentGroupResponse.Builder options(List<FulfillmentOptionResponse> options) {
      this.instance.options(options);
      return this;
    }
    
    public FulfillmentGroupResponse.Builder selectedOptionId(String selectedOptionId) {
      this.instance.selectedOptionId(selectedOptionId);
      return this;
    }
    
    public FulfillmentGroupResponse.Builder selectedOptionId(JsonNullable<String> selectedOptionId) {
      this.instance.selectedOptionId = selectedOptionId;
      return this;
    }
    
    public FulfillmentGroupResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built FulfillmentGroupResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentGroupResponse build() {
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
  public static FulfillmentGroupResponse.Builder builder() {
    return new FulfillmentGroupResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentGroupResponse.Builder toBuilder() {
    FulfillmentGroupResponse.Builder builder = new FulfillmentGroupResponse.Builder();
    return builder.copyOf(this);
  }

}

