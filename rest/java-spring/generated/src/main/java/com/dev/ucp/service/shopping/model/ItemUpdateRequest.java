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
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * ItemUpdateRequest
 */

@JsonTypeName("Item_Update_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class ItemUpdateRequest {

  private String id;

  public ItemUpdateRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public ItemUpdateRequest(String id) {
    this.id = id;
  }

  public ItemUpdateRequest id(String id) {
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

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    ItemUpdateRequest itemUpdateRequest = (ItemUpdateRequest) o;
    return Objects.equals(this.id, itemUpdateRequest.id);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class ItemUpdateRequest {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
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

    private ItemUpdateRequest instance;

    public Builder() {
      this(new ItemUpdateRequest());
    }

    protected Builder(ItemUpdateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(ItemUpdateRequest value) { 
      this.instance.setId(value.id);
      return this;
    }

    public ItemUpdateRequest.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    /**
    * returns a built ItemUpdateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public ItemUpdateRequest build() {
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
  public static ItemUpdateRequest.Builder builder() {
    return new ItemUpdateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public ItemUpdateRequest.Builder toBuilder() {
    ItemUpdateRequest.Builder builder = new ItemUpdateRequest.Builder();
    return builder.copyOf(this);
  }

}

