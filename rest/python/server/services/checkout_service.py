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

"""Checkout service for managing the lifecycle of checkout sessions.

This module provides the `CheckoutService` class, which encapsulates the
business logic
for creating, retrieving, updating, and completing checkout sessions. It handles
integration with the persistence layer, fulfillment calculation, payment
processing,
and inventory validation.

Key responsibilities include:
- Creating and managing checkout sessions with idempotency support.
- Calculating checkout totals, including line items, shipping, and discounts.
- Validating inventory availability.
- Processing payments via various handlers (e.g., Google Pay, Shop Pay, Mock).
- Transforming checkout sessions into completed orders.
- Supporting hierarchical fulfillment configuration.
"""

import datetime
import hashlib
import json
import logging
from typing import Any
import uuid

import config
import db
from enums import CheckoutStatus
from exceptions import CheckoutNotModifiableError
from exceptions import IdempotencyConflictError
from exceptions import InvalidRequestError
from exceptions import OutOfStockError
from exceptions import PaymentFailedError
from exceptions import ResourceNotFoundError
import httpx
from models import UnifiedCheckout as Checkout
from models import UnifiedCheckoutCreateRequest
from models import UnifiedCheckoutUpdateRequest
from pydantic import AnyUrl
from pydantic import BaseModel
from services.fulfillment_service import FulfillmentService
from sqlalchemy.ext.asyncio import AsyncSession
from ucp_sdk.models._internal import Response
from ucp_sdk.models._internal import ResponseCheckout
from ucp_sdk.models._internal import ResponseOrder
from ucp_sdk.models._internal import Version
from ucp_sdk.models.schemas.shopping.ap2_mandate import Ap2CompleteRequest
from ucp_sdk.models.schemas.shopping.discount_resp import Allocation
from ucp_sdk.models.schemas.shopping.discount_resp import AppliedDiscount
from ucp_sdk.models.schemas.shopping.discount_resp import DiscountsObject
from ucp_sdk.models.schemas.shopping.fulfillment_resp import (
  Fulfillment as FulfillmentResp,
)
from ucp_sdk.models.schemas.shopping.order import (
  Fulfillment as OrderFulfillment,
)
from ucp_sdk.models.schemas.shopping.order import Order
from ucp_sdk.models.schemas.shopping.order import PlatformConfig
from ucp_sdk.models.schemas.shopping.payment_create_req import (
  PaymentCreateRequest,
)
from ucp_sdk.models.schemas.shopping.payment_resp import PaymentResponse
from ucp_sdk.models.schemas.shopping.types import order_line_item
from ucp_sdk.models.schemas.shopping.types import total_resp
from ucp_sdk.models.schemas.shopping.types.card_credential import CardCredential
from ucp_sdk.models.schemas.shopping.types.expectation import Expectation
from ucp_sdk.models.schemas.shopping.types.expectation import (
  LineItem as ExpectationLineItem,
)
from ucp_sdk.models.schemas.shopping.types.fulfillment_destination_resp import (
  FulfillmentDestinationResponse,
)
from ucp_sdk.models.schemas.shopping.types.fulfillment_group_resp import (
  FulfillmentGroupResponse,
)
from ucp_sdk.models.schemas.shopping.types.fulfillment_method_resp import (
  FulfillmentMethodResponse,
)
from ucp_sdk.models.schemas.shopping.types.fulfillment_resp import (
  FulfillmentResponse,
)
from ucp_sdk.models.schemas.shopping.types.item_resp import ItemResponse
from ucp_sdk.models.schemas.shopping.types.line_item_resp import (
  LineItemResponse,
)
from ucp_sdk.models.schemas.shopping.types.order_confirmation import (
  OrderConfirmation,
)
from ucp_sdk.models.schemas.shopping.types.order_line_item import OrderLineItem
from ucp_sdk.models.schemas.shopping.types.postal_address import PostalAddress
from ucp_sdk.models.schemas.shopping.types.shipping_destination_resp import (
  ShippingDestinationResponse,
)
from ucp_sdk.models.schemas.shopping.types.token_credential_resp import (
  TokenCredentialResponse,
)
from ucp_sdk.models.schemas.shopping.types.total_resp import (
  TotalResponse as Total,
)

logger = logging.getLogger(__name__)


class CheckoutService:
  """Service for managing checkout sessions and orders."""

  def __init__(
    self,
    fulfillment_service: FulfillmentService,
    products_session: AsyncSession,
    transactions_session: AsyncSession,
    base_url: str,
  ):
    """Initialize CheckoutService."""
    self.fulfillment_service = fulfillment_service
    self.products_session = products_session
    self.transactions_session = transactions_session
    self.base_url = base_url.rstrip("/")

  def _compute_hash(self, data: Any) -> str:
    """Compute SHA256 hash of the JSON-serialized data."""
    if isinstance(data, BaseModel):
      # Pydantic's optimized JSON dump
      # sort_keys is not supported in model_dump_json in Pydantic V2.
      # We dump to dict and use standard json.dumps for deterministic sorting.
      json_str = json.dumps(data.model_dump(mode="json"), sort_keys=True)
    else:
      # sort_keys=True ensures deterministic hashing for dicts
      json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

  async def create_checkout(
    self,
    checkout_req: UnifiedCheckoutCreateRequest,
    idempotency_key: str,
    platform_config: PlatformConfig | None = None,
  ) -> Checkout:
    """Create a new checkout session."""
    logger.info("Creating checkout session")

    # Idempotency Check
    request_hash = self._compute_hash(checkout_req)
    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )

    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      # Return cached response
      return Checkout(**existing_record.response_body)

    # Initialize full model from request
    checkout_id = getattr(checkout_req, "id", None) or str(uuid.uuid4())

    # Map line items
    line_items = []
    for li_req in checkout_req.line_items:
      line_items.append(
        LineItemResponse(
          id=str(uuid.uuid4()),
          item=ItemResponse(
            id=li_req.item.id,
            title=li_req.item.title,
            price=0,  # Will be set by recalculate_totals
          ),
          quantity=li_req.quantity,
          totals=[],
        )
      )

    # We exclude fields that the service explicitly manages or overrides to
    # avoid keyword argument conflicts when constructing the response model.
    # By excluding only these 'base' fields, we allow extension fields (like
    # 'buyer' or 'discounts') to pass through dynamically via **checkout_data.
    #
    # * Conflict Prevention: If we didn't exclude currency, id, or payment,
    #   passing them via **checkout_data while also specifying them as keyword
    #   arguments (e.g., currency=checkout_req.currency) would raise a
    #   TypeError: multiple values for keyword argument.
    # * Server Authority: Fields like status, totals, and links might be
    #   present in a client request (even if they shouldn't be), but the server
    #   is the source of truth. We exclude them from the dumped data to ensure
    #   we start with a "clean" calculated state (e.g.,
    #   status=CheckoutStatus.IN_PROGRESS, totals=[]).
    # * Model Transformation: ucp in the request is usually just version
    #   negotiation info, but in the response, it's a complex ResponseCheckout
    #   object with capability metadata. We exclude the request version to
    #   inject the full response object.
    checkout_data = checkout_req.model_dump(
      exclude={
        "line_items",
        "payment",
        "ucp",
        "currency",
        "id",
        "status",
        "totals",
        "links",
        "fulfillment",
      }
    )

    # Initialize fulfillment response
    fulfillment_resp = None
    if checkout_req.fulfillment:
      req_fulfillment = checkout_req.fulfillment.root
      resp_methods = []
      all_li_ids = [li.id for li in line_items]

      if req_fulfillment.methods:
        for method_req in req_fulfillment.methods:
          # Create Method Response
          method_id = getattr(method_req, "id", None) or str(uuid.uuid4())
          method_li_ids = (
            getattr(method_req, "line_item_ids", None) or all_li_ids
          )
          method_type = getattr(method_req, "type", "shipping")

          resp_groups = []
          if method_req.groups:
            for group_req in method_req.groups:
              group_id = (
                getattr(group_req, "id", None) or f"group_{uuid.uuid4()}"
              )
              group_li_ids = (
                getattr(group_req, "line_item_ids", None) or all_li_ids
              )

              resp_groups.append(
                FulfillmentGroupResponse(
                  id=group_id,
                  line_item_ids=group_li_ids,
                  selected_option_id=getattr(
                    group_req, "selected_option_id", None
                  ),
                )
              )

          # Convert destinations if present (usually empty on create, but
          # handled for completeness)
          resp_destinations = []
          if method_req.destinations:
            for dest_req in method_req.destinations:
              # Assuming ShippingDestinationRequest can map to Response
              # structure or needs conversion. For create, we typically accept
              # ShippingDestinationRequest inside
              # FulfillmentMethodCreateRequest. We need to convert it to
              # FulfillmentDestinationResponse.
              # The request model structure is complex
              # (FulfillmentDestinationRequest -> ShippingDestinationRequest)
              # The response model is FulfillmentDestinationResponse ->
              # ShippingDestinationResponse

              # Extract the inner ShippingDestinationRequest
              inner_dest = dest_req.root

              resp_destinations.append(
                FulfillmentDestinationResponse(
                  root=ShippingDestinationResponse(
                    id=getattr(inner_dest, "id", None) or str(uuid.uuid4()),
                    address_country=inner_dest.address_country,
                    postal_code=inner_dest.postal_code,
                    address_region=inner_dest.address_region,
                    address_locality=inner_dest.address_locality,
                    street_address=inner_dest.street_address,
                  )
                )
              )

          resp_methods.append(
            FulfillmentMethodResponse(
              id=method_id,
              type=method_type,
              line_item_ids=method_li_ids,
              groups=resp_groups or None,
              destinations=resp_destinations or None,
              selected_destination_id=getattr(
                method_req, "selected_destination_id", None
              ),
            )
          )

      fulfillment_resp = FulfillmentResp(
        root=FulfillmentResponse(methods=resp_methods)
      )

    checkout = Checkout(
      ucp=ResponseCheckout(
        version=Version(config.get_server_version()),
        capabilities=[
          Response(
            name="dev.ucp.shopping.checkout",
            version=Version(config.get_server_version()),
          )
        ],
      ),
      id=checkout_id,
      status=CheckoutStatus.IN_PROGRESS,
      currency=checkout_req.currency,
      line_items=line_items,
      totals=[],
      links=[],
      payment=PaymentResponse(
        handlers=[],
        selected_instrument_id=checkout_req.payment.selected_instrument_id,
        instruments=checkout_req.payment.instruments,
      ),
      platform=platform_config,
      fulfillment=fulfillment_resp,
      **checkout_data,
    )

    # Validate inventory and recalculate totals (Server is authority)
    await self._recalculate_totals(checkout)
    await self._validate_inventory(checkout)

    checkout.status = CheckoutStatus.READY_FOR_COMPLETE

    response_body = checkout.model_dump(mode="json", by_alias=True)

    # Persist checkout to Transactions DB
    await db.save_checkout(
      self.transactions_session,
      checkout.id,
      checkout.status,
      response_body,
    )

    # Save Idempotency Record
    await db.save_idempotency_record(
      self.transactions_session,
      idempotency_key,
      request_hash,
      201,  # Created
      response_body,
    )

    await self.transactions_session.commit()

    return checkout

  async def get_checkout(
    self,
    checkout_id: str,
  ) -> Checkout:
    """Retrieve a checkout session."""
    # Log the request
    await db.log_request(
      self.transactions_session,
      method="GET",
      url=f"/checkout-sessions/{checkout_id}",
      checkout_id=checkout_id,
    )
    await self.transactions_session.commit()

    return await self._get_and_validate_checkout(checkout_id)

  async def update_checkout(
    self,
    checkout_id: str,
    checkout_req: UnifiedCheckoutUpdateRequest,
    idempotency_key: str,
    platform_config: PlatformConfig | None = None,
  ) -> Checkout:
    """Update a checkout session."""
    logger.info("Updating checkout session %s", checkout_id)

    # Idempotency Check
    request_hash = self._compute_hash(checkout_req)

    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )
    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Checkout(**existing_record.response_body)

    # Log the request
    payload_dict = checkout_req.model_dump(mode="json")
    await db.log_request(
      self.transactions_session,
      method="PUT",
      url=f"/checkout-sessions/{checkout_id}",
      checkout_id=checkout_id,
      payload=payload_dict,
    )

    existing = await self._get_and_validate_checkout(checkout_id)
    self._ensure_modifiable(existing, "update")

    # Update existing with request data
    # This is a partial update logic
    if checkout_req.line_items:
      line_items = []
      for li_req in checkout_req.line_items:
        line_items.append(
          LineItemResponse(
            id=li_req.id or str(uuid.uuid4()),
            item=ItemResponse(
              id=li_req.item.id,
              title=li_req.item.title,
              price=0,
            ),
            quantity=li_req.quantity,
            totals=[],
            parent_id=li_req.parent_id,
          )
        )
      existing.line_items = line_items

    if checkout_req.currency:
      existing.currency = checkout_req.currency

    if checkout_req.payment:
      existing.payment = PaymentResponse(
        handlers=existing.payment.handlers,
        selected_instrument_id=checkout_req.payment.selected_instrument_id,
        instruments=checkout_req.payment.instruments,
      )

    if checkout_req.buyer:
      existing.buyer = checkout_req.buyer

    if hasattr(checkout_req, "fulfillment") and checkout_req.fulfillment:
      # Hierarchical fulfillment update
      logging.info(
        "Processing hierarchical fulfillment update for %s", checkout_id
      )

      # Fetch customer addresses if buyer is known
      customer_addresses = []
      if existing.buyer and existing.buyer.email:
        customer_addresses = await db.get_customer_addresses(
          self.transactions_session, existing.buyer.email
        )

      req_fulfillment = checkout_req.fulfillment
      resp_methods = []

      if req_fulfillment.root.methods:
        logging.info(
          "Request has %d methods", len(req_fulfillment.root.methods)
        )
        for m_req in req_fulfillment.root.methods:
          # Find matching existing method to preserve state
          existing_method = None
          if existing.fulfillment and existing.fulfillment.root.methods:
            existing_method = next(
              (
                m
                for m in existing.fulfillment.root.methods
                if m.id == getattr(m_req, "id", None)
              ),
              None,
            )
            # Fallback: If no ID in request, and only 1 existing method, match
            # it
            if (
              not existing_method
              and not getattr(m_req, "id", None)
              and len(existing.fulfillment.root.methods) == 1
            ):
              existing_method = existing.fulfillment.root.methods[0]

          # Resolve ID
          method_id = getattr(m_req, "id", None)
          if existing_method and not method_id:
            method_id = existing_method.id
          if not method_id:
            method_id = str(uuid.uuid4())

          method_type = getattr(m_req, "type", "shipping")
          method_li_ids = getattr(m_req, "line_item_ids", None) or [
            li.id for li in existing.line_items
          ]

          resp_destinations = []

          # Handle destinations
          if method_type == "shipping":
            if m_req.destinations:
              # Use provided destinations
              for dest_req in m_req.destinations:
                # Extract inner dest
                inner_dest = dest_req.root
                dest_data = inner_dest.model_dump(exclude_none=True)

                # Persist addresses for known customers
                if existing.buyer and existing.buyer.email:
                  # Save and update ID
                  saved_id = await db.save_customer_address(
                    self.transactions_session,
                    existing.buyer.email,
                    dest_data,
                  )
                  dest_data["id"] = saved_id

                resp_destinations.append(
                  FulfillmentDestinationResponse(
                    root=ShippingDestinationResponse(**dest_data)
                  )
                )

            elif existing_method and existing_method.destinations:
              # Preserve existing destinations
              resp_destinations = existing_method.destinations
            elif customer_addresses:
              for addr in customer_addresses:
                resp_destinations.append(
                  FulfillmentDestinationResponse(
                    root=ShippingDestinationResponse(
                      id=addr.id,
                      street_address=addr.street_address,
                      city=addr.city,
                      region=addr.state,  # Map state to region
                      postal_code=addr.postal_code,
                      address_country=addr.country,
                    )
                  )
                )

          # Handle groups
          resp_groups = []
          if m_req.groups:
            for g_req in m_req.groups:
              g_id = getattr(g_req, "id", None) or f"group_{uuid.uuid4()}"
              g_li_ids = getattr(g_req, "line_item_ids", None) or [
                li.id for li in existing.line_items
              ]
              resp_groups.append(
                FulfillmentGroupResponse(
                  id=g_id,
                  line_item_ids=g_li_ids,
                  selected_option_id=getattr(g_req, "selected_option_id", None),
                )
              )
          elif existing_method and existing_method.groups:
            # Preserve existing groups if not updating them
            resp_groups = existing_method.groups

          # Construct the method response
          method_resp = FulfillmentMethodResponse(
            id=method_id,
            type=method_type,
            line_item_ids=method_li_ids,
            groups=resp_groups or None,
            destinations=resp_destinations or None,
            selected_destination_id=getattr(
              m_req, "selected_destination_id", None
            ),
          )
          resp_methods.append(method_resp)

      existing.fulfillment = FulfillmentResp(
        root=FulfillmentResponse(
          methods=resp_methods,
        )
      )

    if checkout_req.discounts:
      existing.discounts = checkout_req.discounts

    if platform_config:
      existing.platform = platform_config

    # Validate inventory and recalculate totals (Server is authority)
    await self._recalculate_totals(existing)
    await self._validate_inventory(existing)

    response_body = existing.model_dump(mode="json", by_alias=True)

    await db.save_checkout(
      self.transactions_session,
      checkout_id,
      existing.status,
      response_body,
    )

    # Save Idempotency Record
    await db.save_idempotency_record(
      self.transactions_session,
      idempotency_key,
      request_hash,
      200,
      response_body,
    )

    await self.transactions_session.commit()
    return existing

  async def complete_checkout(
    self,
    checkout_id: str,
    payment: PaymentCreateRequest,
    risk_signals: dict[str, Any],
    idempotency_key: str,
    ap2: Ap2CompleteRequest | None = None,
  ) -> Checkout:
    """Complete a checkout session."""
    logger.info("Completing checkout session %s", checkout_id)

    # Idempotency Check
    # Include risk_signals and ap2 in the hash
    combined_data = {
      "payment": payment.model_dump(mode="json"),
      "risk_signals": risk_signals,
      "ap2": ap2.model_dump(mode="json") if ap2 else None,
    }
    request_hash = self._compute_hash(combined_data)

    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )
    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Checkout(**existing_record.response_body)

    # Log the request
    await db.log_request(
      self.transactions_session,
      method="POST",
      url=f"/checkout-sessions/{checkout_id}/complete",
      checkout_id=checkout_id,
      payload=combined_data,
    )

    checkout = await self._get_and_validate_checkout(checkout_id)
    self._ensure_modifiable(checkout, "complete")

    # Process Payment
    await self._process_payment(payment)

    # Validate Fulfillment (Required for completion in this implementation)
    fulfillment_valid = False
    if checkout.fulfillment and checkout.fulfillment.root.methods:
      for method in checkout.fulfillment.root.methods:
        if method.type == "shipping" and not method.selected_destination_id:
          continue
        if method.groups:
          for group in method.groups:
            if group.selected_option_id:
              fulfillment_valid = True
              break
        if fulfillment_valid:
          break

    if not fulfillment_valid:
      raise InvalidRequestError(
        "Fulfillment address and option must be selected before completion."
      )

    # Atomic Inventory Reservation + Order Completion
    try:
      for line in checkout.line_items:
        product_id = line.item.id
        # We verify product existence again (optional but good practice)
        if await db.get_product(self.products_session, product_id):
          success = await db.reserve_stock(
            self.transactions_session, product_id, line.quantity
          )
          if not success:
            # This rollback applies to the transaction_session
            await self.transactions_session.rollback()
            raise OutOfStockError(
              f"Item {product_id} is out of stock", status_code=409
            )

      checkout.status = CheckoutStatus.COMPLETED
      order_id = f"{uuid.uuid4()}"
      order_permalink_url = AnyUrl(f"{self.base_url}/orders/{order_id}")

      checkout.order = OrderConfirmation(
        id=order_id, permalink_url=order_permalink_url
      )
      response_body = checkout.model_dump(mode="json", by_alias=True)

      # Create and persist Order
      expectations = []
      if checkout.fulfillment and checkout.fulfillment.root.methods:
        for method in checkout.fulfillment.root.methods:
          selected_dest = None
          if method.selected_destination_id and method.destinations:
            for dest in method.destinations:
              if dest.root.id == method.selected_destination_id:
                # Convert ShippingDestination to PostalAddress for expectation
                # Assuming simple mapping for now
                dest_root = dest.root

                selected_dest = PostalAddress(
                  street_address=dest_root.street_address,
                  address_locality=dest_root.address_locality,
                  address_region=dest_root.address_region,
                  postal_code=dest_root.postal_code,
                  address_country=dest_root.address_country,
                )
                break

          if method.groups:
            for group in method.groups:
              if group.selected_option_id and group.options:
                selected_opt = next(
                  (
                    o for o in group.options if o.id == group.selected_option_id
                  ),
                  None,
                )
                if selected_opt:
                  expectation_id = f"exp_{uuid.uuid4()}"

                  # Filter line items for this group
                  # group.line_item_ids is list[str]
                  # We need to find quantity for each id
                  exp_line_items = []
                  for li in checkout.line_items:
                    if li.id in group.line_item_ids:
                      exp_line_items.append(
                        ExpectationLineItem(id=li.id, quantity=li.quantity)
                      )

                  expectations.append(
                    Expectation(
                      id=expectation_id,
                      line_items=exp_line_items,
                      method_type=method.type,
                      destination=selected_dest,
                      description=selected_opt.title,
                    )
                  )

      order_line_items = []

      for li in checkout.line_items:
        # Create Quantity object for OrderLineItem
        qty = order_line_item.Quantity(total=li.quantity, fulfilled=0)

        oli = OrderLineItem(
          id=li.id,
          item=li.item,
          quantity=qty,
          totals=li.totals,
          status="processing",
          parent_id=li.parent_id,
        )
        order_line_items.append(oli)

      order = Order(
        ucp=ResponseOrder(**checkout.ucp.model_dump()),
        id=checkout.order.id,
        checkout_id=checkout.id,
        permalink_url=checkout.order.permalink_url,
        line_items=order_line_items,
        totals=[
          total_resp.TotalResponse(**t.model_dump()) for t in checkout.totals
        ],
        fulfillment=OrderFulfillment(expectations=expectations, events=[]),
      )

      await db.save_order(
        self.transactions_session,
        order.id,
        order.model_dump(mode="json", by_alias=True),
      )

      await db.save_checkout(
        self.transactions_session,
        checkout_id,
        checkout.status,
        response_body,
      )

      # Save Idempotency Record
      await db.save_idempotency_record(
        self.transactions_session,
        idempotency_key,
        request_hash,
        200,
        response_body,
      )

      # Commit both inventory updates and checkout status update atomically
      await self.transactions_session.commit()

      # Notify webhook of order placement
      await self._notify_webhook(checkout, "order_placed")

    except Exception as e:
      await self.transactions_session.rollback()
      raise e

    return checkout

  async def _notify_webhook(self, checkout: Checkout, event_type: str) -> None:
    """Notifies the configured webhook of an event."""
    if not checkout.platform or not checkout.platform.webhook_url:
      return

    webhook_url = str(checkout.platform.webhook_url)
    order_data = None
    if checkout.order and checkout.order.id:
      order_data = await db.get_order(
        self.transactions_session, checkout.order.id
      )

    payload = {
      "event_type": event_type,
      "checkout_id": checkout.id,
      "order": order_data,
    }

    try:
      async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=5.0)
    except Exception as e:  # pylint: disable=broad-exception-caught
      logger.error("Failed to notify webhook at %s: %s", webhook_url, e)

  async def ship_order(self, order_id: str) -> None:
    """Simulate shipping an order and notifies the webhook."""
    order_data = await db.get_order(self.transactions_session, order_id)
    if not order_data:
      raise ResourceNotFoundError("Order not found")

    # Add shipping event to order
    if "fulfillment" not in order_data:
      order_data["fulfillment"] = {"events": []}
    if (
      "events" not in order_data["fulfillment"]
      or order_data["fulfillment"]["events"] is None
    ):
      order_data["fulfillment"]["events"] = []

    event_id = f"evt_{uuid.uuid4()}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    order_data["fulfillment"]["events"].append(
      {
        "id": event_id,
        "type": "shipped",
        "timestamp": timestamp,
      }
    )

    await db.save_order(self.transactions_session, order_id, order_data)
    await self.transactions_session.commit()

    # Get checkout to find webhook_url
    checkout_id = order_data.get("checkout_id")
    if checkout_id:
      checkout = await self._get_and_validate_checkout(checkout_id)
      await self._notify_webhook(checkout, "order_shipped")

  async def cancel_checkout(
    self,
    checkout_id: str,
    idempotency_key: str,
  ) -> Checkout:
    """Cancel a checkout session."""
    logger.info("Canceling checkout session %s", checkout_id)

    # Idempotency Check
    # Payload is empty for cancel usually.
    request_hash = self._compute_hash({})

    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )
    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Checkout(**existing_record.response_body)

    # Log the request
    await db.log_request(
      self.transactions_session,
      method="POST",
      url=f"/checkout-sessions/{checkout_id}/cancel",
      checkout_id=checkout_id,
    )

    checkout = await self._get_and_validate_checkout(checkout_id)
    self._ensure_modifiable(checkout, "cancel")

    checkout.status = CheckoutStatus.CANCELED
    response_body = checkout.model_dump(mode="json", by_alias=True)

    await db.save_checkout(
      self.transactions_session,
      checkout_id,
      checkout.status,
      response_body,
    )

    # Save Idempotency Record
    await db.save_idempotency_record(
      self.transactions_session,
      idempotency_key,
      request_hash,
      200,
      response_body,
    )

    await self.transactions_session.commit()
    return checkout

  async def get_order(
    self,
    order_id: str,
  ) -> dict[str, Any]:
    """Retrieve an order."""
    data = await db.get_order(self.transactions_session, order_id)
    if not data:
      raise ResourceNotFoundError("Order not found")
    return data

  async def update_order(
    self,
    order_id: str,
    order: dict[str, Any],
  ) -> dict[str, Any]:
    """Update an order."""
    # Verify existence
    await self.get_order(order_id)

    # Persist
    await db.save_order(
      self.transactions_session,
      order_id,
      order,
    )
    await self.transactions_session.commit()
    return order

  async def _get_and_validate_checkout(self, checkout_id: str) -> Checkout:
    """Retrieve a checkout session and validates its existence."""
    data = await db.get_checkout_session(self.transactions_session, checkout_id)
    if not data:
      raise ResourceNotFoundError("Checkout session not found")
    return Checkout(**data)

  def _ensure_modifiable(self, checkout: Checkout, action: str) -> None:
    """Ensure that the checkout is in a state that allows modification."""
    if checkout.status in [CheckoutStatus.COMPLETED, CheckoutStatus.CANCELED]:
      raise CheckoutNotModifiableError(
        f"Cannot {action} checkout in state '{checkout.status}'"
      )

  async def _validate_inventory(
    self,
    checkout: Checkout,
  ) -> None:
    """Validate that all items in the checkout have sufficient stock."""
    for line in checkout.line_items:
      product_id = line.item.id
      qty_avail = await db.get_inventory(self.transactions_session, product_id)
      if qty_avail is None or qty_avail < line.quantity:
        raise OutOfStockError(f"Insufficient stock for item {product_id}")

  async def _recalculate_totals(
    self,
    checkout: Checkout,
  ) -> None:
    """Recalculate line item subtotals and checkout totals."""
    grand_total = 0

    for line in checkout.line_items:
      product_id = line.item.id
      product = await db.get_product(self.products_session, product_id)
      if not product:
        raise InvalidRequestError(f"Product {product_id} not found")

      # Use authoritative price and title from DB
      line.item.price = product.price
      line.item.title = product.title

      base_amount = product.price * line.quantity
      line.totals = [
        Total(type="subtotal", amount=base_amount),
        Total(type="total", amount=base_amount),
      ]
      grand_total += base_amount

    checkout.totals = []
    # Always include subtotal for clarity when other costs might be added
    checkout.totals.append(Total(type="subtotal", amount=grand_total))

    # Fulfillment Logic
    if checkout.fulfillment and checkout.fulfillment.root.methods:
      # Fetch promotions once for the loop
      promotions = await db.get_active_promotions(self.products_session)

      for method in checkout.fulfillment.root.methods:
        # 1. Identify Destination and Calculate Options
        calculated_options = []
        if method.type == "shipping" and method.selected_destination_id:
          selected_dest = None
          if method.destinations:
            for dest in method.destinations:
              if dest.root.id == method.selected_destination_id:
                selected_dest = dest.root
                break

          if selected_dest:
            logger.info(
              "Calculating options for country: %s (dest_id: %s)",
              selected_dest.address_country,
              method.selected_destination_id,
            )
            # Log all available destinations for debugging
            if method.destinations:
              logger.info(
                "Available destinations in method %s: %s",
                method.id,
                [
                  f"{d.root.id} ({d.root.address_country})"
                  for d in method.destinations
                ],
              )
            try:
              # Map ShippingDestination to PostalAddress for service call
              # Using strong types from SDK
              address_obj = PostalAddress(
                street_address=selected_dest.street_address,
                address_locality=selected_dest.address_locality,
                address_region=selected_dest.address_region,
                postal_code=selected_dest.postal_code,
                address_country=selected_dest.address_country,
              )

              # Get options from service
              # We calculate based on the items in this method/group
              # For simplicity, passing method's line_item_ids if available,
              # else all.
              all_li_ids = [li.id for li in checkout.line_items]
              target_li_ids = method.line_item_ids or all_li_ids

              # Map Line Item IDs to Product IDs for the service
              target_product_ids = []
              for li_uuid in target_li_ids:
                li = next(
                  (item for item in checkout.line_items if item.id == li_uuid),
                  None,
                )
                if li:
                  target_product_ids.append(li.item.id)

              calculated_options_resp = (
                await self.fulfillment_service.calculate_options(
                  self.transactions_session,
                  address_obj,
                  promotions=promotions,
                  subtotal=grand_total,
                  line_item_ids=target_product_ids,
                )
              )
              calculated_options = [opt.root for opt in calculated_options_resp]
            except (ValueError, TypeError) as e:
              logging.error("Failed to calculate options: %s", e)

        # 2. Generate or Update Groups
        if method.selected_destination_id and not method.groups:
          # Generate new group
          group = FulfillmentGroupResponse(
            id=f"group_{uuid.uuid4()}",
            line_item_ids=method.line_item_ids,
            options=calculated_options,
          )
          method.groups = [group]
        elif method.groups:
          # Update existing groups with fresh options
          for group in method.groups:
            # Refresh options if they changed due to address/item update
            if calculated_options:
              group.options = calculated_options

            # Recalculate Totals based on Group Selection
            if group.selected_option_id and group.options:
              selected_opt = next(
                (o for o in group.options if o.id == group.selected_option_id),
                None,
              )
              if selected_opt:
                # Avoid double counting if already added.
                # Multiple groups can have costs.
                # We assume each group adds to the total.
                opt_total = next(
                  (t.amount for t in selected_opt.totals if t.type == "total"),
                  0,
                )
                grand_total += opt_total
                checkout.totals.append(
                  Total(type="fulfillment", amount=opt_total)
                )

    # Discount Logic
    if not checkout.discounts:
      checkout.discounts = DiscountsObject()

    if checkout.discounts.codes:
      # Batch fetch discounts to avoid N+1 queries
      discounts = await db.get_discounts_by_codes(
        self.transactions_session, checkout.discounts.codes
      )
      # Create a map for easy lookup by code (preserving request order if
      # needed)
      discount_map = {d.code: d for d in discounts}

      for code in checkout.discounts.codes:
        discount_obj = discount_map.get(code)
        if discount_obj:
          discount_amount = 0
          if discount_obj.type == "percentage":
            discount_amount = int(grand_total * (discount_obj.value / 100))
          elif discount_obj.type == "fixed_amount":
            discount_amount = discount_obj.value

          if discount_amount > 0:
            grand_total -= discount_amount
            if checkout.discounts.applied is None:
              checkout.discounts.applied = []
            checkout.discounts.applied.append(
              AppliedDiscount(
                code=code,
                title=discount_obj.description,
                amount=discount_amount,
                allocations=[
                  Allocation(
                    path="$.totals[?(@.type=='subtotal')]",
                    amount=discount_amount,
                  )
                ],
              )
            )
            checkout.totals.append(
              Total(type="discount", amount=discount_amount)
            )

    checkout.totals.append(Total(type="total", amount=grand_total))

  async def _process_payment(self, payment: PaymentCreateRequest) -> None:
    """Validate and process payment instruments."""
    instruments = payment.instruments
    if not instruments:
      raise InvalidRequestError("Missing payment instruments")

    selected_id = payment.selected_instrument_id
    if not selected_id:
      raise InvalidRequestError("Missing selected_instrument_id")

    selected_instrument = next(
      (i for i in instruments if i.root.id == selected_id), None
    )
    if not selected_instrument:
      raise InvalidRequestError(f"Selected instrument {selected_id} not found")

    handler_id = selected_instrument.root.handler_id
    credential = selected_instrument.root.credential
    if not credential:
      raise InvalidRequestError("Missing credentials in instrument")

    # If it's a RootModel (like PaymentCredential), unwrap it to get the actual
    # credential data
    if hasattr(credential, "root"):
      credential = credential.root

    token = None
    if isinstance(credential, CardCredential):
      # Handle card details
      logger.info(
        "Processing card payment for card ending in %s",
        credential.number[-4:] if credential.number else "unknown",
      )
      return
    elif isinstance(credential, TokenCredentialResponse):
      token = credential.token
    elif isinstance(credential, dict):
      # Attempt to parse as TokenCredentialResponse or CardCredential
      try:
        cred_model = TokenCredentialResponse.model_validate(credential)
        token = cred_model.token
      except (ValueError, TypeError):
        try:
          cred_model = CardCredential.model_validate(credential)
          logger.info(
            "Processing card payment for card ending in %s",
            cred_model.number[-4:] if cred_model.number else "unknown",
          )
          return
        except (ValueError, TypeError):
          # Fallback to direct access if validation fails (e.g. partial data)
          token = credential.get("token")
    else:
      # Fallback for unknown types if model validation allowed extras or
      # different types
      logger.warning("Unknown credential type: %s", type(credential))
      token = getattr(credential, "token", None)

    if handler_id == "mock_payment_handler":
      if token == "success_token":
        return  # Success
      elif token == "fail_token":
        raise PaymentFailedError(
          "Payment Failed: Insufficient Funds (Mock)",
          code="INSUFFICIENT_FUNDS",
        )
      elif token == "fraud_token":
        raise PaymentFailedError(
          "Payment Failed: Fraud Detected (Mock)",
          code="FRAUD_DETECTED",
          status_code=403,
        )
      else:
        raise PaymentFailedError(
          f"Unknown mock token: {token}", code="UNKNOWN_TOKEN"
        )
    elif handler_id == "google_pay":
      # Accept any token for now, or specific ones
      return
    elif handler_id == "shop_pay":
      # For shop_pay, we expect a 'shop_token' credential type.
      # Since we don't have a real backend, we accept it if present.
      # The token value validation logic is similar to mock_payment_handler
      # for this test. Or just accept any token.
      return
    else:
      # Unknown handler
      raise InvalidRequestError(f"Unsupported payment handler: {handler_id}")
