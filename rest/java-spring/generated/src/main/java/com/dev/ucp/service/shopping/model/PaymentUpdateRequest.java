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
 * Payment configuration containing handlers.
 */

@Schema(name = "Payment_Update_Request", description = "Payment configuration containing handlers.")
@JsonTypeName("Payment_Update_Request")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class PaymentUpdateRequest {

  private @Nullable String selectedInstrumentId;

  @Valid
  private List<CardPaymentInstrument> instruments = new ArrayList<>();

  public PaymentUpdateRequest selectedInstrumentId(@Nullable String selectedInstrumentId) {
    this.selectedInstrumentId = selectedInstrumentId;
    return this;
  }

  /**
   * The id of the currently selected payment instrument from the instruments array. Set by the agent when submitting payment, and echoed back by the merchant in finalized state.
   * @return selectedInstrumentId
   */
  
  @Schema(name = "selected_instrument_id", description = "The id of the currently selected payment instrument from the instruments array. Set by the agent when submitting payment, and echoed back by the merchant in finalized state.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("selected_instrument_id")
  public @Nullable String getSelectedInstrumentId() {
    return selectedInstrumentId;
  }

  public void setSelectedInstrumentId(@Nullable String selectedInstrumentId) {
    this.selectedInstrumentId = selectedInstrumentId;
  }

  public PaymentUpdateRequest instruments(List<CardPaymentInstrument> instruments) {
    this.instruments = instruments;
    return this;
  }

  public PaymentUpdateRequest addInstrumentsItem(CardPaymentInstrument instrumentsItem) {
    if (this.instruments == null) {
      this.instruments = new ArrayList<>();
    }
    this.instruments.add(instrumentsItem);
    return this;
  }

  /**
   * The payment instruments available for this payment. Each instrument is associated with a specific handler via the handler_id field. Handlers can extend the base payment_instrument schema to add handler-specific fields.
   * @return instruments
   */
  @Valid 
  @Schema(name = "instruments", description = "The payment instruments available for this payment. Each instrument is associated with a specific handler via the handler_id field. Handlers can extend the base payment_instrument schema to add handler-specific fields.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("instruments")
  public List<CardPaymentInstrument> getInstruments() {
    return instruments;
  }

  public void setInstruments(List<CardPaymentInstrument> instruments) {
    this.instruments = instruments;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    PaymentUpdateRequest paymentUpdateRequest = (PaymentUpdateRequest) o;
    return Objects.equals(this.selectedInstrumentId, paymentUpdateRequest.selectedInstrumentId) &&
        Objects.equals(this.instruments, paymentUpdateRequest.instruments);
  }

  @Override
  public int hashCode() {
    return Objects.hash(selectedInstrumentId, instruments);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class PaymentUpdateRequest {\n");
    sb.append("    selectedInstrumentId: ").append(toIndentedString(selectedInstrumentId)).append("\n");
    sb.append("    instruments: ").append(toIndentedString(instruments)).append("\n");
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

    private PaymentUpdateRequest instance;

    public Builder() {
      this(new PaymentUpdateRequest());
    }

    protected Builder(PaymentUpdateRequest instance) {
      this.instance = instance;
    }

    protected Builder copyOf(PaymentUpdateRequest value) { 
      this.instance.setSelectedInstrumentId(value.selectedInstrumentId);
      this.instance.setInstruments(value.instruments);
      return this;
    }

    public PaymentUpdateRequest.Builder selectedInstrumentId(String selectedInstrumentId) {
      this.instance.selectedInstrumentId(selectedInstrumentId);
      return this;
    }
    
    public PaymentUpdateRequest.Builder instruments(List<CardPaymentInstrument> instruments) {
      this.instance.instruments(instruments);
      return this;
    }
    
    /**
    * returns a built PaymentUpdateRequest instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public PaymentUpdateRequest build() {
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
  public static PaymentUpdateRequest.Builder builder() {
    return new PaymentUpdateRequest.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public PaymentUpdateRequest.Builder toBuilder() {
    PaymentUpdateRequest.Builder builder = new PaymentUpdateRequest.Builder();
    return builder.copyOf(this);
  }

}

