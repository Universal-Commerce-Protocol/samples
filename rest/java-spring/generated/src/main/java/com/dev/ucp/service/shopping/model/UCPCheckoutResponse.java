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
import com.dev.ucp.service.shopping.model.CapabilityResponse;
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
 * UCP metadata for checkout responses.
 */

@Schema(name = "UCP_Checkout_Response", description = "UCP metadata for checkout responses.")
@JsonTypeName("UCP_Checkout_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class UCPCheckoutResponse {

  private String version;

  @Valid
  private List<CapabilityResponse> capabilities = new ArrayList<>();

  public UCPCheckoutResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public UCPCheckoutResponse(String version, List<CapabilityResponse> capabilities) {
    this.version = version;
    this.capabilities = capabilities;
  }

  public UCPCheckoutResponse version(String version) {
    this.version = version;
    return this;
  }

  /**
   * Handler version in YYYY-MM-DD format.
   * @return version
   */
  @NotNull @Pattern(regexp = "^\\d{4}-\\d{2}-\\d{2}$") 
  @Schema(name = "version", description = "Handler version in YYYY-MM-DD format.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("version")
  public String getVersion() {
    return version;
  }

  public void setVersion(String version) {
    this.version = version;
  }

  public UCPCheckoutResponse capabilities(List<CapabilityResponse> capabilities) {
    this.capabilities = capabilities;
    return this;
  }

  public UCPCheckoutResponse addCapabilitiesItem(CapabilityResponse capabilitiesItem) {
    if (this.capabilities == null) {
      this.capabilities = new ArrayList<>();
    }
    this.capabilities.add(capabilitiesItem);
    return this;
  }

  /**
   * Active capabilities for this response.
   * @return capabilities
   */
  @NotNull @Valid 
  @Schema(name = "capabilities", description = "Active capabilities for this response.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("capabilities")
  public List<CapabilityResponse> getCapabilities() {
    return capabilities;
  }

  public void setCapabilities(List<CapabilityResponse> capabilities) {
    this.capabilities = capabilities;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    UCPCheckoutResponse ucPCheckoutResponse = (UCPCheckoutResponse) o;
    return Objects.equals(this.version, ucPCheckoutResponse.version) &&
        Objects.equals(this.capabilities, ucPCheckoutResponse.capabilities);
  }

  @Override
  public int hashCode() {
    return Objects.hash(version, capabilities);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class UCPCheckoutResponse {\n");
    sb.append("    version: ").append(toIndentedString(version)).append("\n");
    sb.append("    capabilities: ").append(toIndentedString(capabilities)).append("\n");
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

    private UCPCheckoutResponse instance;

    public Builder() {
      this(new UCPCheckoutResponse());
    }

    protected Builder(UCPCheckoutResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(UCPCheckoutResponse value) { 
      this.instance.setVersion(value.version);
      this.instance.setCapabilities(value.capabilities);
      return this;
    }

    public UCPCheckoutResponse.Builder version(String version) {
      this.instance.version(version);
      return this;
    }
    
    public UCPCheckoutResponse.Builder capabilities(List<CapabilityResponse> capabilities) {
      this.instance.capabilities(capabilities);
      return this;
    }
    
    /**
    * returns a built UCPCheckoutResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public UCPCheckoutResponse build() {
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
  public static UCPCheckoutResponse.Builder builder() {
    return new UCPCheckoutResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public UCPCheckoutResponse.Builder toBuilder() {
    UCPCheckoutResponse.Builder builder = new UCPCheckoutResponse.Builder();
    return builder.copyOf(this);
  }

}

