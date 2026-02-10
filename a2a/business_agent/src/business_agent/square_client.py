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

"""Square API client wrapper for service booking."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from square import Square
from square.environment import SquareEnvironment

from .models.appointment_types import (
    Address,
    AppointmentSegment,
    AvailabilitySlot,
    Booking,
    Coordinate,
    Customer,
    Location,
    LocationStatus,
    LocationSummary,
    ServiceVariation,
    StaffResponse,
    StaffStatus,
    StaffSummaryResponse,
)


def _fuzzy_match(query: str, text: str) -> bool:
    """Simple case-insensitive substring match."""
    return query.lower() in text.lower()


class SquareServiceClient:
    """Client for Square Bookings API operations."""

    def __init__(self, token: str, sandbox: bool = True):
        """Initialize the Square client.

        Args:
            token: Square API access token.
            sandbox: Whether to use sandbox environment (default True).
        """
        environment = (
            SquareEnvironment.SANDBOX if sandbox else SquareEnvironment.PRODUCTION
        )
        self._client = Square(token=token, environment=environment)
        self._location_cache: dict[str, Location] = {}
        self._staff_cache: dict[str, StaffSummaryResponse] = {}

    def list_locations(self, query: str | None = None) -> list[Location]:
        """List all available locations where services can be booked.

        Args:
            query: Optional fuzzy search on location name, address, or city.

        Returns:
            List of Location objects.
        """
        # only return active locations
        result = self._client.locations.list()
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        locations = []
        for loc in result.locations or []:
            if not loc.status == "ACTIVE":
                continue
            address_data = loc.address
            address = None
            if address_data:
                address = Address(
                    address_line_1=address_data.address_line1 or "",
                    address_line_2=address_data.address_line2,
                    city=address_data.locality or "",
                    state=address_data.administrative_district_level1 or "",
                    zip_code=address_data.postal_code,
                    country=address_data.country or "",
                )

            coords = loc.coordinates
            coordinates = None
            if coords:
                coordinates = Coordinate(
                    latitude=coords.latitude or 0,
                    longitude=coords.longitude or 0,
                )

            location = Location(
                id=loc.id,
                name=loc.name or "",
                address=address,
                timezone=loc.timezone or "UTC",
                status=LocationStatus.ACTIVE,
                coordinates=coordinates,
                description=loc.description,
            )
            locations.append(location)
            self._location_cache[loc.id] = location

        # Apply fuzzy filter if query provided; return all if no matches
        if query:
            filtered = [
                loc
                for loc in locations
                if _fuzzy_match(
                    query,
                    f"{loc.name} {loc.address.city if loc.address else ''} "
                    f"{loc.address.address_line_1 if loc.address else ''}",
                )
            ]
            return filtered if filtered else locations

        return locations

    def list_staff(self, query: str | None = None) -> list[StaffResponse]:
        """List all staff members who can provide services.

        Args:
            query: Optional fuzzy search on staff name or email.

        Returns:
            List of StaffResponse objects.
        """
        # First get all locations to map IDs to names
        locations_result = self._client.locations.list()
        if locations_result.errors:
            raise Exception(f"Square API error: {locations_result.errors}")

        location_map = {
            loc.id: loc.name or "" for loc in locations_result.locations or []
        }

        # Get team members using the team API
        result = self._client.team_members.search(
            query={"filter": {"status": "ACTIVE"}}
        )
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        staff_list = []
        for member in result.team_members or []:
            # Get assigned locations for this staff member
            assigned_locations = member.assigned_locations
            assigned_location_ids = (
                assigned_locations.location_ids if assigned_locations else []
            )
            locations = [
                LocationSummary(id=loc_id, name=location_map.get(loc_id, ""))
                for loc_id in (assigned_location_ids or [])
            ]

            staff = StaffResponse(
                id=member.id,
                first_name=member.given_name or "",
                last_name=member.family_name or "",
                email=member.email_address or "",
                phone=member.phone_number or "",
                status=StaffStatus.ACTIVE
                if member.status == "ACTIVE"
                else StaffStatus.INACTIVE,
                locations=locations,
            )
            staff_list.append(staff)

            # Cache staff summary
            self._staff_cache[member.id] = StaffSummaryResponse(
                id=member.id,
                name=f"{member.given_name or ''} {member.family_name or ''}".strip(),
                first_name=member.given_name or "",
                last_name=member.family_name or "",
                available_at=locations,
            )

        # Apply fuzzy filter if query provided; return all if no matches
        if query:
            filtered = [
                s
                for s in staff_list
                if _fuzzy_match(query, f"{s.first_name} {s.last_name} {s.email}")
            ]
            return filtered if filtered else staff_list

        return staff_list

    def list_service_variations(
        self, query: str | None = None
    ) -> list[ServiceVariation]:
        """List all available service variations that can be booked.

        Args:
            query: Optional fuzzy search on service or variation name.

        Returns:
            List of ServiceVariation objects.
        """
        # Search for appointment service items only
        result = self._client.catalog.search_items(
            product_types=["APPOINTMENTS_SERVICE"]
        )
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        variations = []
        for item in result.items or []:
            item_data = item.item_data
            if not item_data:
                continue

            service_name = item_data.name or ""

            for var in item_data.variations or []:
                var_data = var.item_variation_data
                if not var_data:
                    continue
                var_name = var_data.name or ""

                # Parse price
                price_money = var_data.price_money
                price = None
                display_price = "Price varies"
                if price_money:
                    amount = price_money.amount or 0
                    currency = price_money.currency or "USD"
                    price = amount / 100.0
                    display_price = (
                        f"${price:.2f}"
                        if currency == "USD"
                        else f"{price:.2f} {currency}"
                    )

                # Get duration from service variation
                service_duration = var_data.service_duration or 0
                duration_seconds = service_duration // 1000  # Convert from milliseconds

                variation = ServiceVariation(
                    id=var.id,
                    service_id=item.id,
                    name=f"{service_name} - {var_name}" if var_name else service_name,
                    description=item_data.description,
                    display_price=display_price,
                    price=price,
                    duration_seconds=duration_seconds,
                )
                variations.append(variation)

        # Apply fuzzy filter if query provided; return all if no matches
        if query:
            filtered = [v for v in variations if _fuzzy_match(query, v.name)]
            return filtered if filtered else variations

        return variations

    def search_availability(
        self,
        start_date: date,
        end_date: date,
        location_id: str | None = None,
        staff_id: str | None = None,
        service_variation_id: str | None = None,
    ) -> list[AvailabilitySlot]:
        """Search for available appointment slots within a date range.

        Args:
            start_date: Start date for the search range (inclusive).
            end_date: End date for the search range (inclusive).
            location_id: Filter by location.
            staff_id: Filter by staff member.
            service_variation_id: Filter by service variation.

        Returns:
            List of AvailabilitySlot objects.
        """
        # Build the search query
        start_at = datetime.combine(
            start_date, datetime.min.time(), tzinfo=timezone.utc
        ).isoformat()
        end_at = datetime.combine(
            end_date, datetime.max.time(), tzinfo=timezone.utc
        ).isoformat()

        query_filter: dict = {
            "start_at_range": {"start_at": start_at, "end_at": end_at},
        }

        if location_id:
            query_filter["location_id"] = location_id

        if staff_id:
            query_filter["segment_filters"] = [
                {"team_member_id_filter": {"any": [staff_id]}}
            ]

        if service_variation_id:
            if "segment_filters" not in query_filter:
                query_filter["segment_filters"] = [{}]
            query_filter["segment_filters"][0]["service_variation_id"] = (
                service_variation_id
            )

        result = self._client.bookings.search_availability(
            query={"filter": query_filter}
        )
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        # Get location and staff maps for enrichment
        locations_result = self._client.locations.list()
        location_map = {}
        if not locations_result.errors:
            location_map = {loc.id: loc for loc in locations_result.locations or []}

        team_result = self._client.team_members.search()
        staff_map = {}
        if not team_result.errors:
            staff_map = {m.id: m for m in team_result.team_members or []}

        slots = []
        for avail in result.availabilities or []:
            loc_id = avail.location_id or ""
            loc_data = location_map.get(loc_id)
            location_summary = LocationSummary(
                id=loc_id,
                name=loc_data.name if loc_data else "",
            )

            for segment in avail.appointment_segments or []:
                team_member_id = segment.team_member_id or ""
                staff_data = staff_map.get(team_member_id)
                staff_summary = StaffSummaryResponse(
                    id=team_member_id,
                    name=f"{staff_data.given_name or ''} {staff_data.family_name or ''}".strip()
                    if staff_data
                    else "",
                    first_name=staff_data.given_name if staff_data else "",
                    last_name=staff_data.family_name if staff_data else "",
                    available_at=[location_summary],
                )

                start_at_str = avail.start_at or ""
                slot = AvailabilitySlot(
                    start_time=datetime.fromisoformat(
                        start_at_str.replace("Z", "+00:00")
                    ),
                    end_time=datetime.fromisoformat(start_at_str.replace("Z", "+00:00"))
                    + timedelta(minutes=segment.duration_minutes or 0),
                    staff=staff_summary,
                    location=location_summary,
                )
                slots.append(slot)

        return slots

    def create_booking(
        self,
        location_id: str,
        start_time: datetime,
        service_variation_id: str,
        customer_first_name: str | None = None,
        customer_last_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        customer_notes: str | None = None,
        staff_id: str | None = None,
    ) -> Booking:
        """Create a new booking for a service at a specific location and time.

        Args:
            location_id: The location where the service will be provided.
            start_time: Start time for the appointment.
            service_variation_id: The service variation to book.
            customer_first_name: Customer's first name.
            customer_last_name: Customer's last name.
            customer_email: Customer's email address.
            customer_phone: Customer's phone number.
            customer_notes: Optional notes from the customer.
            staff_id: Optional specific staff member to book with.

        Returns:
            The created Booking object.
        """
        # Create or find customer
        customer_id = None
        if customer_email:
            # Search for existing customer
            search_result = self._client.customers.search(
                query={"filter": {"email_address": {"exact": customer_email}}}
            )
            if not search_result.errors and search_result.customers:
                customer_id = search_result.customers[0].id
            else:
                # Create new customer
                create_result = self._client.customers.create(
                    given_name=customer_first_name or "",
                    family_name=customer_last_name or "",
                    email_address=customer_email,
                    phone_number=customer_phone or "",
                )
                if create_result.errors:
                    raise Exception(
                        f"Failed to create customer: {create_result.errors}"
                    )
                customer_id = create_result.customer.id

        # Get service variation to determine duration and version
        catalog_result = self._client.catalog.object.get(
            object_id=service_variation_id, include_related_objects=True
        )
        duration_minutes = 60  # Default
        service_variation_version = None
        if not catalog_result.errors and catalog_result.object:
            service_variation_version = catalog_result.object.version
            var_data = catalog_result.object.item_variation_data
            if var_data:
                duration_ms = var_data.service_duration or 0
                if duration_ms:
                    duration_minutes = duration_ms // 60000  # Convert ms to minutes

        # If no staff_id provided, get an available team member
        team_member_id = staff_id
        if not team_member_id:
            # Get team members available at this location
            team_profiles = self._client.bookings.team_member_profiles.list(
                bookable_only=True, location_id=location_id
            )
            for profile in team_profiles.items:
                team_member_id = profile.team_member_id
                break

        if not team_member_id:
            raise Exception("No available team member found for this location")

        # Build appointment segment
        segment = {
            "service_variation_id": service_variation_id,
            "service_variation_version": service_variation_version,
            "duration_minutes": duration_minutes,
            "team_member_id": team_member_id,
        }

        # Create the booking
        start_at = (
            start_time.isoformat()
            if start_time.tzinfo
            else start_time.replace(tzinfo=timezone.utc).isoformat()
        )
        booking_dict: dict = {
            "location_id": location_id,
            "start_at": start_at,
            "appointment_segments": [segment],
        }

        if customer_id:
            booking_dict["customer_id"] = customer_id
        if customer_notes:
            booking_dict["customer_note"] = customer_notes

        result = self._client.bookings.create(
            idempotency_key=str(uuid.uuid4()),
            booking=booking_dict,
        )
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        return self._parse_booking(result.booking)

    def get_bookings(self, query: str | None = None) -> list[Booking]:
        """List bookings.

        Args:
            query: Optional fuzzy search on location name, service name,
                or staff name.

        Returns:
            List of Booking objects.
        """
        # Get all locations to search bookings across them
        locations_result = self._client.locations.list()
        if locations_result.errors:
            raise Exception(f"Square API error: {locations_result.errors}")

        all_bookings = []
        for loc in locations_result.locations or []:
            # List bookings for this location
            result = self._client.bookings.list(location_id=loc.id)

            for booking_data in result.items:
                booking = self._parse_booking(booking_data)
                all_bookings.append(booking)

        # Apply fuzzy filter if query provided; return all if no matches
        if query:

            def booking_searchable(b: Booking) -> str:
                parts = [b.location.name]
                for seg in b.segments:
                    parts.append(seg.service_variation.name)
                    parts.append(seg.staff.name)
                return " ".join(parts)

            filtered = [
                b for b in all_bookings if _fuzzy_match(query, booking_searchable(b))
            ]
            return filtered if filtered else all_bookings

        return all_bookings

    def cancel_booking(self, booking_id: str) -> str:
        """Cancel an existing booking.

        Args:
            booking_id: The ID of the booking to cancel.

        Returns:
            Confirmation message.
        """
        # First retrieve the booking to get its version
        retrieve_result = self._client.bookings.get(booking_id=booking_id)
        if retrieve_result.errors:
            raise Exception(f"Failed to retrieve booking: {retrieve_result.errors}")

        booking = retrieve_result.booking
        version = booking.version if booking else 0

        result = self._client.bookings.cancel(
            booking_id=booking_id, booking_version=version
        )
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        return f"Booking {booking_id} has been cancelled successfully."

    def _parse_booking(self, booking_data) -> Booking:
        """Parse a Square booking response into our Booking model."""
        # Get location details
        loc_id = booking_data.location_id or ""
        loc_result = self._client.locations.get(location_id=loc_id)
        loc = None
        if not loc_result.errors:
            loc = loc_result.location

        address_data = loc.address if loc else None
        address = None
        if address_data:
            address = Address(
                address_line_1=address_data.address_line1 or "",
                address_line_2=address_data.address_line2,
                city=address_data.locality or "",
                state=address_data.administrative_district_level1 or "",
                zip_code=address_data.postal_code,
                country=address_data.country or "",
            )

        coords = loc.coordinates if loc else None
        coordinates = None
        if coords:
            coordinates = Coordinate(
                latitude=coords.latitude or 0,
                longitude=coords.longitude or 0,
            )

        location = Location(
            id=loc_id,
            name=loc.name if loc else "",
            address=address,
            timezone=loc.timezone if loc else "UTC",
            status=LocationStatus.ACTIVE
            if loc and loc.status == "ACTIVE"
            else LocationStatus.INACTIVE,
            coordinates=coordinates,
            description=loc.description if loc else None,
        )

        # Get customer details
        customer_id = booking_data.customer_id or ""
        customer = None
        if customer_id:
            cust_result = self._client.customers.get(customer_id=customer_id)
            if not cust_result.errors and cust_result.customer:
                cust = cust_result.customer
                customer = Customer(
                    id=customer_id,
                    first_name=cust.given_name or "",
                    last_name=cust.family_name or "",
                    email=cust.email_address or "",
                    phone=cust.phone_number or "",
                )

        # Parse segments
        segments = []
        for seg in booking_data.appointment_segments or []:
            # Get service variation
            var_id = seg.service_variation_id or ""
            service_variation = ServiceVariation(
                id=var_id,
                service_id="",
                name="",
                description=None,
                display_price="",
                duration_seconds=(seg.duration_minutes or 0) * 60,
            )
            if var_id:
                cat_result = self._client.catalog.object.get(
                    object_id=var_id, include_related_objects=True
                )
                if not cat_result.errors and cat_result.object:
                    obj = cat_result.object
                    var_data = obj.item_variation_data
                    if var_data:
                        # Find parent item name
                        parent_id = var_data.item_id or ""
                        parent_name = ""
                        for related in cat_result.related_objects or []:
                            if related.id == parent_id and related.item_data:
                                parent_name = related.item_data.name or ""
                                break
                        var_name = var_data.name or ""
                        service_variation = ServiceVariation(
                            id=var_id,
                            service_id=parent_id,
                            name=f"{parent_name} - {var_name}"
                            if var_name
                            else parent_name,
                            description=None,
                            display_price="",
                            duration_seconds=(seg.duration_minutes or 0) * 60,
                        )

            # Get staff info
            team_member_id = seg.team_member_id or ""
            staff_summary = StaffSummaryResponse(
                id=team_member_id,
                name="",
                first_name="",
                last_name="",
                available_at=[],
            )
            if team_member_id:
                team_result = self._client.team_members.get(
                    team_member_id=team_member_id
                )
                if not team_result.errors and team_result.team_member:
                    member = team_result.team_member
                    staff_summary = StaffSummaryResponse(
                        id=team_member_id,
                        name=f"{member.given_name or ''} {member.family_name or ''}".strip(),
                        first_name=member.given_name or "",
                        last_name=member.family_name or "",
                        available_at=[LocationSummary(id=loc_id, name=location.name)],
                    )

            start_at = booking_data.start_at or ""
            start_time = (
                datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                if start_at
                else datetime.now(timezone.utc)
            )
            duration_minutes = seg.duration_minutes or 0

            segment = AppointmentSegment(
                id=str(uuid.uuid4()),
                service_variation=service_variation,
                staff=staff_summary,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=duration_minutes),
                location=LocationSummary(id=loc_id, name=location.name),
            )
            segments.append(segment)

        start_at = booking_data.start_at or ""
        total_duration = sum(
            (seg.duration_minutes or 0)
            for seg in booking_data.appointment_segments or []
        )

        return Booking(
            id=booking_data.id,
            location=location,
            customer=customer,
            start_time=datetime.fromisoformat(start_at.replace("Z", "+00:00"))
            if start_at
            else datetime.now(timezone.utc),
            duration_minutes=total_duration,
            segments=segments,
            customer_notes=booking_data.customer_note,
            seller_notes=booking_data.seller_note,
        )

    def get_service_variation(self, service_variation_id: str) -> ServiceVariation:
        """Get a single service variation by ID.

        Args:
            service_variation_id: The ID of the service variation.

        Returns:
            The ServiceVariation object.
        """
        cat_result = self._client.catalog.object.get(
            object_id=service_variation_id, include_related_objects=True
        )
        if cat_result.errors:
            raise Exception(f"Square API error: {cat_result.errors}")

        obj = cat_result.object
        if not obj:
            raise Exception(f"Service variation {service_variation_id} not found")

        var_data = obj.item_variation_data
        if not var_data:
            raise Exception(f"Invalid service variation {service_variation_id}")

        # Find parent item name
        parent_id = var_data.item_id or ""
        parent_name = ""
        description = None
        for related in cat_result.related_objects or []:
            if related.id == parent_id and related.item_data:
                parent_name = related.item_data.name or ""
                description = related.item_data.description
                break

        var_name = var_data.name or ""

        # Parse price
        price_money = var_data.price_money
        price = None
        display_price = "Price varies"
        if price_money:
            amount = price_money.amount or 0
            currency = price_money.currency or "USD"
            price = amount / 100.0
            display_price = (
                f"${price:.2f}" if currency == "USD" else f"{price:.2f} {currency}"
            )

        # Get duration
        service_duration = var_data.service_duration or 0
        duration_seconds = service_duration // 1000

        return ServiceVariation(
            id=service_variation_id,
            service_id=parent_id,
            name=f"{parent_name} - {var_name}" if var_name else parent_name,
            description=description,
            display_price=display_price,
            price=price,
            duration_seconds=duration_seconds,
        )

    def get_location(self, location_id: str) -> Location:
        """Get a single location by ID.

        Args:
            location_id: The ID of the location.

        Returns:
            The Location object.
        """
        if location_id in self._location_cache:
            return self._location_cache[location_id]

        result = self._client.locations.get(location_id=location_id)
        if result.errors:
            raise Exception(f"Square API error: {result.errors}")

        loc = result.location
        if not loc:
            raise Exception(f"Location {location_id} not found")

        address_data = loc.address
        address = None
        if address_data:
            address = Address(
                address_line_1=address_data.address_line1 or "",
                address_line_2=address_data.address_line2,
                city=address_data.locality or "",
                state=address_data.administrative_district_level1 or "",
                zip_code=address_data.postal_code,
                country=address_data.country or "",
            )

        coords = loc.coordinates
        coordinates = None
        if coords:
            coordinates = Coordinate(
                latitude=coords.latitude or 0,
                longitude=coords.longitude or 0,
            )

        location = Location(
            id=loc.id,
            name=loc.name or "",
            address=address,
            timezone=loc.timezone or "UTC",
            status=LocationStatus.ACTIVE
            if loc.status == "ACTIVE"
            else LocationStatus.INACTIVE,
            coordinates=coordinates,
            description=loc.description,
        )
        self._location_cache[location_id] = location
        return location
