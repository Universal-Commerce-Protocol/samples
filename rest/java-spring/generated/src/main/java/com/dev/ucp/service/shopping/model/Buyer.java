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
import com.fasterxml.jackson.databind.JsonNode;
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
 * Representation of the buyer.
 */

@Schema(name = "Buyer", description = "Representation of the buyer.")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class Buyer {

  private @Nullable String firstName;

  private @Nullable String lastName;

  private @Nullable String fullName;

  private @Nullable String email;

  private @Nullable String phoneNumber;

  public Buyer firstName(@Nullable String firstName) {
    this.firstName = firstName;
    return this;
  }

  /**
   * First name of the buyer.
   * @return firstName
   */
  
  @Schema(name = "first_name", description = "First name of the buyer.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("first_name")
  public @Nullable String getFirstName() {
    return firstName;
  }

  public void setFirstName(@Nullable String firstName) {
    this.firstName = firstName;
  }

  public Buyer lastName(@Nullable String lastName) {
    this.lastName = lastName;
    return this;
  }

  /**
   * Last name of the buyer.
   * @return lastName
   */
  
  @Schema(name = "last_name", description = "Last name of the buyer.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("last_name")
  public @Nullable String getLastName() {
    return lastName;
  }

  public void setLastName(@Nullable String lastName) {
    this.lastName = lastName;
  }

  public Buyer fullName(@Nullable String fullName) {
    this.fullName = fullName;
    return this;
  }

  /**
   * Optional, buyer's full name (if first_name or last_name fields are present they take precedence).
   * @return fullName
   */
  
  @Schema(name = "full_name", description = "Optional, buyer's full name (if first_name or last_name fields are present they take precedence).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("full_name")
  public @Nullable String getFullName() {
    return fullName;
  }

  public void setFullName(@Nullable String fullName) {
    this.fullName = fullName;
  }

  public Buyer email(@Nullable String email) {
    this.email = email;
    return this;
  }

  /**
   * Email of the buyer.
   * @return email
   */
  
  @Schema(name = "email", description = "Email of the buyer.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("email")
  public @Nullable String getEmail() {
    return email;
  }

  public void setEmail(@Nullable String email) {
    this.email = email;
  }

  public Buyer phoneNumber(@Nullable String phoneNumber) {
    this.phoneNumber = phoneNumber;
    return this;
  }

  /**
   * E.164 standard.
   * @return phoneNumber
   */
  
  @Schema(name = "phone_number", description = "E.164 standard.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("phone_number")
  public @Nullable String getPhoneNumber() {
    return phoneNumber;
  }

  public void setPhoneNumber(@Nullable String phoneNumber) {
    this.phoneNumber = phoneNumber;
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
    public Buyer putAdditionalProperty(String key, JsonNode value) {
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
    Buyer buyer = (Buyer) o;
    return Objects.equals(this.firstName, buyer.firstName) &&
        Objects.equals(this.lastName, buyer.lastName) &&
        Objects.equals(this.fullName, buyer.fullName) &&
        Objects.equals(this.email, buyer.email) &&
        Objects.equals(this.phoneNumber, buyer.phoneNumber) &&
    Objects.equals(this.additionalProperties, buyer.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(firstName, lastName, fullName, email, phoneNumber, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Buyer {\n");
    sb.append("    firstName: ").append(toIndentedString(firstName)).append("\n");
    sb.append("    lastName: ").append(toIndentedString(lastName)).append("\n");
    sb.append("    fullName: ").append(toIndentedString(fullName)).append("\n");
    sb.append("    email: ").append(toIndentedString(email)).append("\n");
    sb.append("    phoneNumber: ").append(toIndentedString(phoneNumber)).append("\n");
    
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

    private Buyer instance;

    public Builder() {
      this(new Buyer());
    }

    protected Builder(Buyer instance) {
      this.instance = instance;
    }

    protected Builder copyOf(Buyer value) { 
      this.instance.setFirstName(value.firstName);
      this.instance.setLastName(value.lastName);
      this.instance.setFullName(value.fullName);
      this.instance.setEmail(value.email);
      this.instance.setPhoneNumber(value.phoneNumber);
      return this;
    }

    public Buyer.Builder firstName(String firstName) {
      this.instance.firstName(firstName);
      return this;
    }
    
    public Buyer.Builder lastName(String lastName) {
      this.instance.lastName(lastName);
      return this;
    }
    
    public Buyer.Builder fullName(String fullName) {
      this.instance.fullName(fullName);
      return this;
    }
    
    public Buyer.Builder email(String email) {
      this.instance.email(email);
      return this;
    }
    
    public Buyer.Builder phoneNumber(String phoneNumber) {
      this.instance.phoneNumber(phoneNumber);
      return this;
    }
    
    public Buyer.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built Buyer instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public Buyer build() {
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
  public static Buyer.Builder builder() {
    return new Buyer.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public Buyer.Builder toBuilder() {
    Buyer.Builder builder = new Buyer.Builder();
    return builder.copyOf(this);
  }

}

