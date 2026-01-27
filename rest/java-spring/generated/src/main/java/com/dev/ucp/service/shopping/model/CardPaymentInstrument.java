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
import com.dev.ucp.service.shopping.model.PaymentCredential;
import com.dev.ucp.service.shopping.model.PostalAddress;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import com.fasterxml.jackson.annotation.JsonValue;
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
 * A basic card payment instrument with visible card details. Can be inherited by a handler&#39;s instrument schema to define handler-specific display details or more complex credential structures.
 */

@Schema(name = "Card_Payment_Instrument", description = "A basic card payment instrument with visible card details. Can be inherited by a handler's instrument schema to define handler-specific display details or more complex credential structures.")
@JsonTypeName("Card_Payment_Instrument")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CardPaymentInstrument {

  private String id;

  private String handlerId;

  /**
   * Indicates this is a card payment instrument.
   */
  public enum TypeEnum {
    CARD("card");

    private final String value;

    TypeEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static TypeEnum fromValue(String value) {
      for (TypeEnum b : TypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private TypeEnum type;

  private @Nullable PostalAddress billingAddress;

  private @Nullable PaymentCredential credential;

  private String brand;

  private String lastDigits;

  private @Nullable Integer expiryMonth;

  private @Nullable Integer expiryYear;

  private @Nullable String richTextDescription;

  private @Nullable URI richCardArt;

  public CardPaymentInstrument() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public CardPaymentInstrument(String id, String handlerId, TypeEnum type, String brand, String lastDigits) {
    this.id = id;
    this.handlerId = handlerId;
    this.type = type;
    this.brand = brand;
    this.lastDigits = lastDigits;
  }

  public CardPaymentInstrument id(String id) {
    this.id = id;
    return this;
  }

  /**
   * A unique identifier for this instrument instance, assigned by the Agent. Used to reference this specific instrument in the 'payment.selected_instrument_id' field.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "A unique identifier for this instrument instance, assigned by the Agent. Used to reference this specific instrument in the 'payment.selected_instrument_id' field.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public CardPaymentInstrument handlerId(String handlerId) {
    this.handlerId = handlerId;
    return this;
  }

  /**
   * The unique identifier for the handler instance that produced this instrument. This corresponds to the 'id' field in the Payment Handler definition.
   * @return handlerId
   */
  @NotNull 
  @Schema(name = "handler_id", description = "The unique identifier for the handler instance that produced this instrument. This corresponds to the 'id' field in the Payment Handler definition.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("handler_id")
  public String getHandlerId() {
    return handlerId;
  }

  public void setHandlerId(String handlerId) {
    this.handlerId = handlerId;
  }

  public CardPaymentInstrument type(TypeEnum type) {
    this.type = type;
    return this;
  }

  /**
   * Indicates this is a card payment instrument.
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Indicates this is a card payment instrument.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public TypeEnum getType() {
    return type;
  }

  public void setType(TypeEnum type) {
    this.type = type;
  }

  public CardPaymentInstrument billingAddress(@Nullable PostalAddress billingAddress) {
    this.billingAddress = billingAddress;
    return this;
  }

  /**
   * Get billingAddress
   * @return billingAddress
   */
  @Valid 
  @Schema(name = "billing_address", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("billing_address")
  public @Nullable PostalAddress getBillingAddress() {
    return billingAddress;
  }

  public void setBillingAddress(@Nullable PostalAddress billingAddress) {
    this.billingAddress = billingAddress;
  }

  public CardPaymentInstrument credential(@Nullable PaymentCredential credential) {
    this.credential = credential;
    return this;
  }

  /**
   * Get credential
   * @return credential
   */
  @Valid 
  @Schema(name = "credential", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("credential")
  public @Nullable PaymentCredential getCredential() {
    return credential;
  }

  public void setCredential(@Nullable PaymentCredential credential) {
    this.credential = credential;
  }

  public CardPaymentInstrument brand(String brand) {
    this.brand = brand;
    return this;
  }

  /**
   * The card brand/network (e.g., visa, mastercard, amex).
   * @return brand
   */
  @NotNull 
  @Schema(name = "brand", description = "The card brand/network (e.g., visa, mastercard, amex).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("brand")
  public String getBrand() {
    return brand;
  }

  public void setBrand(String brand) {
    this.brand = brand;
  }

  public CardPaymentInstrument lastDigits(String lastDigits) {
    this.lastDigits = lastDigits;
    return this;
  }

  /**
   * Last 4 digits of the card number.
   * @return lastDigits
   */
  @NotNull 
  @Schema(name = "last_digits", description = "Last 4 digits of the card number.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("last_digits")
  public String getLastDigits() {
    return lastDigits;
  }

  public void setLastDigits(String lastDigits) {
    this.lastDigits = lastDigits;
  }

  public CardPaymentInstrument expiryMonth(@Nullable Integer expiryMonth) {
    this.expiryMonth = expiryMonth;
    return this;
  }

  /**
   * The month of the card's expiration date (1-12).
   * @return expiryMonth
   */
  
  @Schema(name = "expiry_month", description = "The month of the card's expiration date (1-12).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("expiry_month")
  public @Nullable Integer getExpiryMonth() {
    return expiryMonth;
  }

  public void setExpiryMonth(@Nullable Integer expiryMonth) {
    this.expiryMonth = expiryMonth;
  }

  public CardPaymentInstrument expiryYear(@Nullable Integer expiryYear) {
    this.expiryYear = expiryYear;
    return this;
  }

  /**
   * The year of the card's expiration date.
   * @return expiryYear
   */
  
  @Schema(name = "expiry_year", description = "The year of the card's expiration date.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("expiry_year")
  public @Nullable Integer getExpiryYear() {
    return expiryYear;
  }

  public void setExpiryYear(@Nullable Integer expiryYear) {
    this.expiryYear = expiryYear;
  }

  public CardPaymentInstrument richTextDescription(@Nullable String richTextDescription) {
    this.richTextDescription = richTextDescription;
    return this;
  }

  /**
   * An optional rich text description of the card to display to the user (e.g., 'Visa ending in 1234, expires 12/2025').
   * @return richTextDescription
   */
  
  @Schema(name = "rich_text_description", description = "An optional rich text description of the card to display to the user (e.g., 'Visa ending in 1234, expires 12/2025').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("rich_text_description")
  public @Nullable String getRichTextDescription() {
    return richTextDescription;
  }

  public void setRichTextDescription(@Nullable String richTextDescription) {
    this.richTextDescription = richTextDescription;
  }

  public CardPaymentInstrument richCardArt(@Nullable URI richCardArt) {
    this.richCardArt = richCardArt;
    return this;
  }

  /**
   * An optional URI to a rich image representing the card (e.g., card art provided by the issuer).
   * @return richCardArt
   */
  @Valid 
  @Schema(name = "rich_card_art", description = "An optional URI to a rich image representing the card (e.g., card art provided by the issuer).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("rich_card_art")
  public @Nullable URI getRichCardArt() {
    return richCardArt;
  }

  public void setRichCardArt(@Nullable URI richCardArt) {
    this.richCardArt = richCardArt;
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
    public CardPaymentInstrument putAdditionalProperty(String key, JsonNode value) {
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
    CardPaymentInstrument cardPaymentInstrument = (CardPaymentInstrument) o;
    return Objects.equals(this.id, cardPaymentInstrument.id) &&
        Objects.equals(this.handlerId, cardPaymentInstrument.handlerId) &&
        Objects.equals(this.type, cardPaymentInstrument.type) &&
        Objects.equals(this.billingAddress, cardPaymentInstrument.billingAddress) &&
        Objects.equals(this.credential, cardPaymentInstrument.credential) &&
        Objects.equals(this.brand, cardPaymentInstrument.brand) &&
        Objects.equals(this.lastDigits, cardPaymentInstrument.lastDigits) &&
        Objects.equals(this.expiryMonth, cardPaymentInstrument.expiryMonth) &&
        Objects.equals(this.expiryYear, cardPaymentInstrument.expiryYear) &&
        Objects.equals(this.richTextDescription, cardPaymentInstrument.richTextDescription) &&
        Objects.equals(this.richCardArt, cardPaymentInstrument.richCardArt) &&
    Objects.equals(this.additionalProperties, cardPaymentInstrument.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, handlerId, type, billingAddress, credential, brand, lastDigits, expiryMonth, expiryYear, richTextDescription, richCardArt, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CardPaymentInstrument {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    handlerId: ").append(toIndentedString(handlerId)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    billingAddress: ").append(toIndentedString(billingAddress)).append("\n");
    sb.append("    credential: ").append(toIndentedString(credential)).append("\n");
    sb.append("    brand: ").append(toIndentedString(brand)).append("\n");
    sb.append("    lastDigits: ").append(toIndentedString(lastDigits)).append("\n");
    sb.append("    expiryMonth: ").append(toIndentedString(expiryMonth)).append("\n");
    sb.append("    expiryYear: ").append(toIndentedString(expiryYear)).append("\n");
    sb.append("    richTextDescription: ").append(toIndentedString(richTextDescription)).append("\n");
    sb.append("    richCardArt: ").append(toIndentedString(richCardArt)).append("\n");
    
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

    private CardPaymentInstrument instance;

    public Builder() {
      this(new CardPaymentInstrument());
    }

    protected Builder(CardPaymentInstrument instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CardPaymentInstrument value) { 
      this.instance.setId(value.id);
      this.instance.setHandlerId(value.handlerId);
      this.instance.setType(value.type);
      this.instance.setBillingAddress(value.billingAddress);
      this.instance.setCredential(value.credential);
      this.instance.setBrand(value.brand);
      this.instance.setLastDigits(value.lastDigits);
      this.instance.setExpiryMonth(value.expiryMonth);
      this.instance.setExpiryYear(value.expiryYear);
      this.instance.setRichTextDescription(value.richTextDescription);
      this.instance.setRichCardArt(value.richCardArt);
      return this;
    }

    public CardPaymentInstrument.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public CardPaymentInstrument.Builder handlerId(String handlerId) {
      this.instance.handlerId(handlerId);
      return this;
    }
    
    public CardPaymentInstrument.Builder type(TypeEnum type) {
      this.instance.type(type);
      return this;
    }
    
    public CardPaymentInstrument.Builder billingAddress(PostalAddress billingAddress) {
      this.instance.billingAddress(billingAddress);
      return this;
    }
    
    public CardPaymentInstrument.Builder credential(PaymentCredential credential) {
      this.instance.credential(credential);
      return this;
    }
    
    public CardPaymentInstrument.Builder brand(String brand) {
      this.instance.brand(brand);
      return this;
    }
    
    public CardPaymentInstrument.Builder lastDigits(String lastDigits) {
      this.instance.lastDigits(lastDigits);
      return this;
    }
    
    public CardPaymentInstrument.Builder expiryMonth(Integer expiryMonth) {
      this.instance.expiryMonth(expiryMonth);
      return this;
    }
    
    public CardPaymentInstrument.Builder expiryYear(Integer expiryYear) {
      this.instance.expiryYear(expiryYear);
      return this;
    }
    
    public CardPaymentInstrument.Builder richTextDescription(String richTextDescription) {
      this.instance.richTextDescription(richTextDescription);
      return this;
    }
    
    public CardPaymentInstrument.Builder richCardArt(URI richCardArt) {
      this.instance.richCardArt(richCardArt);
      return this;
    }
    
    public CardPaymentInstrument.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built CardPaymentInstrument instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CardPaymentInstrument build() {
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
  public static CardPaymentInstrument.Builder builder() {
    return new CardPaymentInstrument.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CardPaymentInstrument.Builder toBuilder() {
    CardPaymentInstrument.Builder builder = new CardPaymentInstrument.Builder();
    return builder.copyOf(this);
  }

}

