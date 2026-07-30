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

from absl import flags
from absl.testing import absltest
import db
import dependencies
from fastapi.testclient import TestClient
import respx
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
from ucp_sdk.models.schemas.shopping.types import (
  payment_instrument as payment_instr_type,
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
  shipping_destination as shipping_destination_req,
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
    destination = shipping_destination_req.ShippingDestination(
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
          payment_instr_type.SelectedPaymentInstrument(
            id="instr_1",
            handler_id="mock_payment_handler",
            type="card",
            display={"brand": "Visa", "last_digits": "1234"},
            credential={"type": "token", "token": "success_token"},
          )
        ]
      ),
      risk_signals={},
    )
    return payload.model_dump(mode="json", exclude_none=True)

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
      self.assertEqual(self.get_resource_id(checkout.id), "test_checkout_1")
      self.assertEqual(checkout.status, "ready_for_complete")

      # 2. Complete Checkout
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        "/checkout-sessions/test_checkout_1/complete",
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

      # 2. Complete Checkout (First time)
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        "/checkout-sessions/test_checkout_double/complete",
        headers=self._get_headers(idempotency_key="2", request_id="2"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200)

      # 3. Complete Checkout (Second time) - Should fail
      response = self.client.post(
        "/checkout-sessions/test_checkout_double/complete",
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

      # 2. Complete Multi-item Checkout
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        "/checkout-sessions/test_checkout_multi/complete",
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

      # 2. Cancel Checkout
      response = self.client.post(
        "/checkout-sessions/test_checkout_cancel/cancel",
        headers=self._get_headers(
          idempotency_key="cancel_2", request_id="cancel_2"
        ),
      )
      self.assertEqual(response.status_code, 200)
      checkout = TestCheckout.model_validate(response.json())
      self.assertEqual(checkout.status, "canceled")

      # 3. Try to Cancel again (should fail)
      response = self.client.post(
        "/checkout-sessions/test_checkout_cancel/cancel",
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

      # Complete it
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        "/checkout-sessions/test_checkout_cancel_completed/complete",
        headers=self._get_headers(
          idempotency_key="cancel_5", request_id="cancel_5"
        ),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200)

      # Try to cancel completed checkout
      response = self.client.post(
        "/checkout-sessions/test_checkout_cancel_completed/cancel",
        headers=self._get_headers(
          idempotency_key="cancel_6", request_id="cancel_6"
        ),
      )
      self.assertEqual(response.status_code, 409)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(len(data["messages"]), 1)
      self.assertIn("Cannot cancel checkout", data["messages"][0]["content"])

  def _notify_and_capture(
    self, checkout: UnifiedCheckout, event_type: str
  ) -> list[dict]:
    """Fire _notify_webhook with httpx stubbed and return captured POSTs."""
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
          route = respx.post().respond(200)
          await service._notify_webhook(checkout, event_type)
          if route.called:
            for call in route.calls:
              request = call.request
              body = json.loads(request.content) if request.content else None
              captured.append(
                {
                  "url": str(request.url),
                  "json": body,
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

      payment_payload = self._create_payment_payload()
      response = self.client.post(
        "/checkout-sessions/wh_order_placed/complete",
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
      # Server version is 2026-04-08, so 2026-04-09 should be unsupported
      headers["UCP-Agent"] = (
        'profile="https://agent.example/profile"; version="2026-04-09"'
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
              f"Version 2026-04-09 is not supported. This merchant"
              f" implements version {app.version}."
            ),
            severity=ErrorSeverity.UNRECOVERABLE,
          )
        ],
      )
      self.assertEqual(UcpErrorResponse.model_validate(data), expected)


if __name__ == "__main__":
  absltest.main()
