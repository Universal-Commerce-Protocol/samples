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
import com.dev.ucp.service.shopping.model.CardPaymentInstrument;
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
 * CompleteCheckoutRequest
 */

@JsonTypeName("complete_checkout_request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class CompleteCheckoutRequest {

  private CardPaymentInstrument paymentData;

  private @Nullable JsonNode riskSignals;

  public CompleteCheckoutRequest() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public CompleteCheckoutRequest(CardPaymentInstrument paymentData) {
    this.paymentData = paymentData;
  }

  public CompleteCheckoutRequest paymentData(CardPaymentInstrument paymentData) {
    this.paymentData = paymentData;
    return this;
  }

  /**
   * Get paymentData
   * @return paymentData
   */
  @NotNull @Valid 
  @Schema(name = "payment_data", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("payment_data")
  public CardPaymentInstrument getPaymentData() {
    return paymentData;
  }

  public void setPaymentData(CardPaymentInstrument paymentData) {
    this.paymentData = paymentData;
  }

  public CompleteCheckoutRequest riskSignals(@Nullable JsonNode riskSignals) {
    this.riskSignals = riskSignals;
    return this;
  }

  /**
   * Key-value pairs of risk signals.
   * @return riskSignals
   */
  @Valid 
  @Schema(name = "risk_signals", description = "Key-value pairs of risk signals.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("risk_signals")
  public @Nullable JsonNode getRiskSignals() {
    return riskSignals;
  }

  public void setRiskSignals(@Nullable JsonNode riskSignals) {
    this.riskSignals = riskSignals;
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
    public CompleteCheckoutRequest putAdditionalProperty(String key, JsonNode value) {
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
    CompleteCheckoutRequest completeCheckoutRequest = (CompleteCheckoutRequest) o;
    return Objects.equals(this.paymentData, completeCheckoutRequest.paymentData) &&
        Objects.equals(this.riskSignals, completeCheckoutRequest.riskSignals) &&
    Objects.equals(this.additionalProperties, completeCheckoutRequest.additionalProperties);
  }

  @Override
  public int hashCode() {
    return Objects.hash(paymentData, riskSignals, additionalProperties);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class CompleteCheckoutRequest {\n");
    sb.append("    paymentData: ").append(toIndentedString(paymentData)).append("\n");
    sb.append("    riskSignals: ").append(toIndentedString(riskSignals)).append("\n");
    
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

    private CompleteCheckoutRequest instance;

    public Builder() {
      this(new CompleteCheckoutRequest());
    }

    protected Builder(CompleteCheckoutRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(CompleteCheckoutRequest value) { 
      this.instance.setPaymentData(value.paymentData);
      this.instance.setRiskSignals(value.riskSignals);
      return this;
    }

    public CompleteCheckoutRequest.Builder paymentData(CardPaymentInstrument paymentData) {
      this.instance.paymentData(paymentData);
      return this;
    }
    
    public CompleteCheckoutRequest.Builder riskSignals(JsonNode riskSignals) {
      this.instance.riskSignals(riskSignals);
      return this;
    }
    
    public CompleteCheckoutRequest.Builder additionalProperties(Map<String, JsonNode> additionalProperties) {
      this.instance.additionalProperties = additionalProperties;
      return this;
    }

    /**
    * returns a built CompleteCheckoutRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public CompleteCheckoutRequest build() {
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
  public static CompleteCheckoutRequest.Builder builder() {
    return new CompleteCheckoutRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public CompleteCheckoutRequest.Builder toBuilder() {
    CompleteCheckoutRequest.Builder builder = new CompleteCheckoutRequest.Builder();
    return builder.copyOf(this);
  }

}

