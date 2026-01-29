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
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * The data that will used to submit payment to the merchant.
 */

@Schema(name = "payment_data", description = "The data that will used to submit payment to the merchant.")
@JsonTypeName("payment_data")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class PaymentData {

  private CardPaymentInstrument paymentData;

  public PaymentData() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public PaymentData(CardPaymentInstrument paymentData) {
    this.paymentData = paymentData;
  }

  public PaymentData paymentData(CardPaymentInstrument paymentData) {
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

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PaymentData paymentData = (PaymentData) o;
    return Objects.equals(this.paymentData, paymentData.paymentData);
  }

  @Override
  public int hashCode() {
    return Objects.hash(paymentData);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class PaymentData {\n");
    sb.append("    paymentData: ").append(toIndentedString(paymentData)).append("\n");
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

    private PaymentData instance;

    public Builder() {
      this(new PaymentData());
    }

    protected Builder(PaymentData instance) {
      this.instance = instance;
    }

    protected Builder copyOf(PaymentData value) { 
      this.instance.setPaymentData(value.paymentData);
      return this;
    }

    public PaymentData.Builder paymentData(CardPaymentInstrument paymentData) {
      this.instance.paymentData(paymentData);
      return this;
    }
    
    /**
    * returns a built PaymentData instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public PaymentData build() {
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
  public static PaymentData.Builder builder() {
    return new PaymentData.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public PaymentData.Builder toBuilder() {
    PaymentData.Builder builder = new PaymentData.Builder();
    return builder.copyOf(this);
  }

}

