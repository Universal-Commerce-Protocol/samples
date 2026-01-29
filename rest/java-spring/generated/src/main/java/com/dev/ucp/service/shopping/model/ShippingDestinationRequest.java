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

import java.util.Map;
import java.util.HashMap;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
/**
 * Shipping destination.
 */

@Schema(name = "Shipping_Destination_Request", description = "Shipping destination.")
@JsonTypeName("Shipping_Destination_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:22.638361369Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class ShippingDestinationRequest implements FulfillmentDestinationRequest {

  private @Nullable String extendedAddress;

  private @Nullable String streetAddress;

  private @Nullable String addressLocality;

  private @Nullable String addressRegion;

  private @Nullable String addressCountry;

  private @Nullable String postalCode;

  private @Nullable String firstName;

  private @Nullable String lastName;

  private @Nullable String fullName;

  private @Nullable String phoneNumber;

  private @Nullable String id;

  public ShippingDestinationRequest extendedAddress(@Nullable String extendedAddress) {
    this.extendedAddress = extendedAddress;
    return this;
  }

  /**
   * An address extension such as an apartment number, C/O or alternative name.
   * @return extendedAddress
   */
  
  @Schema(name = "extended_address", description = "An address extension such as an apartment number, C/O or alternative name.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("extended_address")
  public @Nullable String getExtendedAddress() {
    return extendedAddress;
  }

  public void setExtendedAddress(@Nullable String extendedAddress) {
    this.extendedAddress = extendedAddress;
  }

  public ShippingDestinationRequest streetAddress(@Nullable String streetAddress) {
    this.streetAddress = streetAddress;
    return this;
  }

  /**
   * The street address.
   * @return streetAddress
   */
  
  @Schema(name = "street_address", description = "The street address.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("street_address")
  public @Nullable String getStreetAddress() {
    return streetAddress;
  }

  public void setStreetAddress(@Nullable String streetAddress) {
    this.streetAddress = streetAddress;
  }

  public ShippingDestinationRequest addressLocality(@Nullable String addressLocality) {
    this.addressLocality = addressLocality;
    return this;
  }

  /**
   * The locality in which the street address is, and which is in the region. For example, Mountain View.
   * @return addressLocality
   */
  
  @Schema(name = "address_locality", description = "The locality in which the street address is, and which is in the region. For example, Mountain View.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("address_locality")
  public @Nullable String getAddressLocality() {
    return addressLocality;
  }

  public void setAddressLocality(@Nullable String addressLocality) {
    this.addressLocality = addressLocality;
  }

  public ShippingDestinationRequest addressRegion(@Nullable String addressRegion) {
    this.addressRegion = addressRegion;
    return this;
  }

  /**
   * The region in which the locality is, and which is in the country. Required for applicable countries (i.e. state in US, province in CA). For example, California or another appropriate first-level Administrative division.
   * @return addressRegion
   */
  
  @Schema(name = "address_region", description = "The region in which the locality is, and which is in the country. Required for applicable countries (i.e. state in US, province in CA). For example, California or another appropriate first-level Administrative division.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("address_region")
  public @Nullable String getAddressRegion() {
    return addressRegion;
  }

  public void setAddressRegion(@Nullable String addressRegion) {
    this.addressRegion = addressRegion;
  }

  public ShippingDestinationRequest addressCountry(@Nullable String addressCountry) {
    this.addressCountry = addressCountry;
    return this;
  }

  /**
   * The country. Recommended to be in 2-letter ISO 3166-1 alpha-2 format, for example \"US\". For backward compatibility, a 3-letter ISO 3166-1 alpha-3 country code such as \"SGP\" or a full country name such as \"Singapore\" can also be used.
   * @return addressCountry
   */
  
  @Schema(name = "address_country", description = "The country. Recommended to be in 2-letter ISO 3166-1 alpha-2 format, for example \"US\". For backward compatibility, a 3-letter ISO 3166-1 alpha-3 country code such as \"SGP\" or a full country name such as \"Singapore\" can also be used.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("address_country")
  public @Nullable String getAddressCountry() {
    return addressCountry;
  }

  public void setAddressCountry(@Nullable String addressCountry) {
    this.addressCountry = addressCountry;
  }

  public ShippingDestinationRequest postalCode(@Nullable String postalCode) {
    this.postalCode = postalCode;
    return this;
  }

  /**
   * The postal code. For example, 94043.
   * @return postalCode
   */
  
  @Schema(name = "postal_code", description = "The postal code. For example, 94043.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("postal_code")
  public @Nullable String getPostalCode() {
    return postalCode;
  }

  public void setPostalCode(@Nullable String postalCode) {
    this.postalCode = postalCode;
  }

  public ShippingDestinationRequest firstName(@Nullable String firstName) {
    this.firstName = firstName;
    return this;
  }

  /**
   * Optional. First name of the contact associated with the address.
   * @return firstName
   */
  
  @Schema(name = "first_name", description = "Optional. First name of the contact associated with the address.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("first_name")
  public @Nullable String getFirstName() {
    return firstName;
  }

  public void setFirstName(@Nullable String firstName) {
    this.firstName = firstName;
  }

  public ShippingDestinationRequest lastName(@Nullable String lastName) {
    this.lastName = lastName;
    return this;
  }

  /**
   * Optional. Last name of the contact associated with the address.
   * @return lastName
   */
  
  @Schema(name = "last_name", description = "Optional. Last name of the contact associated with the address.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("last_name")
  public @Nullable String getLastName() {
    return lastName;
  }

  public void setLastName(@Nullable String lastName) {
    this.lastName = lastName;
  }

  public ShippingDestinationRequest fullName(@Nullable String fullName) {
    this.fullName = fullName;
    return this;
  }

  /**
   * Optional. Full name of the contact associated with the address (if first_name or last_name fields are present they take precedence).
   * @return fullName
   */
  
  @Schema(name = "full_name", description = "Optional. Full name of the contact associated with the address (if first_name or last_name fields are present they take precedence).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("full_name")
  public @Nullable String getFullName() {
    return fullName;
  }

  public void setFullName(@Nullable String fullName) {
    this.fullName = fullName;
  }

  public ShippingDestinationRequest phoneNumber(@Nullable String phoneNumber) {
    this.phoneNumber = phoneNumber;
    return this;
  }

  /**
   * Optional. Phone number of the contact associated with the address.
   * @return phoneNumber
   */
  
  @Schema(name = "phone_number", description = "Optional. Phone number of the contact associated with the address.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("phone_number")
  public @Nullable String getPhoneNumber() {
    return phoneNumber;
  }

  public void setPhoneNumber(@Nullable String phoneNumber) {
    this.phoneNumber = phoneNumber;
  }

  public ShippingDestinationRequest id(@Nullable String id) {
    this.id = id;
    return this;
  }

  /**
   * ID specific to this shipping destination.
   * @return id
   */
  
  @Schema(name = "id", description = "ID specific to this shipping destination.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("id")
  public @Nullable String getId() {
    return id;
  }

  public void setId(@Nullable String id) {
    this.id = id;
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
    public ShippingDestinationRequest putAdditionalProperty(String key, JsonNode value) {
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
    ShippingDestinationRequest shippingDestinationRequest = (ShippingDestinationRequest) o;
    return Objects.equals(this.extendedAddress, shippingDestinationRequest.extendedAddress) &&
        Objects.equals(this.streetAddress, shippingDestinationRequest.streetAddress) &&
        Objects.equals(this.addressLocality, shippingDestinationRequest.addressLocality) &&
        Objects.equals(this.addressRegion, shippingDestinationRequest.addressRegion) &&
        Objects.equals(this.addressCountry, shippingDestinationRequest.addressCountry) &&
        Objects.equals(this.postalCode, shippingDestinationRequest.postalCode) &&
        Objects.equals(this.firstName, shippingDestinationRequest.firstName) &&
        Objects.equals(this.lastName, shippingDestinationRequest.lastName) &&
        Objects.equals(this.fullName, shippingDestinationRequest.fullName) &&
        Objects.equals(this.phoneNumber, shippingDestinationRequest.phoneNumber) &&
        Objects.equals(this.id, shippingDestinationRequest.id) &&
    Objects.equals(this.additionalProperties, shippingDestinationRequest.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(extendedAddress, streetAddress, addressLocality, addressRegion, addressCountry, postalCode, firstName, lastName, fullName, phoneNumber, id, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class ShippingDestinationRequest {\n");
    sb.append("    extendedAddress: ").append(toIndentedString(extendedAddress)).append("\n");
    sb.append("    streetAddress: ").append(toIndentedString(streetAddress)).append("\n");
    sb.append("    addressLocality: ").append(toIndentedString(addressLocality)).append("\n");
    sb.append("    addressRegion: ").append(toIndentedString(addressRegion)).append("\n");
    sb.append("    addressCountry: ").append(toIndentedString(addressCountry)).append("\n");
    sb.append("    postalCode: ").append(toIndentedString(postalCode)).append("\n");
    sb.append("    firstName: ").append(toIndentedString(firstName)).append("\n");
    sb.append("    lastName: ").append(toIndentedString(lastName)).append("\n");
    sb.append("    fullName: ").append(toIndentedString(fullName)).append("\n");
    sb.append("    phoneNumber: ").append(toIndentedString(phoneNumber)).append("\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    
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

    private ShippingDestinationRequest instance;

    public Builder() {
      this(new ShippingDestinationRequest());
    }

    protected Builder(ShippingDestinationRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(ShippingDestinationRequest value) { 
      this.instance.setExtendedAddress(value.extendedAddress);
      this.instance.setStreetAddress(value.streetAddress);
      this.instance.setAddressLocality(value.addressLocality);
      this.instance.setAddressRegion(value.addressRegion);
      this.instance.setAddressCountry(value.addressCountry);
      this.instance.setPostalCode(value.postalCode);
      this.instance.setFirstName(value.firstName);
      this.instance.setLastName(value.lastName);
      this.instance.setFullName(value.fullName);
      this.instance.setPhoneNumber(value.phoneNumber);
      this.instance.setId(value.id);
      return this;
    }

    public ShippingDestinationRequest.Builder extendedAddress(String extendedAddress) {
      this.instance.extendedAddress(extendedAddress);
      return this;
    }
    
    public ShippingDestinationRequest.Builder streetAddress(String streetAddress) {
      this.instance.streetAddress(streetAddress);
      return this;
    }
    
    public ShippingDestinationRequest.Builder addressLocality(String addressLocality) {
      this.instance.addressLocality(addressLocality);
      return this;
    }
    
    public ShippingDestinationRequest.Builder addressRegion(String addressRegion) {
      this.instance.addressRegion(addressRegion);
      return this;
    }
    
    public ShippingDestinationRequest.Builder addressCountry(String addressCountry) {
      this.instance.addressCountry(addressCountry);
      return this;
    }
    
    public ShippingDestinationRequest.Builder postalCode(String postalCode) {
      this.instance.postalCode(postalCode);
      return this;
    }
    
    public ShippingDestinationRequest.Builder firstName(String firstName) {
      this.instance.firstName(firstName);
      return this;
    }
    
    public ShippingDestinationRequest.Builder lastName(String lastName) {
      this.instance.lastName(lastName);
      return this;
    }
    
    public ShippingDestinationRequest.Builder fullName(String fullName) {
      this.instance.fullName(fullName);
      return this;
    }
    
    public ShippingDestinationRequest.Builder phoneNumber(String phoneNumber) {
      this.instance.phoneNumber(phoneNumber);
      return this;
    }
    
    public ShippingDestinationRequest.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public ShippingDestinationRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built ShippingDestinationRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public ShippingDestinationRequest build() {
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
  public static ShippingDestinationRequest.Builder builder() {
    return new ShippingDestinationRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public ShippingDestinationRequest.Builder toBuilder() {
    ShippingDestinationRequest.Builder builder = new ShippingDestinationRequest.Builder();
    return builder.copyOf(this);
  }

}

