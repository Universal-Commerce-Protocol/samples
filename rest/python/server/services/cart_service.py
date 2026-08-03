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

"""Cart service for managing the lifecycle of cart sessions."""

import logging
import uuid
import datetime
from typing import Any

import config
import db
from exceptions import (
  ResourceNotFoundError,
  IdempotencyConflictError,
  InvalidRequestError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from models import UnifiedCart as Cart
from models import UnifiedCartCreateRequest as CartCreateRequest
from models import UnifiedCartUpdateRequest as CartUpdateRequest
from ucp_sdk.models.schemas.shopping.discount import (
  DiscountsObject,
  AppliedDiscount,
  Allocation,
)
from ucp_sdk.models.schemas.shopping.types.line_item import (
  LineItem as LineItemResponse,
)
from ucp_sdk.models.schemas.shopping.types.item import Item as ItemResponse
from ucp_sdk.models.schemas.shopping.types.total import Total as TotalResponse
from ucp_sdk.models.schemas.ucp import ResponseCartSchema
from ucp_sdk.models.schemas.capability import ResponseSchema as Response
from pydantic import BaseModel, AnyUrl
import json
import hashlib

logger = logging.getLogger(__name__)


class CartService:
  """Service for managing cart sessions."""

  def __init__(
    self,
    products_session: AsyncSession,
    transactions_session: AsyncSession,
    base_url: str,
  ):
    """Initialize CartService."""
    self.products_session = products_session
    self.transactions_session = transactions_session
    self.base_url = base_url.rstrip("/")

  def _compute_hash(self, data: Any) -> str:
    """Compute SHA256 hash of the JSON-serialized data."""
    if isinstance(data, BaseModel):
      json_str = json.dumps(data.model_dump(mode="json"), sort_keys=True)
    else:
      json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

  async def create_cart(
    self,
    cart_req: CartCreateRequest,
    idempotency_key: str,
  ) -> Cart:
    """Create a new cart session."""
    logger.info("Creating cart session")

    # Idempotency Check
    request_hash = self._compute_hash(cart_req)
    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )

    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Cart(**existing_record.response_body)

    cart_id = f"cart_{uuid.uuid4()}"

    # Map line items
    line_items = []
    for li_req in cart_req.line_items:
      line_items.append(
        LineItemResponse(
          id=str(uuid.uuid4()),
          item=ItemResponse(
            id=li_req.item.id,
            title="",
            price=0,
          ),
          quantity=li_req.quantity,
          totals=[],
        )
      )

    cart_data = cart_req.model_dump(
      exclude={
        "line_items",
      }
    )

    cart = Cart(
      ucp=ResponseCartSchema(
        version=config.get_server_version(),
        capabilities={
          "dev.ucp.shopping.cart": [
            Response(
              name="dev.ucp.shopping.cart",
              version=config.get_server_version(),
            )
          ]
        },
      ),
      id=cart_id,
      line_items=line_items,
      currency="USD",
      totals=[
        {"type": "subtotal", "amount": 0},
        {"type": "total", "amount": 0},
      ],
      continue_url=AnyUrl(f"{self.base_url}/checkout?cart={cart_id}"),
      expires_at=datetime.datetime.now(datetime.timezone.utc)
      + datetime.timedelta(days=7),
      **cart_data,
    )

    await self._enrich_and_recalculate(cart)

    response_body = cart.model_dump(
      mode="json", by_alias=True, exclude_none=True
    )

    # Persist cart
    await db.save_cart(
      self.transactions_session,
      cart.id,
      response_body,
    )

    # Save Idempotency Record
    await db.save_idempotency_record(
      self.transactions_session,
      idempotency_key,
      request_hash,
      201,
      response_body,
    )

    await self.transactions_session.commit()
    return cart

  async def get_cart(self, cart_id: str) -> Cart:
    """Retrieve a cart session."""
    data = await db.get_cart_session(self.transactions_session, cart_id)
    if not data:
      raise ResourceNotFoundError(f"Cart session {cart_id} not found")
    return Cart(**data)

  async def update_cart(
    self,
    cart_id: str,
    cart_req: CartUpdateRequest,
    idempotency_key: str,
  ) -> Cart:
    """Update a cart session."""
    logger.info("Updating cart session %s", cart_id)

    # Idempotency Check
    request_hash = self._compute_hash(cart_req)
    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )
    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Cart(**existing_record.response_body)

    # Verify existence
    existing_data = await db.get_cart_session(
      self.transactions_session, cart_id
    )
    if not existing_data:
      raise ResourceNotFoundError(f"Cart session {cart_id} not found")
    existing = Cart(**existing_data)

    # Update line items
    line_items = []
    for li_req in cart_req.line_items:
      line_items.append(
        LineItemResponse(
          id=li_req.id or str(uuid.uuid4()),
          item=ItemResponse(
            id=li_req.item.id,
            title="",
            price=0,
          ),
          quantity=li_req.quantity,
          totals=[],
          parent_id=li_req.parent_id,
        )
      )
    existing.line_items = line_items

    if cart_req.buyer:
      existing.buyer = cart_req.buyer
    if cart_req.context:
      existing.context = cart_req.context
    if cart_req.discounts is not None:
      existing.discounts = cart_req.discounts

    await self._enrich_and_recalculate(existing)

    response_body = existing.model_dump(
      mode="json", by_alias=True, exclude_none=True
    )

    await db.save_cart(
      self.transactions_session,
      cart_id,
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

  async def cancel_cart(
    self,
    cart_id: str,
    idempotency_key: str,
  ) -> Cart:
    """Cancel a cart session."""
    logger.info("Canceling cart session %s", cart_id)

    # Idempotency Check
    request_hash = self._compute_hash({})
    existing_record = await db.get_idempotency_record(
      self.transactions_session, idempotency_key
    )
    if existing_record:
      if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
          "Idempotency key reused with different parameters"
        )
      return Cart(**existing_record.response_body)

    # Verify existence
    existing_data = await db.get_cart_session(
      self.transactions_session, cart_id
    )
    if not existing_data:
      raise ResourceNotFoundError(f"Cart session {cart_id} not found")
    cart = Cart(**existing_data)

    # Delete cart
    await db.delete_cart_session(self.transactions_session, cart_id)

    response_body = cart.model_dump(
      mode="json", by_alias=True, exclude_none=True
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
    return cart

  async def _enrich_and_recalculate(self, cart: Cart) -> None:
    """Enrich cart items from catalog and recalculate subtotals and totals."""
    grand_total = 0

    for line in cart.line_items:
      product_id = line.item.id
      product = await db.get_product(self.products_session, product_id)
      if not product:
        raise InvalidRequestError(f"Product {product_id} not found")

      line.item.price = product.price
      line.item.title = product.title

      base_amount = product.price * line.quantity
      line.totals = [
        TotalResponse(type="subtotal", amount=base_amount),
        TotalResponse(type="total", amount=base_amount),
      ]
      grand_total += base_amount

    cart.totals = [
      TotalResponse(type="subtotal", amount=grand_total),
    ]

    # Discount Logic
    if not cart.discounts:
      cart.discounts = DiscountsObject()

    cart.discounts.applied = None

    if cart.discounts.codes:
      discounts = await db.get_discounts_by_codes(
        self.transactions_session, cart.discounts.codes
      )
      discount_map = {d.code.upper(): d for d in discounts}

      for code in cart.discounts.codes:
        discount_obj = discount_map.get(code.upper())
        if discount_obj:
          discount_amount = 0
          if discount_obj.type == "percentage":
            discount_amount = int(grand_total * (discount_obj.value / 100))
          elif discount_obj.type == "fixed_amount":
            discount_amount = discount_obj.value

          if discount_amount > 0:
            grand_total -= discount_amount
            if cart.discounts.applied is None:
              cart.discounts.applied = []
            cart.discounts.applied.append(
              AppliedDiscount(
                code=discount_obj.code,
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
            cart.totals.append(
              TotalResponse(type="discount", amount=-discount_amount)
            )

    cart.totals.append(TotalResponse(type="total", amount=grand_total))
