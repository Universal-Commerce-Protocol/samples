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
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.lang.Nullable;
import com.fasterxml.jackson.annotation.JsonValue;
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
 * Base token credential schema. Concrete payment handlers may extend this schema with additional fields and define their own constraints.
 */

@Schema(name = "Token_Credential_Response", description = "Base token credential schema. Concrete payment handlers may extend this schema with additional fields and define their own constraints.")
@JsonTypeName("Token_Credential_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class TokenCredentialResponse implements PaymentCredential {

  private String type;

  public TokenCredentialResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public TokenCredentialResponse(String type) {
    this.type = type;
  }

  public TokenCredentialResponse type(String type) {
    this.type = type;
    return this;
  }

  /**
   * The specific type of token produced by the handler (e.g., 'stripe_token').
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "The specific type of token produced by the handler (e.g., 'stripe_token').", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
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
    public TokenCredentialResponse putAdditionalProperty(String key, JsonNode value) {
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
    TokenCredentialResponse tokenCredentialResponse = (TokenCredentialResponse) o;
    return Objects.equals(this.type, tokenCredentialResponse.type) &&
    Objects.equals(this.additionalProperties, tokenCredentialResponse.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TokenCredentialResponse {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    
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

    private TokenCredentialResponse instance;

    public Builder() {
      this(new TokenCredentialResponse());
    }

    protected Builder(TokenCredentialResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(TokenCredentialResponse value) { 
      this.instance.setType(value.type);
      return this;
    }

    public TokenCredentialResponse.Builder type(String type) {
      this.instance.type(type);
      return this;
    }
    
    public TokenCredentialResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built TokenCredentialResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public TokenCredentialResponse build() {
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
  public static TokenCredentialResponse.Builder builder() {
    return new TokenCredentialResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public TokenCredentialResponse.Builder toBuilder() {
    TokenCredentialResponse.Builder builder = new TokenCredentialResponse.Builder();
    return builder.copyOf(this);
  }

}

