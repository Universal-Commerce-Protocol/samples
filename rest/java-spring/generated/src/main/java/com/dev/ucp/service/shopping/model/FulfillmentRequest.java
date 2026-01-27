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
import com.dev.ucp.service.shopping.model.FulfillmentMethodCreateRequest;
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

@Schema(name = "fulfillment_request", description = "Container for fulfillment methods and availability.")
@JsonTypeName("fulfillment_request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentRequest {

  @Valid
  private List<FulfillmentMethodCreateRequest> methods = new ArrayList<>();

  public FulfillmentRequest methods(List<FulfillmentMethodCreateRequest> methods) {
    this.methods = methods;
    return this;
  }

  public FulfillmentRequest addMethodsItem(FulfillmentMethodCreateRequest methodsItem) {
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
  public List<FulfillmentMethodCreateRequest> getMethods() {
    return methods;
  }

  public void setMethods(List<FulfillmentMethodCreateRequest> methods) {
    this.methods = methods;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FulfillmentRequest fulfillmentRequest = (FulfillmentRequest) o;
    return Objects.equals(this.methods, fulfillmentRequest.methods);
  }

  @Override
  public int hashCode() {
    return Objects.hash(methods);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentRequest {\n");
    sb.append("    methods: ").append(toIndentedString(methods)).append("\n");
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

    private FulfillmentRequest instance;

    public Builder() {
      this(new FulfillmentRequest());
    }

    protected Builder(FulfillmentRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentRequest value) { 
      this.instance.setMethods(value.methods);
      return this;
    }

    public FulfillmentRequest.Builder methods(List<FulfillmentMethodCreateRequest> methods) {
      this.instance.methods(methods);
      return this;
    }
    
    /**
    * returns a built FulfillmentRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentRequest build() {
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
  public static FulfillmentRequest.Builder builder() {
    return new FulfillmentRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentRequest.Builder toBuilder() {
    FulfillmentRequest.Builder builder = new FulfillmentRequest.Builder();
    return builder.copyOf(this);
  }

}

