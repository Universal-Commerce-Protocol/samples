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
import com.dev.ucp.service.shopping.model.Expectation;
import com.dev.ucp.service.shopping.model.FulfillmentEvent;
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
 * Fulfillment data: buyer expectations and what actually happened.
 */

@Schema(name = "order_fulfillment", description = "Fulfillment data: buyer expectations and what actually happened.")
@JsonTypeName("order_fulfillment")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class OrderFulfillment {

  @Valid
  private List<@Valid Expectation> expectations = new ArrayList<>();

  @Valid
  private List<@Valid FulfillmentEvent> events = new ArrayList<>();

  public OrderFulfillment expectations(List<@Valid Expectation> expectations) {
    this.expectations = expectations;
    return this;
  }

  public OrderFulfillment addExpectationsItem(Expectation expectationsItem) {
    if (this.expectations == null) {
      this.expectations = new ArrayList<>();
    }
    this.expectations.add(expectationsItem);
    return this;
  }

  /**
   * Buyer-facing groups representing when/how items will be delivered. Can be split, merged, or adjusted post-order.
   * @return expectations
   */
  @Valid 
  @Schema(name = "expectations", description = "Buyer-facing groups representing when/how items will be delivered. Can be split, merged, or adjusted post-order.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("expectations")
  public List<@Valid Expectation> getExpectations() {
    return expectations;
  }

  public void setExpectations(List<@Valid Expectation> expectations) {
    this.expectations = expectations;
  }

  public OrderFulfillment events(List<@Valid FulfillmentEvent> events) {
    this.events = events;
    return this;
  }

  public OrderFulfillment addEventsItem(FulfillmentEvent eventsItem) {
    if (this.events == null) {
      this.events = new ArrayList<>();
    }
    this.events.add(eventsItem);
    return this;
  }

  /**
   * Append-only event log of actual shipments. Each event references line items by ID.
   * @return events
   */
  @Valid 
  @Schema(name = "events", description = "Append-only event log of actual shipments. Each event references line items by ID.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("events")
  public List<@Valid FulfillmentEvent> getEvents() {
    return events;
  }

  public void setEvents(List<@Valid FulfillmentEvent> events) {
    this.events = events;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    OrderFulfillment orderFulfillment = (OrderFulfillment) o;
    return Objects.equals(this.expectations, orderFulfillment.expectations) &&
        Objects.equals(this.events, orderFulfillment.events);
  }

  @Override
  public int hashCode() {
    return Objects.hash(expectations, events);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class OrderFulfillment {\n");
    sb.append("    expectations: ").append(toIndentedString(expectations)).append("\n");
    sb.append("    events: ").append(toIndentedString(events)).append("\n");
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

    private OrderFulfillment instance;

    public Builder() {
      this(new OrderFulfillment());
    }

    protected Builder(OrderFulfillment instance) {
      this.instance = instance;
    }

    protected Builder copyOf(OrderFulfillment value) { 
      this.instance.setExpectations(value.expectations);
      this.instance.setEvents(value.events);
      return this;
    }

    public OrderFulfillment.Builder expectations(List<Expectation> expectations) {
      this.instance.expectations(expectations);
      return this;
    }
    
    public OrderFulfillment.Builder events(List<FulfillmentEvent> events) {
      this.instance.events(events);
      return this;
    }
    
    /**
    * returns a built OrderFulfillment instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public OrderFulfillment build() {
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
  public static OrderFulfillment.Builder builder() {
    return new OrderFulfillment.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public OrderFulfillment.Builder toBuilder() {
    OrderFulfillment.Builder builder = new OrderFulfillment.Builder();
    return builder.copyOf(this);
  }

}

