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
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * OrderEventWebhook200Response
 */

@JsonTypeName("order_event_webhook_200_response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderEventWebhook200Response {

  private JsonNullable<JsonNode> ucp = JsonNullable.<JsonNode>undefined();

  public OrderEventWebhook200Response() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public OrderEventWebhook200Response(JsonNode ucp) {
    this.ucp = JsonNullable.of(ucp);
  }

  public OrderEventWebhook200Response ucp(JsonNode ucp) {
    this.ucp = JsonNullable.of(ucp);
    return this;
  }

  /**
   * Protocol metadata for discovery profiles and responses. Uses slim schema pattern with context-specific required fields.
   * @return ucp
   */
  @NotNull @Valid 
  @Schema(name = "ucp", description = "Protocol metadata for discovery profiles and responses. Uses slim schema pattern with context-specific required fields.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("ucp")
  public JsonNullable<JsonNode> getUcp() {
    return ucp;
  }

  public void setUcp(JsonNullable<JsonNode> ucp) {
    this.ucp = ucp;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OrderEventWebhook200Response orderEventWebhook200Response = (OrderEventWebhook200Response) o;
    return Objects.equals(this.ucp, orderEventWebhook200Response.ucp);
  }

  @Override
  public int hashCode() {
    return Objects.hash(ucp);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderEventWebhook200Response {\n");
    sb.append("    ucp: ").append(toIndentedString(ucp)).append("\n");
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

    private OrderEventWebhook200Response instance;

    public Builder() {
      this(new OrderEventWebhook200Response());
    }

    protected Builder(OrderEventWebhook200Response instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderEventWebhook200Response value) { 
      this.instance.setUcp(value.ucp);
      return this;
    }

    public OrderEventWebhook200Response.Builder ucp(JsonNode ucp) {
      this.instance.ucp(ucp);
      return this;
    }
    
    public OrderEventWebhook200Response.Builder ucp(JsonNullable<JsonNode> ucp) {
      this.instance.ucp = ucp;
      return this;
    }
    
    /**
    * returns a built OrderEventWebhook200Response instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderEventWebhook200Response build() {
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
  public static OrderEventWebhook200Response.Builder builder() {
    return new OrderEventWebhook200Response.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderEventWebhook200Response.Builder toBuilder() {
    OrderEventWebhook200Response.Builder builder = new OrderEventWebhook200Response.Builder();
    return builder.copyOf(this);
  }

}

