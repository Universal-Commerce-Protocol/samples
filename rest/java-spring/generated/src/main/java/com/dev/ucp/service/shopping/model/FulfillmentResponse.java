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
import com.dev.ucp.service.shopping.model.FulfillmentAvailableMethodResponse;
import com.dev.ucp.service.shopping.model.FulfillmentMethodResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
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
 * Container for fulfillment methods and availability.
 */

@Schema(name = "fulfillment_response", description = "Container for fulfillment methods and availability.")
@JsonTypeName("fulfillment_response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentResponse {

  @Valid
  private List<FulfillmentMethodResponse> methods = new ArrayList<>();

  @Valid
  private List<FulfillmentAvailableMethodResponse> availableMethods = new ArrayList<>();

  public FulfillmentResponse methods(List<FulfillmentMethodResponse> methods) {
    this.methods = methods;
    return this;
  }

  public FulfillmentResponse addMethodsItem(FulfillmentMethodResponse methodsItem) {
    if (this.methods == null) {
      this.methods = new ArrayList<>();
    }
    this.methods.add(methodsItem);
    return this;
  }

  /**
   * Fulfillment methods for cart items.
   * @return methods
   */
  @Valid 
  @Schema(name = "methods", description = "Fulfillment methods for cart items.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("methods")
  public List<FulfillmentMethodResponse> getMethods() {
    return methods;
  }

  public void setMethods(List<FulfillmentMethodResponse> methods) {
    this.methods = methods;
  }

  public FulfillmentResponse availableMethods(List<FulfillmentAvailableMethodResponse> availableMethods) {
    this.availableMethods = availableMethods;
    return this;
  }

  public FulfillmentResponse addAvailableMethodsItem(FulfillmentAvailableMethodResponse availableMethodsItem) {
    if (this.availableMethods == null) {
      this.availableMethods = new ArrayList<>();
    }
    this.availableMethods.add(availableMethodsItem);
    return this;
  }

  /**
   * Inventory availability hints.
   * @return availableMethods
   */
  @Valid 
  @Schema(name = "available_methods", description = "Inventory availability hints.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("available_methods")
  public List<FulfillmentAvailableMethodResponse> getAvailableMethods() {
    return availableMethods;
  }

  public void setAvailableMethods(List<FulfillmentAvailableMethodResponse> availableMethods) {
    this.availableMethods = availableMethods;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FulfillmentResponse fulfillmentResponse = (FulfillmentResponse) o;
    return Objects.equals(this.methods, fulfillmentResponse.methods) &&
        Objects.equals(this.availableMethods, fulfillmentResponse.availableMethods);
  }

  @Override
  public int hashCode() {
    return Objects.hash(methods, availableMethods);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentResponse {\n");
    sb.append("    methods: ").append(toIndentedString(methods)).append("\n");
    sb.append("    availableMethods: ").append(toIndentedString(availableMethods)).append("\n");
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

    private FulfillmentResponse instance;

    public Builder() {
      this(new FulfillmentResponse());
    }

    protected Builder(FulfillmentResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentResponse value) { 
      this.instance.setMethods(value.methods);
      this.instance.setAvailableMethods(value.availableMethods);
      return this;
    }

    public FulfillmentResponse.Builder methods(List<FulfillmentMethodResponse> methods) {
      this.instance.methods(methods);
      return this;
    }
    
    public FulfillmentResponse.Builder availableMethods(List<FulfillmentAvailableMethodResponse> availableMethods) {
      this.instance.availableMethods(availableMethods);
      return this;
    }
    
    /**
    * returns a built FulfillmentResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentResponse build() {
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
  public static FulfillmentResponse.Builder builder() {
    return new FulfillmentResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentResponse.Builder toBuilder() {
    FulfillmentResponse.Builder builder = new FulfillmentResponse.Builder();
    return builder.copyOf(this);
  }

}

