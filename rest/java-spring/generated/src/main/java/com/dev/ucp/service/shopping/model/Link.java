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
 * Link
 */

@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class Link {

  private String type;

  private URI url;

  private @Nullable String title;

  public Link() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public Link(String type, URI url) {
    this.type = type;
    this.url = url;
  }

  public Link type(String type) {
    this.type = type;
    return this;
  }

  /**
   * Type of link. Well-known values: `privacy_policy`, `terms_of_service`, `refund_policy`, `shipping_policy`, `faq`. Consumers SHOULD handle unknown values gracefully by displaying them using the `title` field or omitting the link.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Type of link. Well-known values: `privacy_policy`, `terms_of_service`, `refund_policy`, `shipping_policy`, `faq`. Consumers SHOULD handle unknown values gracefully by displaying them using the `title` field or omitting the link.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public Link url(URI url) {
    this.url = url;
    return this;
  }

  /**
   * The actual URL pointing to the content to be displayed.
   * @return url
   */
  @NotNull @Valid 
  @Schema(name = "url", description = "The actual URL pointing to the content to be displayed.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("url")
  public URI getUrl() {
    return url;
  }

  public void setUrl(URI url) {
    this.url = url;
  }

  public Link title(@Nullable String title) {
    this.title = title;
    return this;
  }

  /**
   * Optional display text for the link. When provided, use this instead of generating from type.
   * @return title
   */
  
  @Schema(name = "title", description = "Optional display text for the link. When provided, use this instead of generating from type.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("title")
  public @Nullable String getTitle() {
    return title;
  }

  public void setTitle(@Nullable String title) {
    this.title = title;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    Link link = (Link) o;
    return Objects.equals(this.type, link.type) &&
        Objects.equals(this.url, link.url) &&
        Objects.equals(this.title, link.title);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, url, title);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Link {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
    sb.append("    title: ").append(toIndentedString(title)).append("\n");
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

    private Link instance;

    public Builder() {
      this(new Link());
    }

    protected Builder(Link instance) {
      this.instance = instance;
    }

    protected Builder copyOf(Link value) { 
      this.instance.setType(value.type);
      this.instance.setUrl(value.url);
      this.instance.setTitle(value.title);
      return this;
    }

    public Link.Builder type(String type) {
      this.instance.type(type);
      return this;
    }
    
    public Link.Builder url(URI url) {
      this.instance.url(url);
      return this;
    }
    
    public Link.Builder title(String title) {
      this.instance.title(title);
      return this;
    }
    
    /**
    * returns a built Link instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public Link build() {
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
  public static Link.Builder builder() {
    return new Link.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public Link.Builder toBuilder() {
    Link.Builder builder = new Link.Builder();
    return builder.copyOf(this);
  }

}

