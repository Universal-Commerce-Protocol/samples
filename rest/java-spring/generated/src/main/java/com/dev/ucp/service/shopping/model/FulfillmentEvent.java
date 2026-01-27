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
import com.dev.ucp.service.shopping.model.FulfillmentEventLineItemsInner;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonTypeName;
import java.net.URI;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.lang.Nullable;
import org.openapitools.jackson.nullable.JsonNullable;
import java.time.OffsetDateTime;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import io.swagger.v3.oas.annotations.media.Schema;


import java.util.*;
import jakarta.annotation.Generated;

/**
 * Append-only fulfillment event representing an actual shipment. References line items by ID.
 */

@Schema(name = "Fulfillment_Event", description = "Append-only fulfillment event representing an actual shipment. References line items by ID.")
@JsonTypeName("Fulfillment_Event")
@Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2026-01-26T17:13:20.046324970Z[Etc/UTC]", comments = "Generator version: 7.17.0")
public class FulfillmentEvent {

  private String id;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private OffsetDateTime occurredAt;

  private String type;

  @Valid
  private List<@Valid FulfillmentEventLineItemsInner> lineItems = new ArrayList<>();

  private @Nullable String trackingNumber;

  private @Nullable URI trackingUrl;

  private @Nullable String carrier;

  private @Nullable String description;

  public FulfillmentEvent() {
    super();
  }

  /**
   * Constructor with only required parameters
   */
  public FulfillmentEvent(String id, OffsetDateTime occurredAt, String type, List<@Valid FulfillmentEventLineItemsInner> lineItems) {
    this.id = id;
    this.occurredAt = occurredAt;
    this.type = type;
    this.lineItems = lineItems;
  }

  public FulfillmentEvent id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Fulfillment event identifier.
   * @return id
   */
  @NotNull 
  @Schema(name = "id", description = "Fulfillment event identifier.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("id")
  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public FulfillmentEvent occurredAt(OffsetDateTime occurredAt) {
    this.occurredAt = occurredAt;
    return this;
  }

  /**
   * RFC 3339 timestamp when this fulfillment event occurred.
   * @return occurredAt
   */
  @NotNull @Valid 
  @Schema(name = "occurred_at", description = "RFC 3339 timestamp when this fulfillment event occurred.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("occurred_at")
  public OffsetDateTime getOccurredAt() {
    return occurredAt;
  }

  public void setOccurredAt(OffsetDateTime occurredAt) {
    this.occurredAt = occurredAt;
  }

  public FulfillmentEvent type(String type) {
    this.type = type;
    return this;
  }

  /**
   * Fulfillment event type. Common values include: processing (preparing to ship), shipped (handed to carrier), in_transit (in delivery network), delivered (received by buyer), failed_attempt (delivery attempt failed), canceled (fulfillment canceled), undeliverable (cannot be delivered), returned_to_sender (returned to merchant).
   * @return type
   */
  @NotNull 
  @Schema(name = "type", description = "Fulfillment event type. Common values include: processing (preparing to ship), shipped (handed to carrier), in_transit (in delivery network), delivered (received by buyer), failed_attempt (delivery attempt failed), canceled (fulfillment canceled), undeliverable (cannot be delivered), returned_to_sender (returned to merchant).", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("type")
  public String getType() {
    return type;
  }

  public void setType(String type) {
    this.type = type;
  }

  public FulfillmentEvent lineItems(List<@Valid FulfillmentEventLineItemsInner> lineItems) {
    this.lineItems = lineItems;
    return this;
  }

  public FulfillmentEvent addLineItemsItem(FulfillmentEventLineItemsInner lineItemsItem) {
    if (this.lineItems == null) {
      this.lineItems = new ArrayList<>();
    }
    this.lineItems.add(lineItemsItem);
    return this;
  }

  /**
   * Which line items and quantities are fulfilled in this event.
   * @return lineItems
   */
  @NotNull @Valid 
  @Schema(name = "line_items", description = "Which line items and quantities are fulfilled in this event.", requiredMode = Schema.RequiredMode.REQUIRED)
  @JsonProperty("line_items")
  public List<@Valid FulfillmentEventLineItemsInner> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<@Valid FulfillmentEventLineItemsInner> lineItems) {
    this.lineItems = lineItems;
  }

  public FulfillmentEvent trackingNumber(@Nullable String trackingNumber) {
    this.trackingNumber = trackingNumber;
    return this;
  }

  /**
   * Carrier tracking number (required if type != processing).
   * @return trackingNumber
   */
  
  @Schema(name = "tracking_number", description = "Carrier tracking number (required if type != processing).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("tracking_number")
  public @Nullable String getTrackingNumber() {
    return trackingNumber;
  }

  public void setTrackingNumber(@Nullable String trackingNumber) {
    this.trackingNumber = trackingNumber;
  }

  public FulfillmentEvent trackingUrl(@Nullable URI trackingUrl) {
    this.trackingUrl = trackingUrl;
    return this;
  }

  /**
   * URL to track this shipment (required if type != processing).
   * @return trackingUrl
   */
  @Valid 
  @Schema(name = "tracking_url", description = "URL to track this shipment (required if type != processing).", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("tracking_url")
  public @Nullable URI getTrackingUrl() {
    return trackingUrl;
  }

  public void setTrackingUrl(@Nullable URI trackingUrl) {
    this.trackingUrl = trackingUrl;
  }

  public FulfillmentEvent carrier(@Nullable String carrier) {
    this.carrier = carrier;
    return this;
  }

  /**
   * Carrier name (e.g., 'FedEx', 'USPS').
   * @return carrier
   */
  
  @Schema(name = "carrier", description = "Carrier name (e.g., 'FedEx', 'USPS').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("carrier")
  public @Nullable String getCarrier() {
    return carrier;
  }

  public void setCarrier(@Nullable String carrier) {
    this.carrier = carrier;
  }

  public FulfillmentEvent description(@Nullable String description) {
    this.description = description;
    return this;
  }

  /**
   * Human-readable description of the shipment status or delivery information (e.g., 'Delivered to front door', 'Out for delivery').
   * @return description
   */
  
  @Schema(name = "description", description = "Human-readable description of the shipment status or delivery information (e.g., 'Delivered to front door', 'Out for delivery').", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
  @JsonProperty("description")
  public @Nullable String getDescription() {
    return description;
  }

  public void setDescription(@Nullable String description) {
    this.description = description;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    FulfillmentEvent fulfillmentEvent = (FulfillmentEvent) o;
    return Objects.equals(this.id, fulfillmentEvent.id) &&
        Objects.equals(this.occurredAt, fulfillmentEvent.occurredAt) &&
        Objects.equals(this.type, fulfillmentEvent.type) &&
        Objects.equals(this.lineItems, fulfillmentEvent.lineItems) &&
        Objects.equals(this.trackingNumber, fulfillmentEvent.trackingNumber) &&
        Objects.equals(this.trackingUrl, fulfillmentEvent.trackingUrl) &&
        Objects.equals(this.carrier, fulfillmentEvent.carrier) &&
        Objects.equals(this.description, fulfillmentEvent.description);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, occurredAt, type, lineItems, trackingNumber, trackingUrl, carrier, description);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class FulfillmentEvent {\n");
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    occurredAt: ").append(toIndentedString(occurredAt)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    lineItems: ").append(toIndentedString(lineItems)).append("\n");
    sb.append("    trackingNumber: ").append(toIndentedString(trackingNumber)).append("\n");
    sb.append("    trackingUrl: ").append(toIndentedString(trackingUrl)).append("\n");
    sb.append("    carrier: ").append(toIndentedString(carrier)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
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

    private FulfillmentEvent instance;

    public Builder() {
      this(new FulfillmentEvent());
    }

    protected Builder(FulfillmentEvent instance) {
      this.instance = instance;
    }

    protected Builder copyOf(FulfillmentEvent value) { 
      this.instance.setId(value.id);
      this.instance.setOccurredAt(value.occurredAt);
      this.instance.setType(value.type);
      this.instance.setLineItems(value.lineItems);
      this.instance.setTrackingNumber(value.trackingNumber);
      this.instance.setTrackingUrl(value.trackingUrl);
      this.instance.setCarrier(value.carrier);
      this.instance.setDescription(value.description);
      return this;
    }

    public FulfillmentEvent.Builder id(String id) {
      this.instance.id(id);
      return this;
    }
    
    public FulfillmentEvent.Builder occurredAt(OffsetDateTime occurredAt) {
      this.instance.occurredAt(occurredAt);
      return this;
    }
    
    public FulfillmentEvent.Builder type(String type) {
      this.instance.type(type);
      return this;
    }
    
    public FulfillmentEvent.Builder lineItems(List<FulfillmentEventLineItemsInner> lineItems) {
      this.instance.lineItems(lineItems);
      return this;
    }
    
    public FulfillmentEvent.Builder trackingNumber(String trackingNumber) {
      this.instance.trackingNumber(trackingNumber);
      return this;
    }
    
    public FulfillmentEvent.Builder trackingUrl(URI trackingUrl) {
      this.instance.trackingUrl(trackingUrl);
      return this;
    }
    
    public FulfillmentEvent.Builder carrier(String carrier) {
      this.instance.carrier(carrier);
      return this;
    }
    
    public FulfillmentEvent.Builder description(String description) {
      this.instance.description(description);
      return this;
    }
    
    /**
    * returns a built FulfillmentEvent instance.
    *
    * The builder is not reusable (NullPointerException)
    */
    public FulfillmentEvent build() {
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
  public static FulfillmentEvent.Builder builder() {
    return new FulfillmentEvent.Builder();
  }

  /**
  * Create a builder with a shallow copy of this instance.
  */
  public FulfillmentEvent.Builder toBuilder() {
    FulfillmentEvent.Builder builder = new FulfillmentEvent.Builder();
    return builder.copyOf(this);
  }

}

