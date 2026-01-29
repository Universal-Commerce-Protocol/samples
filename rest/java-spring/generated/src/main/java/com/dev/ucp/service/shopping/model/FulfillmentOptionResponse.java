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
import com.dev.ucp.service.shopping.model.TotalResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.databind.JsonNode;
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

import java.util.Map;
import java.util.HashMap;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
/**
 * A fulfillment option within a group (e.g., Standard Shipping $5, Express $15).
 */

@Schema(name = "Fulfillment_Option_Response", description = "A fulfillment option within a group (e.g., Standard Shipping $5, Express $15).")
@JsonTypeName("Fulfillment_Option_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentOptionResponse {

  private String id;

  private String title;

  private @Nullable String description;

  private @Nullable String carrier;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private @Nullable OffsetDateTime earliestFulfillmentTime;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private @Nullable OffsetDateTime latestFulfillmentTime;

  @Valid
  private List<@Valid TotalResponse> totals = new ArrayList<>();

  public FulfillmentOptionResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentOptionResponse(String id, String title, List<@Valid TotalResponse> totals) {
    this.id = id;
    this.title = title;
    this.totals = totals;
  }

  public FulfillmentOptionResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Unique fulfillment option identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Unique fulfillment option identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public FulfillmentOptionResponse title(String title) {
    this.title = title;
    return this;
  }

  /**
   * Short label (e.g., 'Express Shipping', 'Curbside Pickup').
   * @return title
   */
  @NotNull 
  @Schema(name = "title", description = "Short label (e.g., 'Express Shipping', 'Curbside Pickup').", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("title")
  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public FulfillmentOptionResponse description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Complete context for buyer decision (e.g., 'Arrives Dec 12-15 via FedEx').
   * @return description
   */
  
  @Schema(name = "description", description = "Complete context for buyer decision (e.g., 'Arrives Dec 12-15 via FedEx').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  public void setDescription(@Nullable String description) {
    this.description = description;
  }

  public FulfillmentOptionResponse carrier(@Nullable String carrier) {
    this.carrier = carrier;
    return this;
  }

  /**
   * Carrier name (for shipping).
   * @return carrier
   */
  
  @Schema(name = "carrier", description = "Carrier name (for shipping).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("carrier")
  public @Nullable String getCarrier() {
    return carrier;
  }

  public void setCarrier(@Nullable String carrier) {
    this.carrier = carrier;
  }

  public FulfillmentOptionResponse earliestFulfillmentTime(@Nullable OffsetDateTime earliestFulfillmentTime) {
    this.earliestFulfillmentTime = earliestFulfillmentTime;
    return this;
  }

  /**
   * Earliest fulfillment date.
   * @return earliestFulfillmentTime
   */
  @Valid 
  @Schema(name = "earliest_fulfillment_time", description = "Earliest fulfillment date.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("earliest_fulfillment_time")
  public @Nullable OffsetDateTime getEarliestFulfillmentTime() {
    return earliestFulfillmentTime;
  }

  public void setEarliestFulfillmentTime(@Nullable OffsetDateTime earliestFulfillmentTime) {
    this.earliestFulfillmentTime = earliestFulfillmentTime;
  }

  public FulfillmentOptionResponse latestFulfillmentTime(@Nullable OffsetDateTime latestFulfillmentTime) {
    this.latestFulfillmentTime = latestFulfillmentTime;
    return this;
  }

  /**
   * Latest fulfillment date.
   * @return latestFulfillmentTime
   */
  @Valid 
  @Schema(name = "latest_fulfillment_time", description = "Latest fulfillment date.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("latest_fulfillment_time")
  public @Nullable OffsetDateTime getLatestFulfillmentTime() {
    return latestFulfillmentTime;
  }

  public void setLatestFulfillmentTime(@Nullable OffsetDateTime latestFulfillmentTime) {
    this.latestFulfillmentTime = latestFulfillmentTime;
  }

  public FulfillmentOptionResponse totals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
    return this;
  }

  public FulfillmentOptionResponse addTotalsItem(TotalResponse totalsItem) {
    if (this.totals == null) {
      this.totals = new ArrayList<>();
    }
    this.totals.add(totalsItem);
    return this;
  }

  /**
   * Fulfillment option totals breakdown.
   * @return totals
   */
  @NotNull @Valid 
  @Schema(name = "totals", description = "Fulfillment option totals breakdown.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("totals")
  public List<@Valid TotalResponse> getTotals() {
    return totals;
  }

  public void setTotals(List<@Valid TotalResponse> totals) {
    this.totals = totals;
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
    public FulfillmentOptionResponse putAdditionalProperty(String key, JsonNode value) {
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
    FulfillmentOptionResponse fulfillmentOptionResponse = (FulfillmentOptionResponse) o;
    return Objects.equals(this.id, fulfillmentOptionResponse.id) &&
        Objects.equals(this.title, fulfillmentOptionResponse.title) &&
        Objects.equals(this.description, fulfillmentOptionResponse.description) &&
        Objects.equals(this.carrier, fulfillmentOptionResponse.carrier) &&
        Objects.equals(this.earliestFulfillmentTime, fulfillmentOptionResponse.earliestFulfillmentTime) &&
        Objects.equals(this.latestFulfillmentTime, fulfillmentOptionResponse.latestFulfillmentTime) &&
        Objects.equals(this.totals, fulfillmentOptionResponse.totals) &&
    Objects.equals(this.additionalProperties, fulfillmentOptionResponse.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, title, description, carrier, earliestFulfillmentTime, latestFulfillmentTime, totals, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentOptionResponse {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    title: ").append(toIndentedString(title)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    carrier: ").append(toIndentedString(carrier)).append("\n");
    sb.append("    earliestFulfillmentTime: ").append(toIndentedString(earliestFulfillmentTime)).append("\n");
    sb.append("    latestFulfillmentTime: ").append(toIndentedString(latestFulfillmentTime)).append("\n");
    sb.append("    totals: ").append(toIndentedString(totals)).append("\n");
    
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

    private FulfillmentOptionResponse instance;

    public Builder() {
      this(new FulfillmentOptionResponse());
    }

    protected Builder(FulfillmentOptionResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentOptionResponse value) { 
      this.instance.setId(value.id);
      this.instance.setTitle(value.title);
      this.instance.setDescription(value.description);
      this.instance.setCarrier(value.carrier);
      this.instance.setEarliestFulfillmentTime(value.earliestFulfillmentTime);
      this.instance.setLatestFulfillmentTime(value.latestFulfillmentTime);
      this.instance.setTotals(value.totals);
      return this;
    }

    public FulfillmentOptionResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder title(String title) {
      this.instance.title(title);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder description(String description) {
      this.instance.description(description);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder carrier(String carrier) {
      this.instance.carrier(carrier);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder earliestFulfillmentTime(OffsetDateTime earliestFulfillmentTime) {
      this.instance.earliestFulfillmentTime(earliestFulfillmentTime);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder latestFulfillmentTime(OffsetDateTime latestFulfillmentTime) {
      this.instance.latestFulfillmentTime(latestFulfillmentTime);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder totals(List<TotalResponse> totals) {
      this.instance.totals(totals);
      return this;
    }
    
    public FulfillmentOptionResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built FulfillmentOptionResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentOptionResponse build() {
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
  public static FulfillmentOptionResponse.Builder builder() {
    return new FulfillmentOptionResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentOptionResponse.Builder toBuilder() {
    FulfillmentOptionResponse.Builder builder = new FulfillmentOptionResponse.Builder();
    return builder.copyOf(this);
  }

}

