# Copyright 2026 UCP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Appointment types for UCP.

This module provides types for the com.levro.appointment capability,
which extends checkout to support service booking with location, time slot,
and optional staff selection. Similar to fulfillment, appointments can be
applied to different line items with different options.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from ucp_sdk.models.schemas.shopping.checkout_create_req import (
    CheckoutCreateRequest,
)
from ucp_sdk.models.schemas.shopping.checkout_resp import (
    CheckoutResponse,
)
from ucp_sdk.models.schemas.shopping.checkout_update_req import (
    CheckoutUpdateRequest,
)
from ucp_sdk.models.schemas.shopping.types.retail_location_resp import (
    RetailLocationResponse,
)


# Enums for status values
class LocationStatus(str):
    """Location status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class StaffStatus(str):
    """Staff status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"


# Location-related types
class Coordinate(BaseModel):
    """Geographic coordinates."""

    latitude: float
    longitude: float


class Address(BaseModel):
    """Physical address."""

    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str | None = None
    country: str


class Location(BaseModel):
    """A service location with full details."""

    id: str
    name: str
    address: Address | None = None
    timezone: str
    status: str  # LocationStatus value
    coordinates: Coordinate | None = None
    description: str | None = None


class LocationSummary(BaseModel):
    """Minimal location reference."""

    id: str
    name: str


# Staff-related types
class StaffSummaryResponse(BaseModel):
    """Summary of a staff member."""

    id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    available_at: list[LocationSummary] = Field(default_factory=list)


class StaffResponse(BaseModel):
    """Full staff member details."""

    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    status: str = "active"  # StaffStatus value
    locations: list[LocationSummary] = Field(default_factory=list)

    @property
    def name(self) -> str:
        """Full name for display."""
        return f"{self.first_name} {self.last_name}".strip()


# Customer type
class Customer(BaseModel):
    """Customer information."""

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str


# Service-related types
class ServiceVariation(BaseModel):
    """A bookable service variation from Square catalog."""

    id: str
    service_id: str
    name: str
    description: str | None = None
    display_price: str = Field(
        description="A human-readable price string (e.g. '$50.00' or '$50 - $80')"
    )
    price: float | None = Field(
        default=None,
        description="The exact numeric price for calculation. Null if price varies.",
    )
    duration_seconds: int
    staff: list[StaffSummaryResponse] | None = None


class AppointmentSegment(BaseModel):
    """A segment of an appointment with service, staff, and time details."""

    id: str
    service_variation: ServiceVariation
    staff: StaffSummaryResponse
    start_time: datetime
    end_time: datetime
    location: LocationSummary


class AvailabilitySlot(BaseModel):
    """An available appointment slot from Square."""

    start_time: datetime
    end_time: datetime
    staff: StaffSummaryResponse
    location: LocationSummary


class Booking(BaseModel):
    """A confirmed booking from Square."""

    id: str
    location: Location
    customer: Customer | None = None
    start_time: datetime
    duration_minutes: int | None = None
    segments: list[AppointmentSegment] = Field(default_factory=list)
    customer_notes: str | None = None
    seller_notes: str | None = None


# Option types (similar to FulfillmentOptionResponse)


class AppointmentOptionResponse(BaseModel):
    """An appointment option (e.g., different time slots or staff members)."""

    model_config = ConfigDict(
        extra="allow",
    )
    id: str = Field(description="Unique appointment option identifier")
    start_time: datetime = Field(description="Appointment start time")
    end_time: datetime | None = Field(default=None, description="Appointment end time")
    staff_id: str | None = Field(
        default=None, description="Staff member ID for this option"
    )
    staff_name: str | None = Field(
        default=None, description="Staff member name for display"
    )
    duration_minutes: int | None = Field(
        default=None, description="Duration in minutes"
    )


class AppointmentOptionRequest(BaseModel):
    """An appointment option in a request."""

    model_config = ConfigDict(
        extra="allow",
    )
    id: str = Field(description="Unique appointment option identifier")
    title: str = Field(description="Short label for the option")
    start_time: datetime = Field(description="Appointment start time")
    end_time: datetime | None = Field(default=None, description="Appointment end time")
    staff_id: str | None = Field(
        default=None, description="Staff member ID for this option"
    )
    duration_minutes: int | None = Field(
        default=None, description="Duration in minutes"
    )


# Slot types (similar to FulfillmentGroupResponse - groups line items with options)


class AppointmentSlotResponse(BaseModel):
    """A group of line items with appointment options."""

    model_config = ConfigDict(
        extra="allow",
    )
    id: str = Field(description="Slot identifier for referencing in updates")
    line_item_ids: list[str] = Field(
        description="Line item IDs included in this appointment slot"
    )
    location: RetailLocationResponse = Field(
        description="Location for the appointment slot"
    )
    options: list[AppointmentOptionResponse] | None = Field(
        default=None,
        description="Available appointment options for this slot",
    )
    selected_option_id: str | None = Field(
        default=None,
        description="ID of the selected appointment option for this slot",
    )
    notes: str | None = Field(
        default=None, description="Optional notes for the appointment"
    )


class AppointmentSlotRequest(BaseModel):
    """A group of line items with appointment options in a request."""

    model_config = ConfigDict(
        extra="allow",
    )
    id: str | None = Field(default=None, description="Slot identifier for updates")
    line_item_ids: list[str] = Field(
        description="Line item IDs included in this appointment slot"
    )
    location_id: str = Field(description="Location ID for the appointment")
    staff_id: str | None = Field(
        default=None, description="Staff member ID for this appointment"
    )
    start_time: datetime = Field(description="Appointment start time")
    notes: str | None = Field(
        default=None, description="Optional notes for the appointment"
    )


# Container types (similar to FulfillmentResponse)


class AppointmentResponse(BaseModel):
    """Container for appointment slots and availability."""

    model_config = ConfigDict(
        extra="allow",
    )
    slots: list[AppointmentSlotResponse] | None = Field(
        default=None, description="Appointment slots for line items"
    )


class AppointmentRequest(BaseModel):
    """Container for appointment slots in a request."""

    model_config = ConfigDict(
        extra="allow",
    )
    slots: list[AppointmentSlotRequest] | None = Field(
        default=None, description="Appointment slots for line items"
    )


# Checkout extension types (similar to fulfillment_resp.py, etc.)


class AppointmentCheckoutResponse(CheckoutResponse):
    """Checkout extended with appointment details."""

    model_config = ConfigDict(
        extra="allow",
    )
    appointment: AppointmentResponse | None = None
    """
    Appointment details.
    """


class AppointmentCheckoutCreateRequest(CheckoutCreateRequest):
    """Checkout create request extended with appointment details."""

    model_config = ConfigDict(
        extra="allow",
    )
    appointment: AppointmentRequest | None = None
    """
    Appointment details.
    """


class AppointmentCheckoutUpdateRequest(CheckoutUpdateRequest):
    """Checkout update request extended with appointment details."""

    model_config = ConfigDict(
        extra="allow",
    )
    appointment: AppointmentRequest | None = None
    """
    Appointment details.
    """


# Aliases for backwards compatibility and convenience
AppointmentCheckout = AppointmentCheckoutResponse
Appointment = AppointmentResponse
