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

"""Integration tests for the UCP SDK Server."""

import asyncio
from collections.abc import AsyncGenerator
import datetime
import json
from pathlib import Path
import shutil
import tempfile
import uuid

from urllib.parse import urlsplit

from absl import flags
from absl.testing import absltest
import config
import db
import dependencies
from fastapi.testclient import TestClient
import httpx
import respx
import ucp_signing
import webhook_signer
from enums import ErrorSeverity, MessageType
from exceptions import UcpErrorResponse, UcpMessageError
from models import UnifiedCheckout
from server.server import app
from services.checkout_service import CheckoutService
from services.fulfillment_service import FulfillmentService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete
from ucp_sdk.models.schemas.shopping import (
  checkout_create_request as checkout_create_req,
)
from ucp_sdk.models.schemas.shopping import (
  payment_create_request as payment_create_req,
)

from ucp_sdk.models.schemas.shopping import (
  checkout_complete_request as checkout_comp_req,
  payment_complete_request as payment_comp_req,
)
from ucp_sdk.models.schemas.shopping.ap2_mandate import Checkout as Ap2Checkout
from ucp_sdk.models.schemas.shopping.buyer_consent import (
  Checkout as BuyerConsentCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.discount import (
  Checkout as DiscountCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.fulfillment import (
  Checkout as FulfillmentCheckout,
)
from ucp_sdk.models.schemas.shopping.order import Order
from ucp_sdk.models.schemas.shopping.order import PlatformSchema
from ucp_sdk.models.schemas.shopping.types import (
  fulfillment_group_create_request as fulfillment_group_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  fulfillment_method_create_request as fulfillment_method_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  item_create_request as item_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  line_item_create_request as line_item_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  shipping_destination_create_request as shipping_destination_req,
)

FLAGS = flags.FLAGS


class TestCheckout(
  BuyerConsentCheckoutResp,
  FulfillmentCheckout,
  DiscountCheckoutResp,
  Ap2Checkout,
):
  """Checkout model supporting Fulfillment, Discount, and AP2 extensions."""

  platform: PlatformSchema | None = None
  cart_id: str | None = None


class IntegrationTest(absltest.TestCase):
  """Integration tests for the UCP server application."""

  def setUp(self) -> None:
    """Set up the test environment, including temporary DBs and dependencies."""
    flags.FLAGS(["test"])
    super().setUp()
    # Create a temporary directory for test databases
    self.test_dir = Path(tempfile.mkdtemp())
    self.products_db = self.test_dir / "test_products.db"
    self.transactions_db = self.test_dir / "test_transactions.db"

    # Initialize local engines and session makers
    prod_url = f"sqlite+aiosqlite:///{self.products_db}"
    self.products_engine = create_async_engine(prod_url, echo=False)
    self.products_session_factory = sessionmaker(
      self.products_engine, expire_on_commit=False, class_=AsyncSession
    )

    trans_url = f"sqlite+aiosqlite:///{self.transactions_db}"
    self.transactions_engine = create_async_engine(trans_url, echo=False)
    self.transactions_session_factory = sessionmaker(
      self.transactions_engine, expire_on_commit=False, class_=AsyncSession
    )

    # Initialize DB schemas locally
    async def init_schemas() -> None:
      async with self.products_engine.begin() as conn:
        await conn.run_sync(db.ProductBase.metadata.create_all)
      async with self.transactions_engine.begin() as conn:
        await conn.run_sync(db.TransactionBase.metadata.create_all)

    asyncio.run(init_schemas())

    # Define dependency overrides
    async def override_get_products_db() -> AsyncGenerator[AsyncSession, None]:
      async with self.products_session_factory() as session:
        yield session

    async def override_get_transactions_db() -> AsyncGenerator[
      AsyncSession, None
    ]:
      async with self.transactions_session_factory() as session:
        yield session

    # Apply overrides
    app.dependency_overrides[dependencies.get_products_db] = (
      override_get_products_db
    )
    app.dependency_overrides[dependencies.get_transactions_db] = (
      override_get_transactions_db
    )

    # Initialize Client
    self.client = TestClient(app)

    self._seed_data()

  def tearDown(self) -> None:
    """Clean up the test environment."""
    # Clear overrides
    app.dependency_overrides.clear()

    # Dispose engines
    async def dispose_engines() -> None:
      await self.products_engine.dispose()
      await self.transactions_engine.dispose()

    asyncio.run(dispose_engines())

    shutil.rmtree(self.test_dir)
    super().tearDown()

  def get_resource_id(self, gid: str | None) -> str | None:
    """Get the resource_id from a GID."""
    if gid and gid.startswith("gid://"):
      return gid.split("/")[-1]
    return gid

  def _seed_data(self) -> None:
    """Seed initial test data synchronously."""
    with self.client:
      asyncio.run(self._async_seed())

  async def _async_seed(self) -> None:
    """Seed initial test data asynchronously."""
    # Seed Products using local session maker
    async with self.products_session_factory() as session:
      await session.execute(delete(db.Product))
      products = [
        db.Product(
          id="rose",
          title="Red Rose",
          price=1000,
          image_url="http://rose.com",
        ),
        db.Product(
          id="tulip",
          title="White Tulip",
          price=800,
          image_url="http://tulip.com",
        ),
      ]
      session.add_all(products)
      await session.commit()

    # Seed Inventory using local session maker
    async with self.transactions_session_factory() as session:
      await session.execute(delete(db.Inventory))
      inventory = [
        db.Inventory(product_id="rose", quantity=5),
        db.Inventory(product_id="tulip", quantity=2),
      ]
      session.add_all(inventory)
      await session.commit()

  def _get_headers(
    self,
    idempotency_key: str | None = None,
    request_id: str | None = None,
    exclude: list[str] | None = None,
  ) -> dict[str, str]:
    """Construct request headers with optional overrides."""
    headers = {
      "UCP-Agent": 'profile="https://agent.example/profile"',
      "request-signature": "test",
      "idempotency-key": idempotency_key or str(uuid.uuid4()),
      "request-id": request_id or str(uuid.uuid4()),
    }
    if exclude:
      for key in exclude:
        headers.pop(key, None)
    return headers

  def _create_checkout_payload(
    self,
    checkout_id: str,
    items: list[tuple[str, str, int, int]],
  ) -> checkout_create_req.CheckoutCreateRequest:
    """Create a checkout payload using SDK models."""
    line_items = []
    for item_id, _item_title, _item_price, quantity in items:
      item = item_create_req.ItemCreateRequest(id=item_id)
      line_item = line_item_create_req.LineItemCreateRequest(
        quantity=quantity, item=item
      )
      line_items.append(line_item)

    payment = payment_create_req.PaymentCreateRequest(instruments=[])

    # Hierarchical Fulfillment Construction
    destination = shipping_destination_req.ShippingDestinationCreateRequest(
      id="dest_1", address_country="US"
    )
    group = fulfillment_group_create_req.FulfillmentGroupCreateRequest(
      id="group_1",
      line_item_ids=[i_id for i_id, _, _, _ in items],
      selected_option_id="std-ship",
    )
    method = fulfillment_method_create_req.FulfillmentMethodCreateRequest(
      id="method_1",
      line_item_ids=[i_id for i_id, _, _, _ in items],
      type="shipping",
      destinations=[destination],
      selected_destination_id="dest_1",
      groups=[group],
    )
    fulfillment = {
      "methods": [
        method.model_dump(mode="json", exclude_none=True, by_alias=True)
      ]
    }

    return checkout_create_req.CheckoutCreateRequest(
      id=checkout_id,
      currency="USD",
      line_items=line_items,
      payment=payment,
      fulfillment=fulfillment,
    )

  def _create_payment_payload(self) -> dict:
    """Create a payment payload using SDK models."""
    payload = checkout_comp_req.CheckoutCompleteRequest(
      payment=payment_comp_req.PaymentCompleteRequest(
        instruments=[
          {
            "id": "instr_1",
            "handler_id": "mock_payment_handler",
            "type": "card",
            "display": {"brand": "Visa", "last_digits": "1234"},
            "credential": {"type": "token", "token": "success_token"},
          }
        ]
      ),
      risk_signals={},
    )
    return payload.model_dump(mode="json", exclude_none=True)

  def _perform_checkout_operation(
    self,
    operation: str,
    checkout_id: str,
    idempotency_key: str,
    request_id: str,
    request_body: dict | None,
  ):
    """Perform a checkout write operation for idempotency tests."""
    headers = self._get_headers(
      idempotency_key=idempotency_key,
      request_id=request_id,
    )
    if operation == "update":
      return self.client.put(
        f"/checkout-sessions/{checkout_id}",
        headers=headers,
        json=request_body,
      )
    if operation == "complete":
      return self.client.post(
        f"/checkout-sessions/{checkout_id}/complete",
        headers=headers,
        json=request_body,
      )
    if operation == "cancel":
      return self.client.post(
        f"/checkout-sessions/{checkout_id}/cancel",
        headers=headers,
      )
    raise ValueError(f"Unsupported checkout operation: {operation}")

  def test_single_item_checkout(self) -> None:
    """Test the full lifecycle of a single item checkout."""
    with self.client:
      # 1. Create Checkout
      payload = self._create_checkout_payload(
        "test_checkout_1", [("rose", "Red Rose", 1000, 2)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="1", request_id="1"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      checkout = TestCheckout.model_validate(response.json())
      # `id` is ucp_request: omit, so the server assigns it; follow-up
      # operations use the returned id.
      checkout_sid = self.get_resource_id(checkout.id)
      self.assertIsInstance(checkout_sid, str)
      self.assertEqual(checkout.status, "ready_for_complete")

      # 2. Complete Checkout
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(idempotency_key="2", request_id="2"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200, response.text)
      checkout = TestCheckout.model_validate(response.json())
      self.assertEqual(checkout.status, "completed")

      # Verify DB State: Inventory Decremented
      async def verify_inventory() -> int | None:
        async with self.transactions_session_factory() as session:
          qty = await db.get_inventory(session, "rose")
          return qty

      qty = asyncio.run(verify_inventory())
      # Original 5 - 2 sold = 3 remaining
      self.assertEqual(qty, 3, "Inventory should be decremented to 3")

      # 3. Verify Inventory Deduction
      # (Try to buy 4 more roses, only 3 should be left)
      payload = self._create_checkout_payload(
        "test_checkout_2", [("rose", "Red Rose", 1000, 4)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="3", request_id="3"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 400)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(len(data["messages"]), 1)
      self.assertIn("Insufficient stock", data["messages"][0]["content"])

  def test_double_complete_checkout(self) -> None:
    """Test that completing a checkout twice is idempotent."""
    with self.client:
      # 1. Create Checkout
      payload = self._create_checkout_payload(
        "test_checkout_double", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="1", request_id="1"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      checkout_sid = self.get_resource_id(response.json()["id"])

      # 2. Complete Checkout (First time)
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(idempotency_key="2", request_id="2"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200)

      # 3. Complete Checkout (Second time) - Should fail
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(idempotency_key="4", request_id="4"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 409)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(len(data["messages"]), 1)
      self.assertEqual(
        data["messages"][0]["content"],
        "Cannot complete checkout in state 'completed'",
      )

  def test_multi_item_checkout(self) -> None:
    """Tests checking out multiple items with inventory validation."""
    with self.client:
      # 1. Create Multi-item Checkout
      payload = self._create_checkout_payload(
        "test_checkout_multi",
        [("rose", "Red Rose", 1000, 1), ("tulip", "White Tulip", 800, 2)],
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="5", request_id="5"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      checkout_sid = self.get_resource_id(response.json()["id"])

      # 2. Complete Multi-item Checkout
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(idempotency_key="6", request_id="6"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200)

      # Verify DB State for Multi-item
      async def verify_multi_inventory() -> tuple[int | None, int | None]:
        async with self.transactions_session_factory() as session:
          qty_rose = await db.get_inventory(session, "rose")
          qty_tulip = await db.get_inventory(session, "tulip")
          return qty_rose, qty_tulip

      qty_rose, qty_tulip = asyncio.run(verify_multi_inventory())
      # 5 - 1 = 4
      self.assertEqual(qty_rose, 4, "Rose inventory should be 4 (5 - 1)")
      # 2 - 2 = 0
      self.assertEqual(qty_tulip, 0, "Tulip inventory should be 0 (2 - 2)")

  def test_shipping_event_matches_order_schema(self) -> None:
    """Simulated shipping persists a schema-valid fulfillment event."""
    with self.client:
      payload = self._create_checkout_payload(
        "shipping_event",
        [
          ("rose", "Red Rose", 1000, 2),
          ("tulip", "White Tulip", 800, 1),
        ],
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="shipping_event_1", request_id="shipping_event_1"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, response.text)
      checkout_sid = self.get_resource_id(response.json()["id"])

      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(
          idempotency_key="shipping_event_2", request_id="shipping_event_2"
        ),
        json=self._create_payment_payload(),
      )
      self.assertEqual(response.status_code, 200, response.text)
      order_id = response.json()["order"]["id"]

      headers = self._get_headers()
      headers["Simulation-Secret"] = FLAGS.simulation_secret
      response = self.client.post(
        f"/testing/simulate-shipping/{order_id}", headers=headers
      )
      self.assertEqual(response.status_code, 200, response.text)

      response = self.client.get(
        f"/orders/{order_id}", headers=self._get_headers()
      )
      self.assertEqual(response.status_code, 200, response.text)
      order_data = response.json()
      Order.model_validate(order_data)
      event = order_data["fulfillment"]["events"][-1]
      self.assertNotIn("timestamp", event)
      self.assertEqual(event["type"], "shipped")
      self.assertIn("occurred_at", event)
      self.assertEqual(
        event["line_items"],
        [
          {
            "id": line_item["id"],
            "quantity": line_item["quantity"]["total"],
          }
          for line_item in order_data["line_items"]
        ],
      )

  def test_missing_ucp_agent_header(self) -> None:
    """Tests that requests missing mandatory headers are rejected."""
    with self.client:
      payload = self._create_checkout_payload(
        "test_checkout_missing_header", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="7", request_id="7", exclude=["UCP-Agent"]
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      # Missing header should result in 422 Unprocessable Entity (FastAPI
      # default validation)
      self.assertEqual(response.status_code, 422)

  def test_discount_code_matches_case_insensitively(self) -> None:
    """Codes are matched case-insensitively by business (discount.md)."""

    async def seed_discount() -> None:
      async with self.transactions_session_factory() as session:
        await session.execute(delete(db.Discount))
        session.add(
          db.Discount(
            code="10OFF", type="percentage", value=10, description="10% Off"
          )
        )
        await session.commit()

    asyncio.run(seed_discount())

    with self.client:
      payload = self._create_checkout_payload(
        "test_checkout_discount_ci", [("rose", "Red Rose", 1000, 1)]
      )
      body = payload.model_dump(mode="json", exclude_none=True)
      # The seeded code is 10OFF; submit it lowercase on purpose.
      body["discounts"] = {"codes": ["10off"]}
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="dci-1", request_id="dci-1"),
        json=body,
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      data = response.json()
      applied = (data.get("discounts") or {}).get("applied") or []
      self.assertEqual(
        [a["code"] for a in applied],
        ["10OFF"],
        "a lowercase code must match the seeded uppercase code",
      )
      discount_totals = [
        t["amount"] for t in data.get("totals", []) if t["type"] == "discount"
      ]
      self.assertEqual(discount_totals, [-100], "10% of the 1000 subtotal")

  def test_discount_total_is_negative_and_receipt_reconciles(self) -> None:
    """A discount totals[] entry is negative and the receipt sums to total.

    Per discount.md, applied[].amount is the magnitude (always positive) while
    the corresponding totals[] entry is its signed effect on the receipt
    (negative for discounts); total.json constrains discount/items_discount
    amounts with exclusiveMaximum: 0. The subtotal plus the (negative) discount
    must therefore reconcile to the total.
    """

    async def seed_discount() -> None:
      async with self.transactions_session_factory() as session:
        await session.execute(delete(db.Discount))
        session.add(
          db.Discount(
            code="10OFF", type="percentage", value=10, description="10% Off"
          )
        )
        await session.commit()

    asyncio.run(seed_discount())

    with self.client:
      payload = self._create_checkout_payload(
        "test_checkout_discount_sign", [("rose", "Red Rose", 1000, 1)]
      )
      body = payload.model_dump(mode="json", exclude_none=True)
      body["discounts"] = {"codes": ["10OFF"]}
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="ds-1", request_id="ds-1"),
        json=body,
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      data = response.json()
      totals = {t["type"]: t["amount"] for t in data.get("totals", [])}

      # 1. The discount totals[] entry is strictly negative (total.json
      #    exclusiveMaximum: 0).
      self.assertLess(
        totals["discount"], 0, "discount totals[] entry must be negative"
      )
      # 2. applied[].amount stays positive (the magnitude, per discount.md).
      applied = (data.get("discounts") or {}).get("applied") or []
      self.assertTrue(
        applied and all(a["amount"] > 0 for a in applied),
        "applied[].amount is the positive magnitude",
      )
      # 3. The receipt reconciles: subtotal + discount == total.
      self.assertEqual(
        totals["subtotal"] + totals["discount"],
        totals["total"],
        "subtotal plus the signed discount must equal the total",
      )

  def test_discount_applied_is_not_duplicated_on_update(self) -> None:
    """An update that omits discounts must not duplicate discounts.applied.

    _recalculate_totals rebuilds checkout.totals from scratch on every
    create/update, but it appended to discounts.applied without first
    resetting it. Because the persisted (and reloaded) checkout already
    carries the applied entries from the previous response, an update that
    does not re-submit the discounts field accumulated a duplicate applied
    entry on every call. The server is the authority for applied discounts
    (discount.json marks applied as ucp_request:"omit"), so the list must be
    rebuilt idempotently, mirroring how totals is rebuilt.
    """

    async def seed_discount() -> None:
      async with self.transactions_session_factory() as session:
        await session.execute(delete(db.Discount))
        session.add(
          db.Discount(
            code="10OFF", type="percentage", value=10, description="10% Off"
          )
        )
        await session.commit()

    asyncio.run(seed_discount())

    with self.client:
      checkout_id = "test_checkout_discount_dup"
      # 1. Create with a discount code -> applied has exactly one entry.
      payload = self._create_checkout_payload(
        checkout_id, [("rose", "Red Rose", 1000, 1)]
      )
      body = payload.model_dump(mode="json", exclude_none=True)
      body["discounts"] = {"codes": ["10OFF"]}
      create = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="dup-1", request_id="dup-1"),
        json=body,
      )
      self.assertEqual(create.status_code, 201, f"Response: {create.text}")
      checkout_id = self.get_resource_id(create.json()["id"])
      applied = (create.json().get("discounts") or {}).get("applied") or []
      self.assertEqual(len(applied), 1, "create applies the discount once")

      # 2. Update without re-submitting discounts (e.g. a quantity/address
      #    change). applied must remain a single entry, not accumulate.
      update_body = payload.model_dump(mode="json", exclude_none=True)
      update = self.client.put(
        f"/checkout-sessions/{checkout_id}",
        headers=self._get_headers(idempotency_key="dup-2", request_id="dup-2"),
        json=update_body,
      )
      self.assertEqual(update.status_code, 200, f"Response: {update.text}")
      applied_after = (update.json().get("discounts") or {}).get(
        "applied"
      ) or []
      self.assertEqual(
        [a["code"] for a in applied_after],
        ["10OFF"],
        "the previously applied discount is retained",
      )
      self.assertEqual(
        len(applied_after),
        1,
        "update must not duplicate discounts.applied entries",
      )

      # 3. The receipt is still correct after the update: exactly one
      #    negative discount totals[] entry, and subtotal + discount == total
      #    (proves the totals rebuild and the applied rebuild stay in sync).
      totals_by_type: dict[str, int] = {}
      discount_total_entries = 0
      for t in update.json().get("totals", []):
        totals_by_type[t["type"]] = t["amount"]
        if t["type"] == "discount":
          discount_total_entries += 1
      self.assertEqual(discount_total_entries, 1, "one discount totals[] entry")
      self.assertEqual(
        totals_by_type.get("discount"), -100, "10% of the 1000 subtotal"
      )
      self.assertEqual(
        totals_by_type.get("subtotal") + totals_by_type.get("discount"),
        totals_by_type.get("total"),
        "subtotal plus the signed discount must equal the total",
      )

  def test_cancel_checkout(self) -> None:
    """Tests the checkout cancellation flow."""
    with self.client:
      # 1. Create Checkout
      payload = self._create_checkout_payload(
        "test_checkout_cancel", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="cancel_1", request_id="cancel_1"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      checkout_sid = self.get_resource_id(response.json()["id"])

      # 2. Cancel Checkout
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/cancel",
        headers=self._get_headers(
          idempotency_key="cancel_2", request_id="cancel_2"
        ),
      )
      self.assertEqual(response.status_code, 200)
      checkout = TestCheckout.model_validate(response.json())
      self.assertEqual(checkout.status, "canceled")

      # 3. Try to Cancel again (should fail)
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/cancel",
        headers=self._get_headers(
          idempotency_key="cancel_3", request_id="cancel_3"
        ),
      )
      self.assertEqual(response.status_code, 409)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(len(data["messages"]), 1)
      self.assertIn("Cannot cancel checkout", data["messages"][0]["content"])

      # 4. Create another checkout and complete it, then try to cancel
      payload = self._create_checkout_payload(
        "test_checkout_cancel_completed", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="cancel_4", request_id="cancel_4"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      completed_sid = self.get_resource_id(response.json()["id"])

      # Complete it
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{completed_sid}/complete",
        headers=self._get_headers(
          idempotency_key="cancel_5", request_id="cancel_5"
        ),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200)

      # Try to cancel completed checkout
      response = self.client.post(
        f"/checkout-sessions/{completed_sid}/cancel",
        headers=self._get_headers(
          idempotency_key="cancel_6", request_id="cancel_6"
        ),
      )
      self.assertEqual(response.status_code, 409)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(len(data["messages"]), 1)
      self.assertIn("Cannot cancel checkout", data["messages"][0]["content"])

  def test_idempotency_key_is_scoped_to_operation_and_checkout(self) -> None:
    """An idempotency key only replays the exact same checkout operation."""
    with self.client:
      for operation in ("update", "complete", "cancel"):
        with self.subTest(operation=operation):
          # The server assigns the checkout ids; the labels only scope the
          # idempotency keys of the create calls.
          server_ids: dict[str, str] = {}
          for label in ("first", "second"):
            payload = self._create_checkout_payload(
              f"idempotency_{operation}_{label}",
              [("rose", "Red Rose", 1000, 1)],
            )
            response = self.client.post(
              "/checkout-sessions",
              headers=self._get_headers(
                idempotency_key=f"create_idempotency_{operation}_{label}",
                request_id=f"create_idempotency_{operation}_{label}",
              ),
              json=payload.model_dump(mode="json", exclude_none=True),
            )
            self.assertEqual(response.status_code, 201, response.text)
            server_ids[label] = self.get_resource_id(response.json()["id"])
          first_checkout_id = server_ids["first"]
          second_checkout_id = server_ids["second"]

          shared_key = f"shared_{operation}_key"
          request_body = None
          if operation == "update":
            request_body = {
              "line_items": [
                {
                  "id": "shared_line_item",
                  "quantity": 2,
                  "item": {"id": "rose"},
                }
              ]
            }
          elif operation == "complete":
            request_body = self._create_payment_payload()

          first_response = self._perform_checkout_operation(
            operation,
            first_checkout_id,
            shared_key,
            f"{operation}_first",
            request_body,
          )
          self.assertEqual(first_response.status_code, 200, first_response.text)

          replay_response = self._perform_checkout_operation(
            operation,
            first_checkout_id,
            shared_key,
            f"{operation}_replay",
            request_body,
          )
          self.assertEqual(
            replay_response.status_code, 200, replay_response.text
          )
          self.assertEqual(replay_response.json(), first_response.json())

          conflict_response = self._perform_checkout_operation(
            operation,
            second_checkout_id,
            shared_key,
            f"{operation}_second",
            request_body,
          )
          self.assertEqual(
            conflict_response.status_code, 409, conflict_response.text
          )
          self.assertEqual(
            conflict_response.json()["messages"][0]["code"],
            "IDEMPOTENCY_CONFLICT",
          )

          second_checkout = self.client.get(
            f"/checkout-sessions/{second_checkout_id}",
            headers=self._get_headers(
              idempotency_key=f"get_{second_checkout_id}",
              request_id=f"get_{second_checkout_id}",
            ),
          )
          self.assertEqual(
            second_checkout.status_code, 200, second_checkout.text
          )
          second_checkout_data = second_checkout.json()
          self.assertEqual(second_checkout_data["status"], "ready_for_complete")
          self.assertEqual(second_checkout_data["line_items"][0]["quantity"], 1)

  def _notify_and_capture(
    self,
    checkout: UnifiedCheckout,
    event_type: str,
    respond: list | None = None,
  ) -> list[dict]:
    """Fire _notify_webhook with httpx stubbed and return captured POSTs.

    ``respond`` optionally scripts the receiver, one entry per delivery
    attempt: an int becomes that HTTP status, an Exception instance is
    raised as a transport failure. Defaults to a single 200.
    """
    captured: list[dict] = []

    async def run() -> None:
      async with (
        self.products_session_factory() as products_session,
        self.transactions_session_factory() as transactions_session,
      ):
        service = CheckoutService(
          FulfillmentService(),
          products_session,
          transactions_session,
          "http://testserver",
        )
        with respx.mock:
          if respond is None:
            route = respx.post().respond(200)
          else:
            route = respx.post().mock(
              side_effect=[
                r if isinstance(r, Exception) else httpx.Response(r)
                for r in respond
              ]
            )
          await service._notify_webhook(checkout, event_type)
          if route.called:
            for call in route.calls:
              request = call.request
              body = json.loads(request.content) if request.content else None
              captured.append(
                {
                  "url": str(request.url),
                  "json": body,
                  "content": request.content,
                  "headers": request.headers,
                }
              )

    asyncio.run(run())
    return captured

  def test_webhook_delivers_the_bare_order_as_body(self) -> None:
    """The order-event webhook body is the order object, per rest.openapi.json.

    webhooks.orderEvent.post.requestBody references #/components/schemas/order,
    so the delivered JSON must be the order itself (every required top-level
    field present) with the event type carried in the X-Event-Type header --
    never a custom {event_type, checkout_id, order} envelope.
    """
    with self.client:
      # Drive a real create + complete so the server persists a real order.
      payload = self._create_checkout_payload(
        "wh_order_placed", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="wh1", request_id="wh1"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, response.text)
      checkout_sid = self.get_resource_id(response.json()["id"])

      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{checkout_sid}/complete",
        headers=self._get_headers(idempotency_key="wh2", request_id="wh2"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200, response.text)

      checkout = UnifiedCheckout.model_validate(response.json())
      self.assertIsNotNone(
        checkout.order, "completed checkout must carry an order"
      )
      checkout.platform = PlatformSchema(
        webhook_url="https://platform.example/ucp-webhook"
      )

    captured = self._notify_and_capture(checkout, "order_placed")

    self.assertEqual(len(captured), 1, "exactly one webhook must be delivered")
    delivered = captured[0]
    self.assertEqual(delivered["url"], "https://platform.example/ucp-webhook")
    # The event type travels in the header, not the body.
    self.assertEqual(delivered["headers"].get("X-Event-Type"), "order_placed")

    self.assertIn("Webhook-Id", delivered["headers"])
    uuid_str = delivered["headers"]["Webhook-Id"]
    try:
      uuid.UUID(uuid_str)
    except ValueError:
      self.fail(f"Webhook-Id {uuid_str} is not a valid UUID")

    self.assertIn("Webhook-Timestamp", delivered["headers"])
    timestamp_str = delivered["headers"]["Webhook-Timestamp"]
    try:
      timestamp = int(timestamp_str)
    except ValueError:
      self.fail(f"Webhook-Timestamp {timestamp_str} is not a valid integer")

    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    self.assertLess(
      abs(now - timestamp),
      5,
      f"Webhook-Timestamp ({timestamp}) should be close to now ({now})",
    )

    body = delivered["json"]
    # The body IS an order: it validates and carries every required field.
    Order.model_validate(body)
    for field in (
      "ucp",
      "id",
      "checkout_id",
      "permalink_url",
      "line_items",
      "fulfillment",
      "currency",
      "totals",
    ):
      self.assertIn(field, body, f"order body missing required '{field}'")
    # And it is NOT the old {event_type, checkout_id, order} envelope.
    self.assertNotIn("event_type", body)
    self.assertNotIn("order", body)

  def test_webhook_is_skipped_when_there_is_no_order(self) -> None:
    """No webhook is delivered when the checkout has no order to send.

    The body must always be a valid order, so an absent order must never be
    posted (the old envelope posted a body of {"order": null}).
    """
    with self.client:
      payload = self._create_checkout_payload(
        "wh_no_order", [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="wh3", request_id="wh3"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, response.text)
      # A created-but-not-completed checkout has no order yet.
      checkout = UnifiedCheckout.model_validate(response.json())
      self.assertIsNone(checkout.order)
      checkout.platform = PlatformSchema(
        webhook_url="https://platform.example/ucp-webhook"
      )

    captured = self._notify_and_capture(checkout, "order_placed")
    self.assertEqual(captured, [], "no webhook may be sent without an order")

  def _completed_checkout(
    self, checkout_id: str, webhook_url: str
  ) -> UnifiedCheckout:
    """Drive create + complete so a real order exists; set the webhook URL."""
    with self.client:
      payload = self._create_checkout_payload(
        checkout_id, [("rose", "Red Rose", 1000, 1)]
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key=f"{checkout_id}_create",
          request_id=f"{checkout_id}_create",
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, response.text)
      # The server assigns the checkout id (#167); the client-supplied id in
      # the payload is not honored, so complete against the id the create
      # response actually returned.
      server_id = response.json()["id"]
      response = self.client.post(
        f"/checkout-sessions/{server_id}/complete",
        headers=self._get_headers(
          idempotency_key=f"{checkout_id}_complete",
          request_id=f"{checkout_id}_complete",
        ),
        json=self._create_payment_payload(),
      )
      self.assertEqual(response.status_code, 200, response.text)
    checkout = UnifiedCheckout.model_validate(response.json())
    self.assertIsNotNone(checkout.order)
    checkout.platform = PlatformSchema(webhook_url=webhook_url)
    return checkout

  def test_webhook_delivery_carries_the_signature_headers(self) -> None:
    """Every delivery carries the four required signature headers.

    order.md, Webhook Signature Verification: webhook payloads MUST be
    signed; UCP-Agent (the business profile URL), Signature,
    Signature-Input, and Content-Digest are required headers on every
    delivery.
    """
    checkout = self._completed_checkout(
      "wh_signed", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(checkout, "order_placed")
    self.assertEqual(len(captured), 1)
    headers = captured[0]["headers"]
    for name in ("UCP-Agent", "Signature", "Signature-Input", "Content-Digest"):
      self.assertIn(name, headers, f"delivery is missing {name}")
    # The UCP-Agent profile member is the business's own well-known URL
    # (signatures.md, UCP-Agent parsing rule 4 for business profiles).
    self.assertEqual(
      headers["UCP-Agent"],
      'profile="http://testserver/.well-known/ucp"',
    )

  def test_webhook_signature_verifies_against_the_published_key(self) -> None:
    """The platform-side verification loop closes on the raw wire bytes.

    order.md, Verification (Platform): Content-Digest matches the SHA-256 of
    the raw body, and the signature verifies against the key the business
    publishes in its profile's signing_keys with the declared kid. This test
    IS that platform: it discovers the profile from the server and runs the
    server's own verify path over the captured delivery.
    """
    checkout = self._completed_checkout(
      "wh_verify", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(checkout, "order_placed")
    self.assertEqual(len(captured), 1)
    delivered = captured[0]
    raw = delivered["content"]
    headers = {k.lower(): v for k, v in delivered["headers"].items()}

    self.assertTrue(
      ucp_signing.content_digest_matches(headers["content-digest"], raw),
      "Content-Digest must cover the exact raw body bytes on the wire",
    )

    with self.client:
      profile = self.client.get("/.well-known/ucp").json()
    keys = profile.get("signing_keys")
    self.assertTrue(keys, "profile must publish signing_keys for verifiers")

    split = urlsplit(delivered["url"])
    keyid = ucp_signing.verify_request(
      "POST", split.netloc, split.path, split.query, headers, raw, keys
    )
    self.assertEqual(keyid, webhook_signer.public_jwk()["kid"])

    # Kill direction: a tampered body must NOT verify.
    with self.assertRaises(ucp_signing.SignatureError):
      ucp_signing.verify_request(
        "POST",
        split.netloc,
        split.path,
        split.query,
        headers,
        raw + b" ",
        keys,
      )

  def test_webhook_signed_components_cover_identity_and_event(self) -> None:
    """The signed set covers the spec table plus the webhook headers.

    signatures.md, REST Request Signing: @method/@authority/@path always;
    @query when the platform URL has one; content-digest/content-type for
    the body; idempotency-key on a state-changing POST; ucp-agent when the
    header is present. Webhook-Id, Webhook-Timestamp, and X-Event-Type are
    additionally bound: every header this server adds to the delivery is
    signed, so the event identity the platform dedupes and dispatches on
    cannot be altered in transit.
    """
    checkout = self._completed_checkout(
      "wh_components", "https://platform.example/ucp-webhook?token=t1"
    )
    captured = self._notify_and_capture(checkout, "order_placed")
    self.assertEqual(len(captured), 1)
    delivered = captured[0]
    # The delivery reaches the URL exactly as the platform provided it.
    self.assertEqual(
      delivered["url"], "https://platform.example/ucp-webhook?token=t1"
    )
    parsed = ucp_signing.parse_signature_input(
      delivered["headers"]["Signature-Input"]
    )
    self.assertIsNotNone(parsed)
    components = set(next(iter(parsed.values()))["components"])
    self.assertLessEqual(
      {
        "@method",
        "@authority",
        "@path",
        "@query",
        "content-digest",
        "content-type",
        "idempotency-key",
        "ucp-agent",
        "webhook-id",
        "webhook-timestamp",
        "x-event-type",
      },
      components,
    )
    # Every signed header component is actually present on the delivery.
    for name in (
      "Idempotency-Key",
      "Webhook-Id",
      "Webhook-Timestamp",
      "X-Event-Type",
    ):
      self.assertIn(name, delivered["headers"])

  def test_webhook_retries_after_5xx_and_succeeds(self) -> None:
    """A 5xx from the receiver triggers a retry that then succeeds.

    order.md, Guidelines (Business): MUST retry failed webhook deliveries.
    The retry is the SAME event: Webhook-Id and Idempotency-Key are stable
    across attempts so the platform can deduplicate, and every attempt is
    signed.
    """
    config.FLAGS.webhook_retry_backoff_seconds = 0.01
    checkout = self._completed_checkout(
      "wh_retry", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(
      checkout, "order_placed", respond=[500, 200]
    )
    self.assertEqual(
      len(captured), 2, "a failed delivery must be retried once it 5xxes"
    )
    first, second = captured
    self.assertEqual(
      first["headers"]["Webhook-Id"], second["headers"]["Webhook-Id"]
    )
    self.assertEqual(
      first["headers"]["Idempotency-Key"],
      second["headers"]["Idempotency-Key"],
    )
    for attempt in captured:
      self.assertIn("Signature", attempt["headers"])
      self.assertEqual(attempt["json"]["id"], checkout.order.id)

  def test_webhook_retries_after_connection_error(self) -> None:
    """A transport failure (connection refused/reset) is also retried."""
    config.FLAGS.webhook_retry_backoff_seconds = 0.01
    checkout = self._completed_checkout(
      "wh_conn_retry", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(
      checkout,
      "order_placed",
      respond=[httpx.ConnectError("connection refused"), 200],
    )
    self.assertEqual(len(captured), 2)

  def test_webhook_retries_are_bounded(self) -> None:
    """A receiver that keeps failing sees a bounded number of attempts.

    The retry MUST terminate: exactly --webhook_delivery_attempts POSTs,
    and the failure never escapes into the checkout flow.
    """
    config.FLAGS.webhook_retry_backoff_seconds = 0.01
    checkout = self._completed_checkout(
      "wh_bounded", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(
      checkout, "order_placed", respond=[500] * 10
    )
    self.assertEqual(len(captured), config.FLAGS.webhook_delivery_attempts)

  def test_webhook_4xx_is_not_retried(self) -> None:
    """A 4xx is a permanent rejection of this delivery: exactly one POST.

    Retrying a request the receiver deemed invalid cannot succeed and turns
    a bad delivery into a retry storm; only transport failures and 5xx are
    transient.
    """
    config.FLAGS.webhook_retry_backoff_seconds = 0.01
    checkout = self._completed_checkout(
      "wh_4xx", "https://platform.example/ucp-webhook"
    )
    captured = self._notify_and_capture(
      checkout, "order_placed", respond=[400, 200]
    )
    self.assertEqual(len(captured), 1)

  def test_bad_webhook_signing_key_fails_at_startup(self) -> None:
    """A misconfigured signing key aborts server startup loudly.

    Loading the key only at delivery time would swallow the configuration
    error into a per-webhook log line and silently degrade every delivery;
    the operator asked for a specific signing identity, so a key that
    cannot be loaded must fail the boot, not the webhooks.
    """
    config.FLAGS.webhook_signing_key = "/nonexistent/key.pem"
    webhook_signer.reset()
    try:
      with self.assertRaises(OSError), TestClient(app):
        pass
    finally:
      config.FLAGS.webhook_signing_key = None
      webhook_signer.reset()

  def test_profile_publishes_the_webhook_signing_key(self) -> None:
    """The served profile publishes the webhook public key for verifiers.

    signatures.md, Key Discovery: public keys live in the profile's
    signing_keys[] (a top-level sibling of `ucp` per the discovery profile
    schema). It is also mirrored into ucp.keys[], the JWK Set this server's
    own verifier resolves.
    """
    with self.client:
      profile = self.client.get("/.well-known/ucp").json()
    jwk = webhook_signer.public_jwk()
    self.assertIn(jwk, profile.get("signing_keys", []))
    self.assertIn(jwk, profile.get("ucp", {}).get("keys", []))

  def test_version_invalid_format(self) -> None:
    """Tests that UCP-Agent with invalid version format is rejected."""
    with self.client:
      payload = self._create_checkout_payload(
        "test_version_invalid", [("rose", "Red Rose", 1000, 1)]
      )
      headers = self._get_headers(idempotency_key="ver_1", request_id="ver_1")
      headers["UCP-Agent"] = (
        'profile="https://agent.example/profile"; version="bad-version"'
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=headers,
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 422)

      # Verify the error structure matches UcpErrorResponse
      data = response.json()
      self.assertNotIn("detail", data)
      expected = UcpErrorResponse(
        ucp={"version": app.version, "status": "error"},
        messages=[
          UcpMessageError(
            type=MessageType.ERROR,
            code="VERSION_INVALID_FORMAT",
            content=("Version 'bad-version' is invalid. Expected YYYY-MM-DD."),
            severity=ErrorSeverity.UNRECOVERABLE,
          )
        ],
      )
      self.assertEqual(UcpErrorResponse.model_validate(data), expected)

  def test_version_unsupported(self) -> None:
    """Tests that UCP-Agent with unsupported (newer) version is rejected."""
    with self.client:
      payload = self._create_checkout_payload(
        "test_version_unsupported", [("rose", "Red Rose", 1000, 1)]
      )
      headers = self._get_headers(idempotency_key="ver_2", request_id="ver_2")
      unsupported_version = datetime.date.fromisoformat(
        app.version
      ) + datetime.timedelta(1)
      headers["UCP-Agent"] = (
        'profile="https://agent.example/profile"; '
        f'version="{unsupported_version}"'
      )
      response = self.client.post(
        "/checkout-sessions",
        headers=headers,
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 422)

      # Verify the error structure matches UcpErrorResponse
      data = response.json()
      self.assertNotIn("detail", data)
      expected = UcpErrorResponse(
        ucp={"version": app.version, "status": "error"},
        messages=[
          UcpMessageError(
            type=MessageType.ERROR,
            code="VERSION_UNSUPPORTED",
            content=(
              f"Version {unsupported_version} is not supported. This merchant"
              f" implements version {app.version}."
            ),
            severity=ErrorSeverity.UNRECOVERABLE,
          )
        ],
      )
      self.assertEqual(UcpErrorResponse.model_validate(data), expected)

  def test_profile_includes_cache_control_header(self) -> None:
    """Profiles must be served cacheable (overview.md, profile caching).

    The Cache-Control header must be `public` with `max-age` of at least 60
    seconds, and must not use `private`, `no-store`, or `no-cache`.
    """
    with self.client:
      response = self.client.get("/.well-known/ucp")
      self.assertEqual(response.status_code, 200)
      cache_control = response.headers.get("Cache-Control", "")
      directives = [d.strip().lower() for d in cache_control.split(",")]
      self.assertIn("public", directives)
      max_age = next(
        (
          int(d.split("=", 1)[1])
          for d in directives
          if d.startswith("max-age=") and d.split("=", 1)[1].isdigit()
        ),
        None,
      )
      self.assertIsNotNone(
        max_age, "profile Cache-Control must include a numeric max-age"
      )
      self.assertGreaterEqual(max_age, 60)
      for forbidden in ("private", "no-store", "no-cache"):
        self.assertNotIn(forbidden, directives)

  def test_create_omitting_server_determined_fields(self) -> None:
    """A conformant create sends only line_items.

    checkout.json marks currency (and id, status, totals, links) with
    `ucp_request: omit`, describing currency as derived from address, context
    and geo IP because merchants determine it. The generated
    CheckoutCreateRequest carries no currency field for that reason, so a
    platform following the schema sends neither.

    The other tests build their payload with _create_checkout_payload, which
    sets id and currency; extra="allow" keeps them, so checkout_req.currency
    always resolves and this path is never exercised.
    """
    with self.client:
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="omit1", request_id="omit1"),
        json={"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      self.assertIsInstance(
        body.get("currency"),
        str,
        "server must determine a currency when the platform omits it",
      )

  def test_update_omitting_server_determined_fields(self) -> None:
    """The update path reads the same omitted field and must not fail."""
    with self.client:
      created = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="omit2", request_id="omit2"),
        json={"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
      )
      self.assertEqual(created.status_code, 201, f"Response: {created.text}")
      checkout_id = self.get_resource_id(created.json()["id"])
      updated = self.client.put(
        f"/checkout-sessions/{checkout_id}",
        headers=self._get_headers(idempotency_key="omit3", request_id="omit3"),
        json={"line_items": [{"item": {"id": "rose"}, "quantity": 2}]},
      )
      self.assertEqual(updated.status_code, 200, f"Response: {updated.text}")

  def test_create_assigns_id_server_side(self) -> None:
    """A create carrying a non-string top-level `id` must not 500.

    checkout.json marks `id` with `ucp_request: omit` -- the business assigns
    it -- so the generated CheckoutCreateRequest declares no id field, and a
    request carrying one of any JSON type is still schema-valid because
    extra="allow" admits it as an extra member. create_checkout read that
    extra attribute and passed it into the Checkout response model verbatim,
    so `"id": 123` raised an uncaught pydantic ValidationError (HTTP 500).
    Same defect class as the currency read fixed in #156: the server
    determines the value and never takes it from the request.
    """

    def _body(**extra: object) -> dict:
      body = {
        "currency": "USD",
        "line_items": [
          {
            "id": "li_1",
            "quantity": 1,
            "item": {"id": "rose", "price": 1000},
            "totals": [],
          }
        ],
        "payment": {"instruments": [], "handlers": []},
        "status": "incomplete",
        "ucp": {"version": "2026-04-08"},
        "totals": [],
        "links": [],
      }
      body.update(extra)
      return body

    with self.client:
      # A non-string id is schema-valid (id is omit, so it arrives as an
      # extra member) and must never 500.
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="sid1", request_id="sid1"),
        json=_body(id=123),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      self.assertIsInstance(
        response.json().get("id"),
        str,
        "server must assign a string id when the platform sends a non-string",
      )

      # A string id is ignored the same way: the server assigns its own.
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="sid2", request_id="sid2"),
        json=_body(id="client_chosen_id"),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      self.assertIsInstance(body.get("id"), str)
      self.assertNotIn(
        "client_chosen_id",
        body["id"],
        "id is ucp_request: omit, so the server assigns it",
      )

      # Omitted id keeps working (the conformant request).
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="sid3", request_id="sid3"),
        json=_body(),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      self.assertIsInstance(response.json().get("id"), str)

  def test_create_does_not_adopt_client_supplied_omit_members(self) -> None:
    """A create carrying ucp_request: omit members must not adopt them.

    checkout.json marks continue_url, expires_at, messages and order as
    ucp_request: omit, so the business owns them on the response. The create
    handler must drop them from the request payload so they never echo in
    the 201 response or persist into the stored session.
    """
    client_values = {
      "continue_url": "https://platform.example/client-chosen",
      "expires_at": "2030-01-01T00:00:00Z",
      "messages": [
        {
          "type": "info",
          "code": "custom",
          "content": "client supplied text",
          "severity": "recoverable",
        }
      ],
      "order": {
        "id": "order_client_chosen",
        "checkout_session_id": "fake",
        "permalink_url": "https://platform.example/order",
      },
    }

    with self.client:
      payload = self._create_checkout_payload(
        "test_omit_members", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      payload.update(client_values)

      headers = self._get_headers(idempotency_key="omit_1", request_id="omit_1")
      response = self.client.post(
        "/checkout-sessions",
        headers=headers,
        json=payload,
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()

      self.assertNotEqual(
        body.get("continue_url"),
        client_values["continue_url"],
        "continue_url is business owned",
      )
      self.assertNotEqual(
        body.get("expires_at"),
        client_values["expires_at"],
        "expires_at is business owned",
      )
      contents = [
        m.get("content")
        for m in body.get("messages", [])
        if isinstance(m, dict)
      ]
      self.assertNotIn(
        "client supplied text",
        contents,
        "messages are business owned",
      )
      order = body.get("order") or {}
      self.assertNotEqual(
        order.get("id"),
        client_values["order"]["id"],
        "order is business owned",
      )

      # Verify persistence: read session back with GET
      checkout_id = self.get_resource_id(body["id"])
      get_res = self.client.get(
        f"/checkout-sessions/{checkout_id}",
        headers=headers,
      )
      self.assertEqual(get_res.status_code, 200, f"Response: {get_res.text}")
      stored = get_res.json()
      self.assertNotEqual(
        stored.get("continue_url"), client_values["continue_url"]
      )
      self.assertNotEqual(stored.get("expires_at"), client_values["expires_at"])
      stored_contents = [
        m.get("content")
        for m in stored.get("messages", [])
        if isinstance(m, dict)
      ]
      self.assertNotIn("client supplied text", stored_contents)
      stored_order = stored.get("order") or {}
      self.assertNotEqual(stored_order.get("id"), client_values["order"]["id"])

  def test_create_ignores_client_currency_and_non_string_currency(
    self,
  ) -> None:
    """Create with client/non-string currency must not override or 500.

    checkout.json marks currency with ucp_request: omit -- the merchant
    determines it via config.get_default_currency(). Client-supplied string
    currency (e.g. 'XTS') must be ignored, and non-string currency (e.g. 123)
    must not raise ValidationError.
    """
    with self.client:
      # Client-supplied string currency is ignored (default 'USD' is used).
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="curr_1", request_id="curr_1"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
          "currency": "XTS",
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      self.assertEqual(response.json().get("currency"), "USD")

      # Non-string currency does not cause 500 ValidationError.
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="curr_2", request_id="curr_2"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
          "currency": 123,
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      self.assertEqual(response.json().get("currency"), "USD")

  def test_create_ignores_client_line_item_id_and_non_string_id(self) -> None:
    """Create with line_items[].id assigns server ID; non-string never 500.

    types/line_item.json marks id with create: omit -- the server assigns it.
    Client-supplied string id is ignored, and non-string id does not raise
    ValidationError.
    """
    with self.client:
      # Client-supplied string line item id is ignored (server assigns UUID).
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="li_id_1", request_id="li_id_1"
        ),
        json={
          "line_items": [
            {"item": {"id": "rose"}, "quantity": 1, "id": "client_line_1"}
          ],
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      line_items = body.get("line_items", [])
      self.assertEqual(len(line_items), 1)
      self.assertIsInstance(line_items[0].get("id"), str)
      self.assertNotEqual(line_items[0].get("id"), "client_line_1")

      # Non-string line item id does not cause 500 ValidationError.
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="li_id_2", request_id="li_id_2"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1, "id": 123}],
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      line_items = body.get("line_items", [])
      self.assertEqual(len(line_items), 1)
      self.assertIsInstance(line_items[0].get("id"), str)

  def test_create_checkout_with_attribution(self) -> None:
    """A checkout create carrying attribution returns 201 and persists."""
    attribution_data = {
      "campaign_id": "18234567890",
      "campaign_source": "google",
      "campaign_medium": "cpc",
      "campaign_name": "spring_2026",
      "gclid": "EAIaIQobChMI...",
    }
    with self.client:
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="attr_1", request_id="attr_1"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
          "attribution": attribution_data,
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      self.assertIsNotNone(body.get("attribution"))
      self.assertEqual(
        body.get("attribution", {}).get("campaign_id"), "18234567890"
      )

      # Verify persistence
      checkout_id = self.get_resource_id(body["id"])
      get_res = self.client.get(
        f"/checkout-sessions/{checkout_id}",
        headers=self._get_headers(request_id="attr_1_get"),
      )
      self.assertEqual(get_res.status_code, 200, f"Response: {get_res.text}")
      stored = get_res.json()
      self.assertEqual(
        stored.get("attribution", {}).get("campaign_id"), "18234567890"
      )

  def test_validation_failure_answers_with_ucp_envelope(self) -> None:
    """A validation failure answers with the UCP envelope, not detail."""
    with self.client:
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="val_err_1", request_id="val_err_1"
        ),
        json={"line_items": "not-an-array"},
      )
      self.assertEqual(response.status_code, 422)
      self.assertIn(
        "application/json", response.headers.get("content-type", "")
      )
      data = response.json()
      self.assertNotIn("detail", data, "flat detail shape must be gone")
      self.assertEqual(
        data.get("ucp", {}).get("status"), "error", "ucp.status must be 'error'"
      )
      self.assertEqual(data.get("ucp", {}).get("version"), app.version)
      messages = data.get("messages", [])
      self.assertTrue(
        isinstance(messages, list) and len(messages) > 0,
        "messages[] must carry the failure",
      )
      msg = messages[0]
      self.assertEqual(msg.get("type"), "error")
      self.assertEqual(msg.get("code"), "INVALID_REQUEST")
      self.assertEqual(msg.get("severity"), "unrecoverable")
      self.assertIn(
        "line_items",
        msg.get("content", ""),
        "content must name the offending member",
      )

  def test_update_applies_payment_instruments(self) -> None:
    """An update carrying payment.instruments must apply them, not 500.

    checkout.json marks `payment` as `ucp_request: {update: "optional"}`, and
    checkout.md says submitting payment populates payment.instruments with
    the collected instrument data -- update is a normal place for a platform
    to submit payment. update_checkout built the response instead as
    `PaymentResponse(instruments=checkout_req.payment.instruments)`, handing
    the response model a list of
    payment_instrument_update_request.SelectedPaymentInstrument instances.
    The response model is typed for the sibling response class
    payment_instrument.SelectedPaymentInstrument, so pydantic rejects the
    construction as an unhandled ValidationError -- a bare 500, not the UCP
    error envelope, whenever a request supplies a non-empty instruments
    array. An update that omits payment (or sends instruments: []) never
    exercises the mismatch, which is why this shipped unnoticed.
    """
    with self.client:
      created = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="pay_upd_1", request_id="pay_upd_1"
        ),
        json={"line_items": [{"item": {"id": "rose"}, "quantity": 1}]},
      )
      self.assertEqual(created.status_code, 201, f"Response: {created.text}")
      checkout_id = self.get_resource_id(created.json()["id"])

      instrument = {
        "id": "instr_upd_1",
        "handler_id": "mock_payment_handler",
        "type": "card",
        "display": {"brand": "Visa", "last_digits": "4242"},
        "selected": True,
      }
      updated = self.client.put(
        f"/checkout-sessions/{checkout_id}",
        headers=self._get_headers(
          idempotency_key="pay_upd_2", request_id="pay_upd_2"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
          "payment": {"instruments": [instrument]},
        },
      )
      self.assertEqual(
        updated.status_code,
        200,
        f"an update carrying payment.instruments must not 500: {updated.text}",
      )
      returned = (updated.json().get("payment") or {}).get("instruments") or []
      self.assertEqual(
        len(returned), 1, "the submitted instrument must be applied"
      )
      self.assertEqual(returned[0].get("id"), "instr_upd_1")
      self.assertEqual(returned[0].get("handler_id"), "mock_payment_handler")
      self.assertEqual(returned[0].get("type"), "card")
      self.assertEqual(
        returned[0].get("display"),
        {"brand": "Visa", "last_digits": "4242"},
      )
      self.assertTrue(returned[0].get("selected"))

  def test_create_applies_payment_instruments(self) -> None:
    """A create carrying payment.instruments must apply them, not 500.

    Same class as test_update_applies_payment_instruments: create_checkout
    builds `PaymentResponse(instruments=checkout_req.payment.instruments)`
    from the create request, handing the response model a list of
    payment_instrument_create_request.SelectedPaymentInstrument instances
    instead of the response class it declares. Every existing create test
    that touches payment sends `instruments: []`, so the mismatch never
    triggers pydantic's model-type check.
    """
    with self.client:
      instrument = {
        "id": "instr_create_1",
        "handler_id": "mock_payment_handler",
        "type": "card",
        "display": {"brand": "Visa", "last_digits": "4242"},
        "selected": True,
      }
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="pay_create_1", request_id="pay_create_1"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
          "payment": {"instruments": [instrument]},
        },
      )
      self.assertEqual(
        response.status_code,
        201,
        f"a create carrying payment.instruments must not 500: {response.text}",
      )
      returned = (response.json().get("payment") or {}).get("instruments") or []
      self.assertEqual(
        len(returned), 1, "the submitted instrument must be applied"
      )
      self.assertEqual(returned[0].get("id"), "instr_create_1")
      self.assertEqual(returned[0].get("handler_id"), "mock_payment_handler")
      self.assertEqual(returned[0].get("type"), "card")


if __name__ == "__main__":
  absltest.main()
