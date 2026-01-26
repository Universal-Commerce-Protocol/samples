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
 * ItemResponse
 */

@JsonTypeName("Item_Response_1")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class ItemResponse {

  private String id;

  private String title;

  private Integer price;

  private @Nullable URI imageUrl;

  public ItemResponse() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public ItemResponse(String id, String title, Integer price) {
    this.id = id;
    this.title = title;
    this.price = price;
  }

  public ItemResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Should be recognized by both the Platform, and the Business. For Google it should match the id provided in the \"id\" field in the product feed.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Should be recognized by both the Platform, and the Business. For Google it should match the id provided in the \"id\" field in the product feed.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public ItemResponse title(String title) {
    this.title = title;
    return this;
  }

  /**
   * Product title.
   * @return title
   */
  @NotNull 
  @Schema(name = "title", description = "Product title.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("title")
  public String getTitle() {
    return title;
  }

  public void setTitle(String title) {
    this.title = title;
  }

  public ItemResponse price(Integer price) {
    this.price = price;
    return this;
  }

  /**
   * Unit price in minor (cents) currency units.
   * minimum: 0
   * @return price
   */
  @NotNull @Min(value = 0) 
  @Schema(name = "price", description = "Unit price in minor (cents) currency units.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("price")
  public Integer getPrice() {
    return price;
  }

  public void setPrice(Integer price) {
    this.price = price;
  }

  public ItemResponse imageUrl(@Nullable URI imageUrl) {
    this.imageUrl = imageUrl;
    return this;
  }

  /**
   * Product image URI.
   * @return imageUrl
   */
  @Valid 
  @Schema(name = "image_url", description = "Product image URI.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("image_url")
  public @Nullable URI getImageUrl() {
    return imageUrl;
  }

  public void setImageUrl(@Nullable URI imageUrl) {
    this.imageUrl = imageUrl;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    ItemResponse itemResponse1 = (ItemResponse) o;
    return Objects.equals(this.id, itemResponse1.id) &&
        Objects.equals(this.title, itemResponse1.title) &&
        Objects.equals(this.price, itemResponse1.price) &&
        Objects.equals(this.imageUrl, itemResponse1.imageUrl);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, title, price, imageUrl);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class ItemResponse {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    title: ").append(toIndentedString(title)).append("\n");
    sb.append("    price: ").append(toIndentedString(price)).append("\n");
    sb.append("    imageUrl: ").append(toIndentedString(imageUrl)).append("\n");
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

    private ItemResponse instance;

    public Builder() {
      this(new ItemResponse());
    }

    protected Builder(ItemResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(ItemResponse value) { 
      this.instance.setId(value.id);
      this.instance.setTitle(value.title);
      this.instance.setPrice(value.price);
      this.instance.setImageUrl(value.imageUrl);
      return this;
    }

    public ItemResponse.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public ItemResponse.Builder title(String title) {
      this.instance.title(title);
      return this;
    }
    
    public ItemResponse.Builder price(Integer price) {
      this.instance.price(price);
      return this;
    }
    
    public ItemResponse.Builder imageUrl(URI imageUrl) {
      this.instance.imageUrl(imageUrl);
      return this;
    }
    
    /**
    * returns a built ItemResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public ItemResponse build() {
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
  public static ItemResponse.Builder builder() {
    return new ItemResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public ItemResponse.Builder toBuilder() {
    ItemResponse.Builder builder = new ItemResponse.Builder();
    return builder.copyOf(this);
  }

}

