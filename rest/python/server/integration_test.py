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
from pathlib import Path
import shutil
import tempfile
from collections.abc import AsyncGenerator
import uuid

from absl import flags
from absl.testing import absltest
import db
import dependencies
from fastapi.testclient import TestClient
from server import app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete
from ucp_sdk.models.schemas.shopping import checkout_create_req
from ucp_sdk.models.schemas.shopping import payment_create_req
from ucp_sdk.models.schemas.shopping.ap2_mandate import (
  CheckoutResponseWithAp2 as Ap2Checkout,
)
from ucp_sdk.models.schemas.shopping.buyer_consent_resp import (
  Checkout as BuyerConsentCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.discount_resp import (
  Checkout as DiscountCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.fulfillment_create_req import Fulfillment
from ucp_sdk.models.schemas.shopping.fulfillment_resp import (
  Checkout as FulfillmentCheckout,
)
from ucp_sdk.models.schemas.shopping.order import PlatformConfig
from ucp_sdk.models.schemas.shopping.payment_data import PaymentData
from ucp_sdk.models.schemas.shopping.types import card_payment_instrument
from ucp_sdk.models.schemas.shopping.types import fulfillment_destination_req
from ucp_sdk.models.schemas.shopping.types import fulfillment_group_create_req
from ucp_sdk.models.schemas.shopping.types import fulfillment_method_create_req
from ucp_sdk.models.schemas.shopping.types import fulfillment_req
from ucp_sdk.models.schemas.shopping.types import item_create_req
from ucp_sdk.models.schemas.shopping.types import line_item_create_req
from ucp_sdk.models.schemas.shopping.types import payment_handler_create_req
from ucp_sdk.models.schemas.shopping.types import payment_instrument
from ucp_sdk.models.schemas.shopping.types import shipping_destination_req
from ucp_sdk.models.schemas.shopping.types import token_credential_resp

FLAGS = flags.FLAGS


class TestCheckout(
  BuyerConsentCheckoutResp,
  FulfillmentCheckout,
  DiscountCheckoutResp,
  Ap2Checkout,
):
  """Checkout model supporting Fulfillment, Discount, and AP2 extensions."""

  platform: PlatformConfig | None = None


class IntegrationTest(absltest.TestCase):
  """Integration tests for the UCP server application."""

  def setUp(self) -> None:
    """Set up the test environment, including temporary DBs and dependencies."""
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
    for item_id, item_title, item_price, quantity in items:
      item = item_create_req.ItemCreateRequest(
        id=item_id, title=item_title, price=item_price
      )
      line_item = line_item_create_req.LineItemCreateRequest(
        quantity=quantity, item=item
      )
      line_items.append(line_item)

    handler = payment_handler_create_req.PaymentHandlerCreateRequest(
      id="google_pay",
      name="google.pay",
      version="2026-01-11",
      spec="https://example.com/spec",
      config_schema="https://example.com/schema",
      instrument_schemas=["https://example.com/schema"],
      config={},
    )

    payment = payment_create_req.PaymentCreateRequest(
      handlers=[handler], instruments=[]
    )

    # Hierarchical Fulfillment Construction
    destination = fulfillment_destination_req.FulfillmentDestinationRequest(
      root=shipping_destination_req.ShippingDestinationRequest(
        id="dest_1", address_country="US"
      )
    )
    group = fulfillment_group_create_req.FulfillmentGroupCreateRequest(
      selected_option_id="std-ship"
    )
    method = fulfillment_method_create_req.FulfillmentMethodCreateRequest(
      type="shipping",
      destinations=[destination],
      selected_destination_id="dest_1",
      groups=[group],
    )
    fulfillment = Fulfillment(
      root=fulfillment_req.FulfillmentRequest(methods=[method])
    )

    return checkout_create_req.CheckoutCreateRequest(
      id=checkout_id,
      currency="USD",
      line_items=line_items,
      payment=payment,
      fulfillment=fulfillment,
    )

  def _create_payment_payload(self) -> PaymentData:
    """Create a payment payload using SDK models."""
    credential = token_credential_resp.TokenCredentialResponse(
      type="token", token="success_token"
    )
    instrument = card_payment_instrument.CardPaymentInstrument(
      id="instr_1",
      handler_id="mock_payment_handler",
      handler_name="mock_payment_handler",
      type="card",
      brand="Visa",
      last_digits="1234",
      credential=credential,
    )
    return PaymentData(
      payment_data=payment_instrument.PaymentInstrument(root=instrument),
      risk_signals={},
    )

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
        json=payment_payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 200)
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
      self.assertIn("Insufficient stock", response.json()["detail"])

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
        json=payment_payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 200)

      # 3. Complete Checkout (Second time) - Should fail
      response = self.client.post(
        "/checkout-sessions/test_checkout_double/complete",
        headers=self._get_headers(idempotency_key="4", request_id="4"),
        json=payment_payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 409)
      self.assertEqual(
        response.json()["detail"],
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
        json=payment_payload.model_dump(mode="json", exclude_none=True),
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
      self.assertIn("Cannot cancel checkout", response.json()["detail"])

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
        json=payment_payload.model_dump(mode="json", exclude_none=True),
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
      self.assertIn("Cannot cancel checkout", response.json()["detail"])


if __name__ == "__main__":
  absltest.main()
