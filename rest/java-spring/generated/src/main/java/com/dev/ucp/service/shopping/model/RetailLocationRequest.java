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
import com.dev.ucp.service.shopping.model.PostalAddress;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.databind.JsonNode;
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
 * A pickup location (retail store, locker, etc.).
 */

@Schema(name = "Retail_Location_Request", description = "A pickup location (retail store, locker, etc.).")
@JsonTypeName("Retail_Location_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class RetailLocationRequest implements FulfillmentDestinationRequest {

  private String name;

  private @Nullable PostalAddress address;

  public RetailLocationRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public RetailLocationRequest(String name) {
    this.name = name;
  }

  public RetailLocationRequest name(String name) {
    this.name = name;
    return this;
  }

  /**
   * Location name (e.g., store name).
   * @return name
   */
  @NotNull 
  @Schema(name = "name", description = "Location name (e.g., store name).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("name")
  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RetailLocationRequest address(@Nullable PostalAddress address) {
    this.address = address;
    return this;
  }

  /**
   * Get address
   * @return address
   */
  @Valid 
  @Schema(name = "address", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("address")
  public @Nullable PostalAddress getAddress() {
    return address;
  }

  public void setAddress(@Nullable PostalAddress address) {
    this.address = address;
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
    public RetailLocationRequest putAdditionalProperty(String key, JsonNode value) {
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
    RetailLocationRequest retailLocationRequest = (RetailLocationRequest) o;
    return Objects.equals(this.name, retailLocationRequest.name) &&
        Objects.equals(this.address, retailLocationRequest.address) &&
    Objects.equals(this.additionalProperties, retailLocationRequest.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, address, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class RetailLocationRequest {\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    address: ").append(toIndentedString(address)).append("\n");
    
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

    private RetailLocationRequest instance;

    public Builder() {
      this(new RetailLocationRequest());
    }

    protected Builder(RetailLocationRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(RetailLocationRequest value) { 
      this.instance.setName(value.name);
      this.instance.setAddress(value.address);
      return this;
    }

    public RetailLocationRequest.Builder name(String name) {
      this.instance.name(name);
      return this;
    }
    
    public RetailLocationRequest.Builder address(PostalAddress address) {
      this.instance.address(address);
      return this;
    }
    
    public RetailLocationRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built RetailLocationRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public RetailLocationRequest build() {
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
  public static RetailLocationRequest.Builder builder() {
    return new RetailLocationRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public RetailLocationRequest.Builder toBuilder() {
    RetailLocationRequest.Builder builder = new RetailLocationRequest.Builder();
    return builder.copyOf(this);
  }

}

