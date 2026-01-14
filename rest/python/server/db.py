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

"""Database management and persistence layer for the UCP sample REST server.

This module provides the schema definitions, database session management, and
asynchronous data access helpers used by the server. It utilizes SQLAlchemy with
SQLite (via aiosqlite) and implements a multi-database architecture separating
product catalog data from transactional session and order data.

Key features include:
- `DatabaseManager`: Handles asynchronous engine initialization and session
factory
  setup for both 'Products' and 'Transactions' databases.
- WAL Mode: Automatically enables SQLite Write-Ahead Logging to support
concurrent
  access from the main server and the webhook server.
- Declarative Models: Defines tables for products, inventory, checkout sessions,
  orders, request logging, and idempotency tracking.
- Data Access Helpers: A suite of asynchronous functions for CRUD operations on
  the database models.
"""

import datetime
import logging
from typing import Any
import uuid

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

ProductBase = declarative_base()
TransactionBase = declarative_base()


class DatabaseManager:
  """Manages database engines and sessions without using global variables."""

  def __init__(self) -> None:
    """Initialize DatabaseManager."""
    self.products_engine: AsyncEngine | None = None
    self.transactions_engine: AsyncEngine | None = None
    self.products_session_factory: sessionmaker | None = None
    self.transactions_session_factory: sessionmaker | None = None

  async def init_dbs(self, products_path: str, transactions_path: str) -> None:
    """Initialize database engines and creates tables."""
    # Products DB Setup
    prod_url = f"sqlite+aiosqlite:///{products_path}"
    self.products_engine = create_async_engine(prod_url, echo=False)

    # Enable WAL mode for Products DB
    async with self.products_engine.connect() as conn:
      await conn.execute(text("PRAGMA journal_mode=WAL"))

    self.products_session_factory = sessionmaker(
      self.products_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with self.products_engine.begin() as conn:
      await conn.run_sync(ProductBase.metadata.create_all)

    # Transactions DB Setup (includes Inventory)
    trans_url = f"sqlite+aiosqlite:///{transactions_path}"
    self.transactions_engine = create_async_engine(trans_url, echo=False)

    # Enable WAL mode for Transactions DB
    async with self.transactions_engine.connect() as conn:
      await conn.execute(text("PRAGMA journal_mode=WAL"))

    self.transactions_session_factory = sessionmaker(
      self.transactions_engine, expire_on_commit=False, class_=AsyncSession
    )

    async with self.transactions_engine.begin() as conn:
      await conn.run_sync(TransactionBase.metadata.create_all)

  async def close(self) -> None:
    """Close all database engines."""
    if self.products_engine:
      await self.products_engine.dispose()
    if self.transactions_engine:
      await self.transactions_engine.dispose()


# Global manager instance (to be initialized via lifespan)
manager = DatabaseManager()


class Product(ProductBase):
  """Product database model."""

  __tablename__ = "products"

  id = Column(String, primary_key=True)
  title = Column(String)
  price = Column(Integer)  # Price in cents
  image_url = Column(String, nullable=True)


class Promotion(ProductBase):
  """Promotion database model."""

  __tablename__ = "promotions"

  id = Column(String, primary_key=True)
  type = Column(String)  # e.g., 'free_shipping'
  min_subtotal = Column(Integer, nullable=True)  # In cents
  eligible_item_ids = Column(JSON, nullable=True)  # List of item IDs
  description = Column(String)


class Inventory(TransactionBase):
  """Inventory database model."""

  __tablename__ = "inventory"

  product_id = Column(String, primary_key=True)
  quantity = Column(Integer, default=0)


class Customer(TransactionBase):
  """Customer database model."""

  __tablename__ = "customers"

  id = Column(String, primary_key=True)
  name = Column(String)
  email = Column(String, index=True)

  addresses = relationship("CustomerAddress", back_populates="customer")


class CustomerAddress(TransactionBase):
  """Customer address database model."""

  __tablename__ = "customer_addresses"

  id = Column(String, primary_key=True)
  customer_id = Column(String, ForeignKey("customers.id"))
  street_address = Column(String)
  city = Column(String)
  state = Column(String)
  postal_code = Column(String)
  country = Column(String)

  customer = relationship("Customer", back_populates="addresses")


class CheckoutSession(TransactionBase):
  """Checkout session database model."""

  __tablename__ = "checkouts"

  id = Column(String, primary_key=True)
  status = Column(String)
  # SQLAlchemy JSON type handles serialization automatically
  data = Column(JSON)


class Order(TransactionBase):
  """Order database model."""

  __tablename__ = "orders"

  id = Column(String, primary_key=True)
  data = Column(JSON)


class RequestLog(TransactionBase):
  """HTTP request log database model."""

  __tablename__ = "request_logs"

  id = Column(Integer, primary_key=True, autoincrement=True)
  timestamp = Column(String)
  method = Column(String)
  url = Column(String)
  checkout_id = Column(String, nullable=True)
  payload = Column(JSON, nullable=True)


class IdempotencyRecord(TransactionBase):
  """Idempotency record database model."""

  __tablename__ = "idempotency_records"

  key = Column(String, primary_key=True)
  request_hash = Column(String)
  response_status = Column(Integer)
  response_body = Column(JSON)
  created_at = Column(String)


class PaymentInstrument(TransactionBase):
  """Payment instrument database model."""

  __tablename__ = "payment_instruments"

  id = Column(String, primary_key=True)
  type = Column(String)
  brand = Column(String)
  last_digits = Column(String)
  token = Column(String)
  handler_id = Column(String)


class Discount(TransactionBase):
  """Discount database model."""

  __tablename__ = "discounts"

  code = Column(String, primary_key=True)
  type = Column(String)  # 'percentage' or 'fixed_amount'
  value = Column(Integer)  # Percentage (e.g., 10) or Amount in cents
  description = Column(String)


class ShippingRate(TransactionBase):
  """Shipping rate database model."""

  __tablename__ = "shipping_rates"

  id = Column(String, primary_key=True)
  country_code = Column(String)  # e.g., 'US', 'default'
  service_level = Column(String)  # e.g., 'standard', 'express'
  price = Column(Integer)  # In cents
  title = Column(String)


# --- Data Access Helpers ---


async def get_shipping_rates(
  session: AsyncSession, country_code: str
) -> list[ShippingRate]:
  """Retrieve shipping rates for a specific country and default rates.

  Args:
    session: The database session to use.
    country_code: The ISO country code (e.g., 'US') to fetch rates for.

  Returns:
    A list of ShippingRate objects matching the country or 'default'.

  """
  result = await session.execute(
    select(ShippingRate).where(
      ShippingRate.country_code.in_([country_code, "default"])
    )
  )
  return list(result.scalars().all())


async def get_discount(session: AsyncSession, code: str) -> Discount | None:
  """Retrieve a discount by code.

  Args:
    session: The database session to use.
    code: The discount code to look up.

  Returns:
    The Discount object if found, otherwise None.

  """
  return await session.get(Discount, code)


async def get_discounts_by_codes(
  session: AsyncSession, codes: list[str]
) -> list[Discount]:
  """Retrieve multiple discounts by their codes in a single query.

  Args:
    session: The database session to use.
    codes: A list of discount codes to look up.

  Returns:
    A list of matching Discount objects.

  """
  result = await session.execute(
    select(Discount).where(Discount.code.in_(codes))
  )
  return list(result.scalars().all())


async def get_active_promotions(session: AsyncSession) -> list[Promotion]:
  """Retrieve all active promotions."""
  result = await session.execute(select(Promotion))
  return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: str) -> Product | None:
  """Retrieve a product by ID."""
  return await session.get(Product, product_id)


async def get_inventory(session: AsyncSession, product_id: str) -> int | None:
  """Retrieve the inventory quantity for a product."""
  result = await session.execute(
    select(Inventory.quantity).where(Inventory.product_id == product_id)
  )
  return result.scalar_one_or_none()


async def get_customer_addresses(
  session: AsyncSession, email: str
) -> list[CustomerAddress]:
  """Retrieve addresses for a customer by email."""
  # First find customer by email
  result = await session.execute(
    select(Customer).where(Customer.email == email)
  )
  customer = result.scalar_one_or_none()
  if not customer:
    return []

  # Then get their addresses
  # Using explicit join or select if lazy loading is an issue with async session
  # But simple select on CustomerAddress is easier
  result = await session.execute(
    select(CustomerAddress).where(CustomerAddress.customer_id == customer.id)
  )
  return list(result.scalars().all())


async def get_customer(session: AsyncSession, email: str) -> Customer | None:
  """Retrieve a customer by email."""
  result = await session.execute(
    select(Customer).where(Customer.email == email)
  )
  return result.scalar_one_or_none()


async def save_customer_address(
  session: AsyncSession, email: str, address: dict[str, Any]
) -> str:
  """Save a customer address, reusing existing ID if content matches.

  Args:
    session: The database session.
    email: The customer's email.
    address: The address dictionary containing 'street_address', 'city', etc.

  Returns:
    The ID of the saved or existing address.

  """
  customer = await get_customer(session, email)
  if not customer:
    # Create customer if missing
    customer = Customer(id=str(uuid.uuid4()), email=email, name="Unknown")
    session.add(customer)
    # Flush to get ID if needed, though we set it manually
    await session.flush()

  # Check for existing address with same content
  stmt = select(CustomerAddress).where(
    CustomerAddress.customer_id == customer.id,
    CustomerAddress.street_address == address.get("street_address"),
    # Map locality to city
    CustomerAddress.city == address.get("address_locality"),
    # Map region to state
    CustomerAddress.state == address.get("address_region"),
    CustomerAddress.postal_code == address.get("postal_code"),
    CustomerAddress.country == address.get("address_country"),
  )
  result = await session.execute(stmt)
  existing_addr = result.scalar_one_or_none()

  if existing_addr:
    return existing_addr.id

  # Create new address
  new_id = address.get("id") or str(uuid.uuid4())
  new_addr = CustomerAddress(
    id=new_id,
    customer_id=customer.id,
    street_address=address.get("street_address"),
    # Map locality to city
    city=address.get("address_locality"),
    state=address.get("address_region"),
    postal_code=address.get("postal_code"),
    country=address.get("address_country"),
  )
  session.add(new_addr)
  return new_id


async def reserve_stock(
  session: AsyncSession, product_id: str, quantity: int
) -> bool:
  """Atomically decrements inventory if sufficient stock exists."""
  stmt = (
    update(Inventory)
    .where(Inventory.product_id == product_id)
    .where(Inventory.quantity >= quantity)
    .values(quantity=Inventory.quantity - quantity)
  )
  result = await session.execute(stmt)
  return result.rowcount > 0


async def save_checkout(
  session: AsyncSession,
  checkout_id: str,
  status: str,
  checkout_obj: dict[str, Any],
) -> None:
  """Save or update a checkout session."""
  existing = await session.get(CheckoutSession, checkout_id)
  if existing:
    existing.status = status
    existing.data = checkout_obj
  else:
    new_checkout = CheckoutSession(
      id=checkout_id, status=status, data=checkout_obj
    )
    session.add(new_checkout)


async def get_checkout_session(
  session: AsyncSession, checkout_id: str
) -> dict[str, Any] | None:
  """Retrieve a checkout session by ID."""
  result = await session.get(CheckoutSession, checkout_id)
  if result:
    return result.data
  return None


async def save_order(
  session: AsyncSession, order_id: str, order_obj: dict[str, Any]
) -> None:
  """Save or update an order."""
  existing = await session.get(Order, order_id)
  if existing:
    existing.data = order_obj
  else:
    new_order = Order(id=order_id, data=order_obj)
    session.add(new_order)


async def get_order(
  session: AsyncSession, order_id: str
) -> dict[str, Any] | None:
  """Retrieve an order by ID."""
  result = await session.get(Order, order_id)
  if result:
    return result.data
  return None


async def log_request(
  session: AsyncSession,
  method: str,
  url: str,
  checkout_id: str | None = None,
  payload: dict[str, Any] | None = None,
) -> None:
  """Log an HTTP request to the database."""
  log_entry = RequestLog(
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    method=method,
    url=url,
    checkout_id=checkout_id,
    payload=payload,
  )
  session.add(log_entry)


async def get_idempotency_record(
  session: AsyncSession, key: str
) -> IdempotencyRecord | None:
  """Retrieve an idempotency record by key."""
  return await session.get(IdempotencyRecord, key)


async def save_idempotency_record(
  session: AsyncSession,
  key: str,
  request_hash: str,
  response_status: int,
  response_body: dict[str, Any],
) -> None:
  """Save a new idempotency record."""
  record = IdempotencyRecord(
    key=key,
    request_hash=request_hash,
    response_status=response_status,
    response_body=response_body,
    created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  )
  session.add(record)
