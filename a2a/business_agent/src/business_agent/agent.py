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

"""Service booking agent with Square backend integration."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from a2a.types import TaskState
from a2a.utils import get_message_text
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from ucp_sdk.models.schemas.shopping.types.buyer import Buyer

from .a2a_extensions import UcpExtension
from .constants import (
    ADK_EXTENSIONS_STATE_KEY,
    ADK_LATEST_TOOL_RESULT,
    ADK_PAYMENT_STATE,
    ADK_UCP_METADATA_STATE,
    ADK_USER_CHECKOUT_ID,
    UCP_CHECKOUT_KEY,
    UCP_PAYMENT_DATA_KEY,
    UCP_RISK_SIGNALS_KEY,
)
from .models.appointment_types import AppointmentRequest
from .payment_processor import MockPaymentProcessor
from .store import ServiceStore


store = ServiceStore()
mpp = MockPaymentProcessor()


def _create_error_response(message: str) -> dict:
    return {"message": message, "status": "error"}


# ---------- Service Catalog Tools ----------


def search_shopping_catalog(tool_context: ToolContext, query: str) -> dict:
    """Search the service catalog for services that match the given query.

    Args:
        tool_context: The tool context for the current request.
        query: Query for performing service search.

    Returns:
        dict: Returns the response from the tool with service results.
    """
    try:
        services = store.search_services(query)
        return {"a2a.service_results": [s.model_dump(mode="json") for s in services]}
    except Exception:
        logging.exception("There was an error searching the service catalog.")
        return _create_error_response(
            "Sorry, there was an error searching the service catalog, "
            "please try again later."
        )


# ---------- Location and Staff Tools ----------


def list_locations(tool_context: ToolContext, query: str | None = None) -> dict:
    """List available locations where services can be booked.

    Args:
        tool_context: The tool context for the current request.
        query: Optional search query to filter locations by name or address.

    Returns:
        dict: Returns list of locations.
    """
    try:
        locations = store.list_locations(query)
        return {"a2a.locations": [loc.model_dump(mode="json") for loc in locations]}
    except Exception:
        logging.exception("There was an error listing locations.")
        return _create_error_response(
            "Sorry, there was an error listing locations, please try again later."
        )


def list_staff(tool_context: ToolContext, query: str | None = None) -> dict:
    """List available staff members who can provide services.

    Args:
        tool_context: The tool context for the current request.
        query: Optional search query to filter staff by name.

    Returns:
        dict: Returns list of staff members.
    """
    try:
        staff = store.list_staff(query)
        return {"a2a.staff": [s.model_dump(mode="json") for s in staff]}
    except Exception:
        logging.exception("There was an error listing staff.")
        return _create_error_response(
            "Sorry, there was an error listing staff, please try again later."
        )


# ---------- Availability Tool ----------


def search_availability(
    tool_context: ToolContext,
    start_date: str,
    end_date: str,
    location_id: str | None = None,
    staff_id: str | None = None,
    service_variation_id: str | None = None,
) -> dict:
    """Search for available appointment slots within a date range.

    Args:
        tool_context: The tool context for the current request.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        location_id: Optional location ID to filter by.
        staff_id: Optional staff ID to filter by.
        service_variation_id: Optional service variation ID to filter by.

    Returns:
        dict: Returns list of available time slots.
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        slots = store.search_availability(
            start_date=start,
            end_date=end,
            location_id=location_id,
            staff_id=staff_id,
            service_variation_id=service_variation_id,
        )
        return {"a2a.availability_slots": [s.model_dump(mode="json") for s in slots]}
    except Exception:
        logging.exception("There was an error searching availability.")
        return _create_error_response(
            "Sorry, there was an error searching availability, please try again later."
        )


# ---------- Checkout Tools ----------


def add_to_checkout(
    tool_context: ToolContext,
    service_variation_id: str,
    quantity: int = 1,
    location_id: str | None = None,
    staff_id: str | None = None,
    start_time: str | None = None,
    notes: str | None = None,
) -> dict:
    """Add a service to the checkout session with optional appointment details.

    Args:
        tool_context: The tool context for the current request.
        service_variation_id: Service variation ID to add.
        quantity: Quantity (default 1).
        location_id: Optional location ID for the appointment.
        staff_id: Optional staff ID for the appointment.
        start_time: Optional start time in ISO 8601 format (e.g., 2024-01-15T10:00:00Z).
        notes: Optional notes for the appointment.

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)
    ucp_metadata = tool_context.state.get(ADK_UCP_METADATA_STATE)

    if not ucp_metadata:
        return _create_error_response("There was an error creating UCP metadata")

    try:
        # Parse start_time if provided
        parsed_start_time = None
        if start_time:
            parsed_start_time = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )

        checkout = store.add_to_checkout(
            metadata=ucp_metadata,
            service_variation_id=service_variation_id,
            quantity=quantity,
            checkout_id=checkout_id,
            location_id=location_id,
            staff_id=staff_id,
            start_time=parsed_start_time,
            notes=notes,
        )

        if not checkout_id:
            tool_context.state[ADK_USER_CHECKOUT_ID] = checkout.id

        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
        }
    except ValueError:
        logging.exception(
            "There was an error adding item to checkout, please retry later."
        )
        return _create_error_response(
            "There was an error adding item to checkout, please retry later."
        )


def remove_from_checkout(tool_context: ToolContext, line_item_id: str) -> dict:
    """Remove a service and its appointment slot from the checkout session.

    Args:
        tool_context: The tool context for the current request.
        line_item_id: Line item ID to remove.

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    try:
        checkout = store.remove_from_checkout(checkout_id, line_item_id)
        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
        }
    except ValueError:
        logging.exception(
            "There was an error removing item from checkout, please retry later."
        )
        return _create_error_response(
            "There was an error removing item from checkout, please retry later."
        )


def update_checkout(
    tool_context: ToolContext,
    line_item_id: str,
    quantity: int | None = None,
    location_id: str | None = None,
    staff_id: str | None = None,
    start_time: str | None = None,
    notes: str | None = None,
) -> dict:
    """Update a line item's quantity and/or appointment details.

    Args:
        tool_context: The tool context for the current request.
        line_item_id: Line item ID to update.
        quantity: New quantity (optional).
        location_id: New location ID for the appointment (optional).
        staff_id: New staff ID for the appointment (optional).
        start_time: New start time in ISO 8601 format (optional).
        notes: New notes for the appointment (optional).

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    try:
        # Parse start_time if provided
        parsed_start_time = None
        if start_time:
            parsed_start_time = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )

        checkout = store.update_checkout(
            checkout_id=checkout_id,
            line_item_id=line_item_id,
            quantity=quantity,
            location_id=location_id,
            staff_id=staff_id,
            start_time=parsed_start_time,
            notes=notes,
        )
        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
        }
    except ValueError:
        logging.exception(
            "There was an error updating the checkout, please retry later."
        )
        return _create_error_response(
            "There was an error updating the checkout, please retry later."
        )


def set_appointment(
    tool_context: ToolContext,
    slots: list[dict],
) -> dict:
    """Set appointment details for multiple line items at once.

    Args:
        tool_context: The tool context for the current request.
        slots: List of appointment slot configurations. Each slot should have:
            - line_item_ids: List of line item IDs this slot applies to
            - location_id: Location ID for the appointment
            - start_time: Start time in ISO 8601 format
            - staff_id: Optional staff member ID
            - notes: Optional customer notes

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    try:
        # Parse slots into AppointmentRequest
        from .models.appointment_types import AppointmentSlotRequest

        parsed_slots = []
        for slot_data in slots:
            start_time_str = slot_data.get("start_time", "")
            parsed_start_time = datetime.fromisoformat(
                start_time_str.replace("Z", "+00:00")
            )
            parsed_slots.append(
                AppointmentSlotRequest(
                    id=slot_data.get("id"),
                    line_item_ids=slot_data.get("line_item_ids", []),
                    location_id=slot_data.get("location_id", ""),
                    staff_id=slot_data.get("staff_id"),
                    start_time=parsed_start_time,
                    notes=slot_data.get("notes"),
                )
            )

        appointment = AppointmentRequest(slots=parsed_slots)
        checkout = store.set_appointment(checkout_id, appointment)

        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
        }
    except ValueError:
        logging.exception(
            "There was an error setting appointment details, please retry later."
        )
        return _create_error_response(
            "There was an error setting appointment details, please retry later."
        )


def get_checkout(tool_context: ToolContext) -> dict:
    """Retrieve the current checkout session.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    checkout = store.get_checkout(checkout_id)
    if checkout is None:
        return _create_error_response("Checkout not found with the given ID.")

    return {
        UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
        "status": "success",
    }


def update_customer_details(
    tool_context: ToolContext,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
) -> dict:
    """Update customer details for the checkout.

    Args:
        tool_context: The tool context for the current request.
        email: Customer email address.
        first_name: Customer first name.
        last_name: Customer last name.
        phone: Customer phone number.

    Returns:
        dict: Returns the checkout response.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    checkout = store.get_checkout(checkout_id)
    if checkout is None:
        return _create_error_response("Checkout not found with the given ID.")

    # Store customer info for booking creation
    checkout.buyer = Buyer(email=email)

    # Store additional customer info in state for later use
    tool_context.state["customer_first_name"] = first_name
    tool_context.state["customer_last_name"] = last_name
    tool_context.state["customer_phone"] = phone
    tool_context.state["customer_email"] = email

    return start_payment(tool_context)


def start_payment(tool_context: ToolContext) -> dict:
    """Ask for required information to proceed with the payment.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Checkout object or error message.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    result = store.start_payment(checkout_id)
    if isinstance(result, str):
        return {"message": result, "status": "requires_more_info"}
    else:
        tool_context.actions.skip_summarization = True
        return {
            UCP_CHECKOUT_KEY: result.model_dump(mode="json"),
            "status": "success",
        }


async def complete_checkout(tool_context: ToolContext) -> dict:
    """Process the payment and create bookings to complete checkout.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Returns the checkout response with order confirmation.
    """
    checkout_id = _get_current_checkout_id(tool_context)

    if not checkout_id:
        return _create_error_response("A Checkout has not yet been created.")

    checkout = store.get_checkout(checkout_id)

    if checkout is None:
        return _create_error_response("Checkout not found for the current session.")

    payment_data: dict[str, Any] = tool_context.state.get(ADK_PAYMENT_STATE)

    if payment_data is None:
        return {
            "message": (
                "Payment Data is missing. Click 'Confirm Purchase' "
                "to complete the purchase."
            ),
            "status": "requires_more_info",
        }

    try:
        task = mpp.process_payment(
            payment_data[UCP_PAYMENT_DATA_KEY],
            payment_data[UCP_RISK_SIGNALS_KEY],
        )

        if task is None:
            return _create_error_response("Failed to receive a valid response from MPP")

        if task.status is not None and task.status.state == TaskState.completed:
            payment_instrument = payment_data.get(UCP_PAYMENT_DATA_KEY)
            checkout.payment.selected_instrument_id = payment_instrument.root.id
            checkout.payment.instruments = [payment_instrument]

            # Get customer info from state
            customer_email = tool_context.state.get("customer_email")
            customer_first_name = tool_context.state.get("customer_first_name")
            customer_last_name = tool_context.state.get("customer_last_name")
            customer_phone = tool_context.state.get("customer_phone")

            response = store.place_order(
                checkout_id,
                customer_email=customer_email,
                customer_first_name=customer_first_name,
                customer_last_name=customer_last_name,
                customer_phone=customer_phone,
            )

            # Clear completed checkout from state
            tool_context.state[ADK_USER_CHECKOUT_ID] = None

            return {
                UCP_CHECKOUT_KEY: response.model_dump(mode="json"),
                "status": "success",
            }
        else:
            return _create_error_response(
                get_message_text(task.status.message)  # type: ignore
            )
    except Exception:
        logging.exception("There was an error completing the checkout.")
        return _create_error_response(
            "Sorry, there was an error completing the checkout, please try again."
        )


# ---------- Booking Management Tools ----------


def get_bookings(tool_context: ToolContext, query: str | None = None) -> dict:
    """Get existing bookings.

    Args:
        tool_context: The tool context for the current request.
        query: Optional search query to filter bookings.

    Returns:
        dict: Returns list of bookings.
    """
    try:
        bookings = store.get_bookings(query)
        return {"a2a.bookings": [b.model_dump(mode="json") for b in bookings]}
    except Exception:
        logging.exception("There was an error getting bookings.")
        return _create_error_response(
            "Sorry, there was an error getting bookings, please try again later."
        )


def cancel_booking(tool_context: ToolContext, booking_id: str) -> dict:
    """Cancel an existing booking.

    Args:
        tool_context: The tool context for the current request.
        booking_id: The ID of the booking to cancel.

    Returns:
        dict: Returns confirmation message.
    """
    try:
        result = store.cancel_booking(booking_id)
        return {"message": result, "status": "success"}
    except Exception:
        logging.exception("There was an error cancelling the booking.")
        return _create_error_response(
            "Sorry, there was an error cancelling the booking, please try again later."
        )


# ---------- Helper Functions ----------


def _get_current_checkout_id(tool_context: ToolContext) -> str | None:
    """Return the current checkout ID from the tool context state."""
    return tool_context.state.get(ADK_USER_CHECKOUT_ID)


def after_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    """Modify the tool response before returning to the agent."""
    extensions = tool_context.state.get(ADK_EXTENSIONS_STATE_KEY, [])
    # Add typed data responses to the state
    ucp_response_keys = [
        UCP_CHECKOUT_KEY,
        "a2a.service_results",
        "a2a.locations",
        "a2a.staff",
        "a2a.availability_slots",
        "a2a.bookings",
    ]
    if UcpExtension.URI in extensions and any(
        key in tool_response for key in ucp_response_keys
    ):
        tool_context.state[ADK_LATEST_TOOL_RESULT] = tool_response

    return None


def modify_output_after_agent(
    callback_context: CallbackContext,
) -> types.Content | None:
    """Modify the agent's output before returning to the user."""
    latest_result = callback_context.state.get(ADK_LATEST_TOOL_RESULT)
    if latest_result:
        return types.Content(
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        response={"result": latest_result}
                    )
                )
            ],
            role="model",
        )

    return None


# ---------- Agent Definition ----------


root_agent = Agent(
    name="service_booking_agent",
    model="gemini-3-flash-preview",
    description="Agent to help with service booking and appointments",
    instruction=(
        "You are a helpful agent for booking services and appointments. "
        "You can help users with:\n"
        "- Searching for available services\n"
        "- Finding locations where services are offered\n"
        "- Checking staff availability\n"
        "- Finding available appointment times\n"
        "- Adding services to a checkout with appointment details\n"
        "- Managing and modifying bookings\n\n"
        "Workflow for booking a service:\n"
        "1. Search for services the user wants (search_shopping_catalog)\n"
        "2. List available locations (list_locations)\n"
        "3. Check availability for the desired date range (search_availability)\n"
        "4. Add the service to checkout with appointment details (add_to_checkout)\n"
        "5. Collect customer details (update_customer_details)\n"
        "6. Complete the checkout to confirm the booking (complete_checkout)\n\n"
        "When adding services to checkout, you can include appointment details "
        "(location_id, staff_id, start_time) directly in add_to_checkout, or "
        "use set_appointment later to schedule appointments for multiple services.\n\n"
        "Always confirm service details, location, and time with the user before "
        "completing the booking. If the user wants to see their existing bookings "
        "or cancel a booking, use get_bookings and cancel_booking."
    ),
    tools=[
        # Catalog
        search_shopping_catalog,
        # Locations and staff
        list_locations,
        list_staff,
        # Availability
        search_availability,
        # Checkout
        add_to_checkout,
        remove_from_checkout,
        update_checkout,
        set_appointment,
        get_checkout,
        # Customer and payment
        update_customer_details,
        start_payment,
        complete_checkout,
        # Booking management
        get_bookings,
        cancel_booking,
    ],
    after_tool_callback=after_tool_modifier,
    after_agent_callback=modify_output_after_agent,
)
