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
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * PaymentHandlerResponse
 */

@JsonTypeName("Payment_Handler_Response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class PaymentHandlerResponse {

  private String id;

  private String name;

  private String version;

  private URI spec;

  private URI configSchema;

  @Valid
  private List<URI> instrumentSchemas = new ArrayList<>();

  @Valid
  private Map<String, JsonNode> config = new HashMap<>();

  public PaymentHandlerResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public PaymentHandlerResponse(String id, String name, String version, URI spec, URI configSchema, List<URI> instrumentSchemas, Map<String, JsonNode> config) {
    this.id = id;
    this.name = name;
    this.version = version;
    this.spec = spec;
    this.configSchema = configSchema;
    this.instrumentSchemas = instrumentSchemas;
    this.config = config;
  }

  public PaymentHandlerResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * The unique identifier for this handler instance within the payment.handlers. Used by payment instruments to reference which handler produced them.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "The unique identifier for this handler instance within the payment.handlers. Used by payment instruments to reference which handler produced them.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public PaymentHandlerResponse name(String name) {
    this.name = name;
    return this;
  }

  /**
   * The specification name using reverse-DNS format. For example, dev.ucp.delegate_payment.
   * @return name
   */
  @NotNull 
  @Schema(name = "name", description = "The specification name using reverse-DNS format. For example, dev.ucp.delegate_payment.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("name")
  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public PaymentHandlerResponse version(String version) {
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

  public PaymentHandlerResponse spec(URI spec) {
    this.spec = spec;
    return this;
  }

  /**
   * A URI pointing to the technical specification or schema that defines how this handler operates.
   * @return spec
   */
  @NotNull @Valid 
  @Schema(name = "spec", description = "A URI pointing to the technical specification or schema that defines how this handler operates.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("spec")
  public URI getSpec() {
    return spec;
  }

  public void setSpec(URI spec) {
    this.spec = spec;
  }

  public PaymentHandlerResponse configSchema(URI configSchema) {
    this.configSchema = configSchema;
    return this;
  }

  /**
   * A URI pointing to a JSON Schema used to validate the structure of the config object.
   * @return configSchema
   */
  @NotNull @Valid 
  @Schema(name = "config_schema", description = "A URI pointing to a JSON Schema used to validate the structure of the config object.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("config_schema")
  public URI getConfigSchema() {
    return configSchema;
  }

  public void setConfigSchema(URI configSchema) {
    this.configSchema = configSchema;
  }

  public PaymentHandlerResponse instrumentSchemas(List<URI> instrumentSchemas) {
    this.instrumentSchemas = instrumentSchemas;
    return this;
  }

  public PaymentHandlerResponse addInstrumentSchemasItem(URI instrumentSchemasItem) {
    if (this.instrumentSchemas == null) {
      this.instrumentSchemas = new ArrayList<>();
    }
    this.instrumentSchemas.add(instrumentSchemasItem);
    return this;
  }

  /**
   * Get instrumentSchemas
   * @return instrumentSchemas
   */
  @NotNull @Valid 
  @Schema(name = "instrument_schemas", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("instrument_schemas")
  public List<URI> getInstrumentSchemas() {
    return instrumentSchemas;
  }

  public void setInstrumentSchemas(List<URI> instrumentSchemas) {
    this.instrumentSchemas = instrumentSchemas;
  }

  public PaymentHandlerResponse config(Map<String, JsonNode> config) {
    this.config = config;
    return this;
  }

  public PaymentHandlerResponse putConfigItem(String key, JsonNode configItem) {
    if (this.config == null) {
      this.config = new HashMap<>();
    }
    this.config.put(key, configItem);
    return this;
  }

  /**
   * A dictionary containing provider-specific configuration details, such as merchant IDs, supported networks, or gateway credentials.
   * @return config
   */
  @NotNull @Valid 
  @Schema(name = "config", description = "A dictionary containing provider-specific configuration details, such as merchant IDs, supported networks, or gateway credentials.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("config")
  public Map<String, JsonNode> getConfig() {
    return config;
  }

  public void setConfig(Map<String, JsonNode> config) {
    this.config = config;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PaymentHandlerResponse paymentHandlerResponse = (PaymentHandlerResponse) o;
    return Objects.equals(this.id, paymentHandlerResponse.id) &&
        Objects.equals(this.name, paymentHandlerResponse.name) &&
        Objects.equals(this.version, paymentHandlerResponse.version) &&
        Objects.equals(this.spec, paymentHandlerResponse.spec) &&
        Objects.equals(this.configSchema, paymentHandlerResponse.configSchema) &&
        Objects.equals(this.instrumentSchemas, paymentHandlerResponse.instrumentSchemas) &&
        Objects.equals(this.config, paymentHandlerResponse.config);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, name, version, spec, configSchema, instrumentSchemas, config);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class PaymentHandlerResponse {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    version: ").append(toIndentedString(version)).append("\n");
    sb.append("    spec: ").append(toIndentedString(spec)).append("\n");
    sb.append("    configSchema: ").append(toIndentedString(configSchema)).append("\n");
    sb.append("    instrumentSchemas: ").append(toIndentedString(instrumentSchemas)).append("\n");
    sb.append("    config: ").append(toIndentedString(config)).append("\n");
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

    private PaymentHandlerResponse instance;

    public Builder() {
      this(new PaymentHandlerResponse());
    }

    protected Builder(PaymentHandlerResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(PaymentHandlerResponse value) { 
      this.instance.setId(value.id);
      this.instance.setName(value.name);
      this.instance.setVersion(value.version);
      this.instance.setSpec(value.spec);
      this.instance.setConfigSchema(value.configSchema);
      this.instance.setInstrumentSchemas(value.instrumentSchemas);
      this.instance.setConfig(value.config);
      return this;
    }

    public PaymentHandlerResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public PaymentHandlerResponse.Builder name(String name) {
      this.instance.name(name);
      return this;
    }
    
    public PaymentHandlerResponse.Builder version(String version) {
      this.instance.version(version);
      return this;
    }
    
    public PaymentHandlerResponse.Builder spec(URI spec) {
      this.instance.spec(spec);
      return this;
    }
    
    public PaymentHandlerResponse.Builder configSchema(URI configSchema) {
      this.instance.configSchema(configSchema);
      return this;
    }
    
    public PaymentHandlerResponse.Builder instrumentSchemas(List<URI> instrumentSchemas) {
      this.instance.instrumentSchemas(instrumentSchemas);
      return this;
    }
    
    public PaymentHandlerResponse.Builder config(Map<String, JsonNode> config) {
      this.instance.config(config);
      return this;
    }
    
    /**
    * returns a built PaymentHandlerResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public PaymentHandlerResponse build() {
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
  public static PaymentHandlerResponse.Builder builder() {
    return new PaymentHandlerResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public PaymentHandlerResponse.Builder toBuilder() {
    PaymentHandlerResponse.Builder builder = new PaymentHandlerResponse.Builder();
    return builder.copyOf(this);
  }

}

