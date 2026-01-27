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
import com.dev.ucp.service.shopping.model.DiscountRequestAppliedInner;
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
 * Discount codes input and applied discounts output.
 */

@Schema(name = "discount_response", description = "Discount codes input and applied discounts output.")
@JsonTypeName("discount_response")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class DiscountResponse {

  @Valid
  private List<String> codes = new ArrayList<>();

  @Valid
  private List<@Valid DiscountRequestAppliedInner> applied = new ArrayList<>();

  public DiscountResponse codes(List<String> codes) {
    this.codes = codes;
    return this;
  }

  public DiscountResponse addCodesItem(String codesItem) {
    if (this.codes == null) {
      this.codes = new ArrayList<>();
    }
    this.codes.add(codesItem);
    return this;
  }

  /**
   * Discount codes to apply. Case-insensitive. Replaces previously submitted codes. Send empty array to clear.
   * @return codes
   */
  
  @Schema(name = "codes", description = "Discount codes to apply. Case-insensitive. Replaces previously submitted codes. Send empty array to clear.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("codes")
  public List<String> getCodes() {
    return codes;
  }

  public void setCodes(List<String> codes) {
    this.codes = codes;
  }

  public DiscountResponse applied(List<@Valid DiscountRequestAppliedInner> applied) {
    this.applied = applied;
    return this;
  }

  public DiscountResponse addAppliedItem(DiscountRequestAppliedInner appliedItem) {
    if (this.applied == null) {
      this.applied = new ArrayList<>();
    }
    this.applied.add(appliedItem);
    return this;
  }

  /**
   * Discounts successfully applied (code-based and automatic).
   * @return applied
   */
  @Valid 
  @Schema(name = "applied", description = "Discounts successfully applied (code-based and automatic).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("applied")
  public List<@Valid DiscountRequestAppliedInner> getApplied() {
    return applied;
  }

  public void setApplied(List<@Valid DiscountRequestAppliedInner> applied) {
    this.applied = applied;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    DiscountResponse discountResponse = (DiscountResponse) o;
    return Objects.equals(this.codes, discountResponse.codes) &&
        Objects.equals(this.applied, discountResponse.applied);
  }

  @Override
  public int hashCode() {
    return Objects.hash(codes, applied);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class DiscountResponse {\n");
    sb.append("    codes: ").append(toIndentedString(codes)).append("\n");
    sb.append("    applied: ").append(toIndentedString(applied)).append("\n");
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

    private DiscountResponse instance;

    public Builder() {
      this(new DiscountResponse());
    }

    protected Builder(DiscountResponse instance) {
      this.instance = instance;
    }

    protected Builder copyOf(DiscountResponse value) { 
      this.instance.setCodes(value.codes);
      this.instance.setApplied(value.applied);
      return this;
    }

    public DiscountResponse.Builder codes(List<String> codes) {
      this.instance.codes(codes);
      return this;
    }
    
    public DiscountResponse.Builder applied(List<DiscountRequestAppliedInner> applied) {
      this.instance.applied(applied);
      return this;
    }
    
    /**
    * returns a built DiscountResponse instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public DiscountResponse build() {
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
  public static DiscountResponse.Builder builder() {
    return new DiscountResponse.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public DiscountResponse.Builder toBuilder() {
    DiscountResponse.Builder builder = new DiscountResponse.Builder();
    return builder.copyOf(this);
  }

}

