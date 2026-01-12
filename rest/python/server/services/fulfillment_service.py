#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Fulfillment service for calculating delivery options.

This module encapsulates the logic for determining available fulfillment methods
and costs based on the provided shipping address.
"""

import db
from sqlalchemy.ext.asyncio import AsyncSession
from ucp_sdk.models.schemas.shopping.fulfillment_resp import FulfillmentOption
from ucp_sdk.models.schemas.shopping.types.fulfillment_option_resp import (
  FulfillmentOptionResponse,
)
from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
from ucp_sdk.models.schemas.shopping.types.total_resp import TotalResponse


class FulfillmentService:
  """Service for handling fulfillment logic."""

  async def calculate_options(
    self,
    session: AsyncSession,
    address: PostalAddress,
    promotions: list[db.Promotion] | None = None,
    subtotal: int = 0,
    line_item_ids: list[str] | None = None,
  ) -> list[FulfillmentOption]:
    """Calculate available fulfillment options based on the address.

    Args:
      session: The database session to fetch rates from.
      address: The shipping address.
      promotions: Optional list of active promotions.
      subtotal: The order subtotal in cents.
      line_item_ids: List of product IDs in the order.

    Returns:
      A list of FulfillmentOption objects.

    """
    if not address or not address.address_country:
      return []

    promotions = promotions or []
    line_item_ids = line_item_ids or []

    # Check for free shipping
    is_free_shipping = False
    for promo in promotions:
      if promo.type == "free_shipping":
        if promo.min_subtotal and subtotal >= promo.min_subtotal:
          is_free_shipping = True
          break

        if promo.eligible_item_ids and any(
          item_id in promo.eligible_item_ids for item_id in line_item_ids
        ):
          is_free_shipping = True
          break

    # Fetch rates from DB
    db_rates = await db.get_shipping_rates(session, address.address_country)

    # Also fetch default rates if not already covered (though helper does
    # partial match, exact country match should take precedence if we had
    # duplicates but here we just return all matching)

    options = []

    # Simple logic: Deduplicate by service level, preferring specific country
    # match. Group by service_level

    rates_by_level = {}
    for rate in db_rates:
      # If we already have a rate for this level, check if the new one is more
      # specific (country match)
      # "default" is less specific than "US"
      if rate.service_level not in rates_by_level:
        rates_by_level[rate.service_level] = rate
      else:
        existing = rates_by_level[rate.service_level]
        if (
          existing.country_code == "default" and rate.country_code != "default"
        ):
          rates_by_level[rate.service_level] = rate

    # Sort for deterministic output
    sorted_rates = sorted(rates_by_level.values(), key=lambda r: r.price)
    for rate in sorted_rates:
      price = rate.price
      title = rate.title

      if is_free_shipping and rate.service_level == "standard":
        price = 0
        title += " (Free)"

      options.append(
        FulfillmentOption(
          root=FulfillmentOptionResponse(
            id=rate.id,
            title=title,
            totals=[
              TotalResponse(type="subtotal", amount=price),
              TotalResponse(type="total", amount=price),
            ],
          )
        )
      )

    return options
