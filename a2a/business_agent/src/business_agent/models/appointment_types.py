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
from ucp_sdk.model.schemas.shopping.types import RetailLocationResponse


class AppointmentLocationResponse(RetailLocationResponse):
    timezone: str
    status: LocationStatus
    coordinates: Coordinate | None
    description: str | None


class StaffSummaryResponse(BaseModel):
    id: str
    name: str
    available_at: list[RetailLocationResponse]


class StaffResponse(BaseModel):
    id: str
    name: str
    email: str | None
    phone: str | None
    locations: list[RetailLocationResponse]


# Option types (similar to FulfillmentOptionResponse)


class AppointmentOptionResponse(BaseModel):
    """An appointment option (e.g., different time slots or staff members)."""

    model_config = ConfigDict(
        extra="allow",
    )
    id: str = Field(description="Unique appointment option identifier")
    start_time: datetime = Field(description="Appointment start time")
    end_time: datetime | None = Field(
        default=None, description="Appointment end time"
    )
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
    end_time: datetime | None = Field(
        default=None, description="Appointment end time"
    )
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
    id: str = Field(
        description="Slot identifier for referencing in updates"
    )
    line_item_ids: list[str] = Field(
        description="Line item IDs included in this appointment slot"
    )
    location: RetailLocationResponse = Field(description="Location for the appointment slot")
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
    id: str | None = Field(
        default=None, description="Slot identifier for updates"
    )
    line_item_ids: list[str] = Field(
        description="Line item IDs included in this appointment slot"
    )
    location_id: str = Field(description="Location ID for the appointment")
    options: list[AppointmentOptionRequest] | None = Field(
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
