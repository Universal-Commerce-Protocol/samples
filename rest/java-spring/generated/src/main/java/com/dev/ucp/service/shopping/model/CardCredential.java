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
import com.fasterxml.jackson.annotation.JsonValue;
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
 * A card credential containing sensitive payment card details including raw Primary Account Numbers (PANs). This credential type MUST NOT be used for checkout, only with payment handlers that tokenize or encrypt credentials. CRITICAL: Both parties handling CardCredential (sender and receiver) MUST be PCI DSS compliant. Transmission MUST use HTTPS/TLS with strong cipher suites.
 */

@Schema(name = "Card_Credential", description = "A card credential containing sensitive payment card details including raw Primary Account Numbers (PANs). This credential type MUST NOT be used for checkout, only with payment handlers that tokenize or encrypt credentials. CRITICAL: Both parties handling CardCredential (sender and receiver) MUST be PCI DSS compliant. Transmission MUST use HTTPS/TLS with strong cipher suites.")
@JsonTypeName("Card_Credential")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CardCredential implements PaymentCredential {

  private JsonNullable<JsonNode> type = JsonNullable.<JsonNode>undefined();

  /**
   * The type of card number. Network tokens are preferred with fallback to FPAN. See PCI Scope for more details.
   */
  public enum CardNumberTypeEnum {
    FPAN("fpan"),
    
    NETWORK_TOKEN("network_token"),
    
    DPAN("dpan");

    private final String value;

    CardNumberTypeEnum(String value) {
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
    public static CardNumberTypeEnum fromValue(String value) {
      for (CardNumberTypeEnum b : CardNumberTypeEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  private CardNumberTypeEnum cardNumberType;

  private @Nullable String number;

  private @Nullable Integer expiryMonth;

  private @Nullable Integer expiryYear;

  private @Nullable String name;

  private @Nullable String cvc;

  private @Nullable String cryptogram;

  private @Nullable String eciValue;

  public CardCredential() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public CardCredential(JsonNode type, CardNumberTypeEnum cardNumberType) {
    this.type = JsonNullable.of(type);
    this.cardNumberType = cardNumberType;
  }

  public CardCredential type(JsonNode type) {
    this.type = JsonNullable.of(type);
    return this;
  }

  /**
   * Get type
   * @return type
   */
  @NotNull @Valid 
  @Schema(name = "type", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public JsonNullable<JsonNode> getType() {
    return type;
  }

  public void setType(JsonNullable<JsonNode> type) {
    this.type = type;
  }

  public CardCredential cardNumberType(CardNumberTypeEnum cardNumberType) {
    this.cardNumberType = cardNumberType;
    return this;
  }

  /**
   * The type of card number. Network tokens are preferred with fallback to FPAN. See PCI Scope for more details.
   * @return cardNumberType
   */
  @NotNull 
  @Schema(name = "card_number_type", description = "The type of card number. Network tokens are preferred with fallback to FPAN. See PCI Scope for more details.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("card_number_type")
  public CardNumberTypeEnum getCardNumberType() {
    return cardNumberType;
  }

  public void setCardNumberType(CardNumberTypeEnum cardNumberType) {
    this.cardNumberType = cardNumberType;
  }

  public CardCredential number(@Nullable String number) {
    this.number = number;
    return this;
  }

  /**
   * Card number.
   * @return number
   */
  
  @Schema(name = "number", description = "Card number.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("number")
  public @Nullable String getNumber() {
    return number;
  }

  public void setNumber(@Nullable String number) {
    this.number = number;
  }

  public CardCredential expiryMonth(@Nullable Integer expiryMonth) {
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

  public CardCredential expiryYear(@Nullable Integer expiryYear) {
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

  public CardCredential name(@Nullable String name) {
    this.name = name;
    return this;
  }

  /**
   * Cardholder name.
   * @return name
   */
  
  @Schema(name = "name", description = "Cardholder name.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("name")
  public @Nullable String getName() {
    return name;
  }

  public void setName(@Nullable String name) {
    this.name = name;
  }

  public CardCredential cvc(@Nullable String cvc) {
    this.cvc = cvc;
    return this;
  }

  /**
   * Card CVC number.
   * @return cvc
   */
  @Size(max = 4) 
  @Schema(name = "cvc", description = "Card CVC number.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("cvc")
  public @Nullable String getCvc() {
    return cvc;
  }

  public void setCvc(@Nullable String cvc) {
    this.cvc = cvc;
  }

  public CardCredential cryptogram(@Nullable String cryptogram) {
    this.cryptogram = cryptogram;
    return this;
  }

  /**
   * Cryptogram provided with network tokens.
   * @return cryptogram
   */
  
  @Schema(name = "cryptogram", description = "Cryptogram provided with network tokens.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("cryptogram")
  public @Nullable String getCryptogram() {
    return cryptogram;
  }

  public void setCryptogram(@Nullable String cryptogram) {
    this.cryptogram = cryptogram;
  }

  public CardCredential eciValue(@Nullable String eciValue) {
    this.eciValue = eciValue;
    return this;
  }

  /**
   * Electronic Commerce Indicator / Security Level Indicator provided with network tokens.
   * @return eciValue
   */
  
  @Schema(name = "eci_value", description = "Electronic Commerce Indicator / Security Level Indicator provided with network tokens.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("eci_value")
  public @Nullable String getEciValue() {
    return eciValue;
  }

  public void setEciValue(@Nullable String eciValue) {
    this.eciValue = eciValue;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    CardCredential cardCredential = (CardCredential) o;
    return Objects.equals(this.type, cardCredential.type) &&
        Objects.equals(this.cardNumberType, cardCredential.cardNumberType) &&
        Objects.equals(this.number, cardCredential.number) &&
        Objects.equals(this.expiryMonth, cardCredential.expiryMonth) &&
        Objects.equals(this.expiryYear, cardCredential.expiryYear) &&
        Objects.equals(this.name, cardCredential.name) &&
        Objects.equals(this.cvc, cardCredential.cvc) &&
        Objects.equals(this.cryptogram, cardCredential.cryptogram) &&
        Objects.equals(this.eciValue, cardCredential.eciValue);
  }

  @Override
  public int hashCode() {
    return Objects.hash(type, cardNumberType, number, expiryMonth, expiryYear, name, cvc, cryptogram, eciValue);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CardCredential {\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    cardNumberType: ").append(toIndentedString(cardNumberType)).append("\n");
    sb.append("    number: ").append(toIndentedString(number)).append("\n");
    sb.append("    expiryMonth: ").append(toIndentedString(expiryMonth)).append("\n");
    sb.append("    expiryYear: ").append(toIndentedString(expiryYear)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    cvc: ").append(toIndentedString(cvc)).append("\n");
    sb.append("    cryptogram: ").append(toIndentedString(cryptogram)).append("\n");
    sb.append("    eciValue: ").append(toIndentedString(eciValue)).append("\n");
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

    private CardCredential instance;

    public Builder() {
      this(new CardCredential());
    }

    protected Builder(CardCredential instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CardCredential value) { 
      this.instance.setType(value.type);
      this.instance.setCardNumberType(value.cardNumberType);
      this.instance.setNumber(value.number);
      this.instance.setExpiryMonth(value.expiryMonth);
      this.instance.setExpiryYear(value.expiryYear);
      this.instance.setName(value.name);
      this.instance.setCvc(value.cvc);
      this.instance.setCryptogram(value.cryptogram);
      this.instance.setEciValue(value.eciValue);
      return this;
    }

    public CardCredential.Builder type(JsonNode type) {
      this.instance.type(type);
      return this;
    }
    
    public CardCredential.Builder type(JsonNullable<JsonNode> type) {
      this.instance.type = type;
      return this;
    }
    
    public CardCredential.Builder cardNumberType(CardNumberTypeEnum cardNumberType) {
      this.instance.cardNumberType(cardNumberType);
      return this;
    }
    
    public CardCredential.Builder number(String number) {
      this.instance.number(number);
      return this;
    }
    
    public CardCredential.Builder expiryMonth(Integer expiryMonth) {
      this.instance.expiryMonth(expiryMonth);
      return this;
    }
    
    public CardCredential.Builder expiryYear(Integer expiryYear) {
      this.instance.expiryYear(expiryYear);
      return this;
    }
    
    public CardCredential.Builder name(String name) {
      this.instance.name(name);
      return this;
    }
    
    public CardCredential.Builder cvc(String cvc) {
      this.instance.cvc(cvc);
      return this;
    }
    
    public CardCredential.Builder cryptogram(String cryptogram) {
      this.instance.cryptogram(cryptogram);
      return this;
    }
    
    public CardCredential.Builder eciValue(String eciValue) {
      this.instance.eciValue(eciValue);
      return this;
    }
    
    /**
    * returns a built CardCredential instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CardCredential build() {
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
  public static CardCredential.Builder builder() {
    return new CardCredential.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CardCredential.Builder toBuilder() {
    CardCredential.Builder builder = new CardCredential.Builder();
    return builder.copyOf(this);
  }

}

