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

"""Catalog service for searching and looking up products."""

import base64
import binascii
import logging
from typing import Any

import config
import db
from enums import MessageType
from exceptions import InvalidRequestError
from exceptions import RequestTooLargeError
from sqlalchemy import false
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ucp_sdk.models.schemas.shopping import catalog_lookup
from ucp_sdk.models.schemas.shopping import catalog_search
from ucp_sdk.models.schemas.shopping.types import search_filters

logger = logging.getLogger(__name__)

SEARCH_CAPABILITY = "dev.ucp.shopping.catalog.search"
LOOKUP_CAPABILITY = "dev.ucp.shopping.catalog.lookup"

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
MAX_LOOKUP_IDS = 50
# Largest offset the database accepts.
MAX_OFFSET = 2**63 - 1


def _ucp(capability: str, **extra: Any) -> dict[str, Any]:
  version = config.get_server_version()
  return {
    "version": version,
    "capabilities": {capability: [{"name": capability, "version": version}]},
    **extra,
  }


def _encode_cursor(offset: int) -> str:
  return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode_cursor(cursor: str | None) -> int:
  if not cursor:
    return 0
  try:
    offset = int(base64.urlsafe_b64decode(cursor.encode()).decode())
  except (ValueError, binascii.Error) as exc:
    raise InvalidRequestError("pagination.cursor is not valid.") from exc
  if not 0 <= offset <= MAX_OFFSET:
    raise InvalidRequestError("pagination.cursor is not valid.")
  return offset


class CatalogService:
  """Serves the product table as a UCP catalog.

  The store has no variants of its own, so every product is offered as a
  single variant that carries the product's id. That id is what checkout
  and cart expect in ``line_items[].item.id``.
  """

  def __init__(
    self, products_session: AsyncSession, transactions_session: AsyncSession
  ):
    """Initialize the catalog service."""
    self.products_session = products_session
    self.transactions_session = transactions_session

  async def search(self, request: catalog_search.SearchRequest) -> Any:
    """Search products by title, optionally narrowed by filters."""
    query = (request.query or "").strip()
    filters = request.filters
    price = filters.price if filters else None
    has_filter = bool(filters and filters.categories) or (
      price is not None and (price.min is not None or price.max is not None)
    )
    if not query and not has_filter:
      raise InvalidRequestError("A search needs a query or a filter.")

    statement = select(db.Product)
    for term in query.lower().split():
      statement = statement.where(
        func.lower(db.Product.title).contains(term, autoescape=True)
      )
    if filters and filters.categories:
      # Products carry no categories, so a category filter matches nothing.
      statement = statement.where(false())
    if price is not None and price.min is not None:
      statement = statement.where(db.Product.price >= price.min)
    if price is not None and price.max is not None:
      statement = statement.where(db.Product.price <= price.max)

    total = await self.products_session.scalar(
      select(func.count()).select_from(statement.subquery())
    )
    pagination = request.pagination
    limit = min(
      (pagination.limit if pagination else None) or DEFAULT_PAGE_SIZE,
      MAX_PAGE_SIZE,
    )
    offset = _decode_cursor(pagination.cursor if pagination else None)
    result = await self.products_session.execute(
      statement.order_by(db.Product.id).offset(offset).limit(limit)
    )
    products = [await self._product(row) for row in result.scalars().all()]

    has_next_page = offset + len(products) < total
    page: dict[str, Any] = {
      "has_next_page": has_next_page,
      "total_count": total,
    }
    if has_next_page:
      page["cursor"] = _encode_cursor(offset + len(products))
    return catalog_search.SearchResponse(
      ucp=_ucp(SEARCH_CAPABILITY), products=products, pagination=page
    )

  async def lookup(self, request: catalog_lookup.LookupRequest) -> Any:
    """Resolve a batch of identifiers to products."""
    if len(request.ids) > MAX_LOOKUP_IDS:
      raise RequestTooLargeError(
        f"A lookup accepts at most {MAX_LOOKUP_IDS} identifiers."
      )
    ids = list(dict.fromkeys(request.ids))

    result = await self.products_session.execute(
      select(db.Product).where(db.Product.id.in_(ids))
    )
    found = {row.id: row for row in result.scalars().all()}

    products = []
    messages = []
    for identifier in ids:
      row = found.get(identifier)
      if row is None:
        messages.append(
          {"type": MessageType.INFO, "code": "not_found", "content": identifier}
        )
        continue
      # Filters apply after resolution: a product they exclude was found,
      # so it is left out without a not_found message.
      if not self._matches(row, request.filters):
        continue
      product = await self._product(row)
      # The id names the product and its only variant, so it resolves to
      # that variant directly.
      product["variants"][0]["inputs"] = [{"id": identifier, "match": "exact"}]
      products.append(product)

    return catalog_lookup.LookupResponse(
      ucp=_ucp(LOOKUP_CAPABILITY),
      products=products,
      messages=messages or None,
    )

  async def get_product(self, request: catalog_lookup.GetProductRequest) -> Any:
    """Return one product, or an error envelope when it is not found."""
    row = await db.get_product(self.products_session, request.id)
    content = None
    if row is None:
      content = f"Product not found: {request.id}"
    elif not self._matches(row, request.filters):
      content = f"No variant of {request.id} matches the filters."
    if content:
      # Not found is reported in the envelope, with HTTP 200.
      return {
        "ucp": _ucp(LOOKUP_CAPABILITY, status="error"),
        "messages": [
          {
            "type": MessageType.ERROR,
            "code": "not_found",
            "content": content,
            "severity": "unrecoverable",
          }
        ],
      }
    return catalog_lookup.GetProductResponse(
      ucp=_ucp(LOOKUP_CAPABILITY), product=await self._product(row)
    )

  def _matches(
    self, row: db.Product, filters: search_filters.SearchFilters | None
  ) -> bool:
    """Tell whether a product passes the filters."""
    if filters is None:
      return True
    if filters.categories:
      # Products carry no categories, so a category filter matches nothing.
      return False
    price = filters.price
    if price is None:
      return True
    above_min = price.min is None or row.price >= price.min
    below_max = price.max is None or row.price <= price.max
    return above_min and below_max

  async def _product(self, row: db.Product) -> dict[str, Any]:
    """Render a product row with its single variant."""
    quantity = await db.get_inventory(self.transactions_session, row.id)
    price = {"amount": row.price, "currency": config.get_default_currency()}
    media = (
      [{"type": "image", "url": row.image_url, "alt_text": row.title}]
      if row.image_url
      else None
    )
    description = {"plain": row.title}
    product: dict[str, Any] = {
      "id": row.id,
      "title": row.title,
      "description": description,
      "price_range": {"min": price, "max": price},
      "variants": [
        {
          "id": row.id,
          "title": row.title,
          "description": description,
          "price": price,
          "availability": {"available": bool(quantity and quantity > 0)},
        }
      ],
    }
    if media:
      product["media"] = media
      product["variants"][0]["media"] = media
    return product
