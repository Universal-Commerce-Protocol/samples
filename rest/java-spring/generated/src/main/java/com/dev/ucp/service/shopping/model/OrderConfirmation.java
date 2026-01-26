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
import java.net.URI;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * Details about an order created for this checkout session.
 */

@Schema(name = "Order_Confirmation", description = "Details about an order created for this checkout session.")
@JsonTypeName("Order_Confirmation")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderConfirmation {

  private String id;

  private URI permalinkUrl;

  public OrderConfirmation() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public OrderConfirmation(String id, URI permalinkUrl) {
    this.id = id;
    this.permalinkUrl = permalinkUrl;
  }

  public OrderConfirmation id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Unique order identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Unique order identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public OrderConfirmation permalinkUrl(URI permalinkUrl) {
    this.permalinkUrl = permalinkUrl;
    return this;
  }

  /**
   * Permalink to access the order on merchant site.
   * @return permalinkUrl
   */
  @NotNull @Valid 
  @Schema(name = "permalink_url", description = "Permalink to access the order on merchant site.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("permalink_url")
  public URI getPermalinkUrl() {
    return permalinkUrl;
  }

  public void setPermalinkUrl(URI permalinkUrl) {
    this.permalinkUrl = permalinkUrl;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OrderConfirmation orderConfirmation = (OrderConfirmation) o;
    return Objects.equals(this.id, orderConfirmation.id) &&
        Objects.equals(this.permalinkUrl, orderConfirmation.permalinkUrl);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, permalinkUrl);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderConfirmation {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    permalinkUrl: ").append(toIndentedString(permalinkUrl)).append("\n");
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

    private OrderConfirmation instance;

    public Builder() {
      this(new OrderConfirmation());
    }

    protected Builder(OrderConfirmation instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderConfirmation value) { 
      this.instance.setId(value.id);
      this.instance.setPermalinkUrl(value.permalinkUrl);
      return this;
    }

    public OrderConfirmation.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public OrderConfirmation.Builder permalinkUrl(URI permalinkUrl) {
      this.instance.permalinkUrl(permalinkUrl);
      return this;
    }
    
    /**
    * returns a built OrderConfirmation instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderConfirmation build() {
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
  public static OrderConfirmation.Builder builder() {
    return new OrderConfirmation.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderConfirmation.Builder toBuilder() {
    OrderConfirmation.Builder builder = new OrderConfirmation.Builder();
    return builder.copyOf(this);
  }

}

