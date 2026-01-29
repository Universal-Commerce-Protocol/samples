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
import java.net.URI;
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
 * Capability reference in responses. Only name/version required to confirm active capabilities.
 */

@Schema(name = "Capability__Response_", description = "Capability reference in responses. Only name/version required to confirm active capabilities.")
@JsonTypeName("Capability__Response_")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CapabilityResponse {

  private @Nullable String name;

  private @Nullable String version;

  private @Nullable URI spec;

  private @Nullable URI schema;

  private @Nullable String _extends;

  private @Nullable JsonNode config;

  public CapabilityResponse name(@Nullable String name) {
    this.name = name;
    return this;
  }

  /**
   * Stable capability identifier in reverse-domain notation (e.g., dev.ucp.shopping.checkout). Used in capability negotiation.
   * @return name
   */
  @Pattern(regexp = "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9_]*)+$") 
  @Schema(name = "name", description = "Stable capability identifier in reverse-domain notation (e.g., dev.ucp.shopping.checkout). Used in capability negotiation.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("name")
  public @Nullable String getName() {
    return name;
  }

  public void setName(@Nullable String name) {
    this.name = name;
  }

  public CapabilityResponse version(@Nullable String version) {
    this.version = version;
    return this;
  }

  /**
   * Capability version in YYYY-MM-DD format.
   * @return version
   */
  @Pattern(regexp = "^\\d{4}-\\d{2}-\\d{2}$") 
  @Schema(name = "version", description = "Capability version in YYYY-MM-DD format.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("version")
  public @Nullable String getVersion() {
    return version;
  }

  public void setVersion(@Nullable String version) {
    this.version = version;
  }

  public CapabilityResponse spec(@Nullable URI spec) {
    this.spec = spec;
    return this;
  }

  /**
   * URL to human-readable specification document.
   * @return spec
   */
  @Valid 
  @Schema(name = "spec", description = "URL to human-readable specification document.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("spec")
  public @Nullable URI getSpec() {
    return spec;
  }

  public void setSpec(@Nullable URI spec) {
    this.spec = spec;
  }

  public CapabilityResponse schema(@Nullable URI schema) {
    this.schema = schema;
    return this;
  }

  /**
   * URL to JSON Schema for this capability's payload.
   * @return schema
   */
  @Valid 
  @Schema(name = "schema", description = "URL to JSON Schema for this capability's payload.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("schema")
  public @Nullable URI getSchema() {
    return schema;
  }

  public void setSchema(@Nullable URI schema) {
    this.schema = schema;
  }

  public CapabilityResponse _extends(@Nullable String _extends) {
    this._extends = _extends;
    return this;
  }

  /**
   * Parent capability this extends. Present for extensions, absent for root capabilities.
   * @return _extends
   */
  @Pattern(regexp = "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9_]*)+$") 
  @Schema(name = "extends", description = "Parent capability this extends. Present for extensions, absent for root capabilities.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("extends")
  public @Nullable String getExtends() {
    return _extends;
  }

  public void setExtends(@Nullable String _extends) {
    this._extends = _extends;
  }

  public CapabilityResponse config(@Nullable JsonNode config) {
    this.config = config;
    return this;
  }

  /**
   * Capability-specific configuration (structure defined by each capability).
   * @return config
   */
  @Valid 
  @Schema(name = "config", description = "Capability-specific configuration (structure defined by each capability).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("config")
  public @Nullable JsonNode getConfig() {
    return config;
  }

  public void setConfig(@Nullable JsonNode config) {
    this.config = config;
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
    public CapabilityResponse putAdditionalProperty(String key, JsonNode value) {
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
    CapabilityResponse capabilityResponse = (CapabilityResponse) o;
    return Objects.equals(this.name, capabilityResponse.name) &&
        Objects.equals(this.version, capabilityResponse.version) &&
        Objects.equals(this.spec, capabilityResponse.spec) &&
        Objects.equals(this.schema, capabilityResponse.schema) &&
        Objects.equals(this._extends, capabilityResponse._extends) &&
        Objects.equals(this.config, capabilityResponse.config) &&
    Objects.equals(this.additionalProperties, capabilityResponse.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, version, spec, schema, _extends, config, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CapabilityResponse {\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    version: ").append(toIndentedString(version)).append("\n");
    sb.append("    spec: ").append(toIndentedString(spec)).append("\n");
    sb.append("    schema: ").append(toIndentedString(schema)).append("\n");
    sb.append("    _extends: ").append(toIndentedString(_extends)).append("\n");
    sb.append("    config: ").append(toIndentedString(config)).append("\n");
    
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

    private CapabilityResponse instance;

    public Builder() {
      this(new CapabilityResponse());
    }

    protected Builder(CapabilityResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CapabilityResponse value) { 
      this.instance.setName(value.name);
      this.instance.setVersion(value.version);
      this.instance.setSpec(value.spec);
      this.instance.setSchema(value.schema);
      this.instance.setExtends(value._extends);
      this.instance.setConfig(value.config);
      return this;
    }

    public CapabilityResponse.Builder name(String name) {
      this.instance.name(name);
      return this;
    }
    
    public CapabilityResponse.Builder version(String version) {
      this.instance.version(version);
      return this;
    }
    
    public CapabilityResponse.Builder spec(URI spec) {
      this.instance.spec(spec);
      return this;
    }
    
    public CapabilityResponse.Builder schema(URI schema) {
      this.instance.schema(schema);
      return this;
    }
    
    public CapabilityResponse.Builder _extends(String _extends) {
      this.instance._extends(_extends);
      return this;
    }
    
    public CapabilityResponse.Builder config(JsonNode config) {
      this.instance.config(config);
      return this;
    }
    
    public CapabilityResponse.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built CapabilityResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CapabilityResponse build() {
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
  public static CapabilityResponse.Builder builder() {
    return new CapabilityResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CapabilityResponse.Builder toBuilder() {
    CapabilityResponse.Builder builder = new CapabilityResponse.Builder();
    return builder.copyOf(this);
  }

}

