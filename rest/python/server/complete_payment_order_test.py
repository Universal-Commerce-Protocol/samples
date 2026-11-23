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

"""Regression test: completion processes payment only after its checks pass.

Baseline: `complete_checkout` calls `_process_payment` before it checks the
fulfillment selection and reserves stock. When either check fails, the
request ends in a 4xx without an idempotency record, so a retry with the same
Idempotency-Key processes the payment again. The mock handler charges
nothing, but a real handler would charge for a checkout that never completes.
"""

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
import shutil
import tempfile
from unittest import mock
import uuid

from absl import flags
from absl.testing import absltest
import db
import dependencies
from fastapi.testclient import TestClient
from server.server import app
from services.checkout_service import CheckoutService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker


def _headers(idempotency_key: str | None = None) -> dict[str, str]:
  return {
    "UCP-Agent": 'profile="https://agent.example/profile"',
    "request-id": str(uuid.uuid4()),
    "idempotency-key": idempotency_key or str(uuid.uuid4()),
  }


def _fulfillment(line_item_id: str) -> dict:
  return {
    "methods": [
      {
        "id": "method_1",
        "line_item_ids": [line_item_id],
        "type": "shipping",
        "destinations": [{"id": "dest_1", "address_country": "US"}],
        "selected_destination_id": "dest_1",
        "groups": [
          {
            "id": "group_1",
            "line_item_ids": [line_item_id],
            "selected_option_id": "std-ship",
          }
        ],
      }
    ]
  }


def _payment(token: str = "success_token") -> dict:
  return {
    "payment": {
      "instruments": [
        {
          "id": "instr_1",
          "handler_id": "mock_payment_handler",
          "type": "card",
          "display": {"brand": "Visa", "last_digits": "1234"},
          "credential": {"type": "token", "token": token},
        }
      ]
    },
    "risk_signals": {},
  }


class CompletePaymentOrderTest(absltest.TestCase):
  """A completion that fails its checks must not process the payment."""

  def setUp(self) -> None:
    """Set up temp DBs, dependency overrides, seed data and a payment spy."""
    flags.FLAGS(["test"])
    super().setUp()
    self.test_dir = Path(tempfile.mkdtemp())
    self.products_engine = create_async_engine(
      f"sqlite+aiosqlite:///{self.test_dir / 'products.db'}"
    )
    self.transactions_engine = create_async_engine(
      f"sqlite+aiosqlite:///{self.test_dir / 'transactions.db'}"
    )
    self.products_factory = sessionmaker(
      self.products_engine, expire_on_commit=False, class_=AsyncSession
    )
    self.transactions_factory = sessionmaker(
      self.transactions_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def init() -> None:
      async with self.products_engine.begin() as conn:
        await conn.run_sync(db.ProductBase.metadata.create_all)
      async with self.transactions_engine.begin() as conn:
        await conn.run_sync(db.TransactionBase.metadata.create_all)
      async with self.products_factory() as session:
        session.add(db.Product(id="gizmo", title="Gizmo Pro", price=5000))
        await session.commit()
      async with self.transactions_factory() as session:
        session.add(db.Inventory(product_id="gizmo", quantity=5))
        await session.commit()

    asyncio.run(init())

    async def override_products() -> AsyncGenerator[AsyncSession, None]:
      async with self.products_factory() as session:
        yield session

    async def override_transactions() -> AsyncGenerator[AsyncSession, None]:
      async with self.transactions_factory() as session:
        yield session

    app.dependency_overrides[dependencies.get_products_db] = override_products
    app.dependency_overrides[dependencies.get_transactions_db] = (
      override_transactions
    )
    self.client = TestClient(app)
    self.payments = mock.patch.object(
      CheckoutService,
      "_process_payment",
      autospec=True,
      side_effect=CheckoutService._process_payment,
    ).start()
    self.addCleanup(mock.patch.stopall)

  def tearDown(self) -> None:
    """Clear overrides, dispose engines, and remove temp DBs."""
    app.dependency_overrides.clear()

    async def dispose() -> None:
      await self.products_engine.dispose()
      await self.transactions_engine.dispose()

    asyncio.run(dispose())
    shutil.rmtree(self.test_dir)
    super().tearDown()

  def _set_inventory(self, quantity: int) -> None:
    async def update() -> None:
      async with self.transactions_factory() as session:
        row = await session.get(db.Inventory, "gizmo")
        row.quantity = quantity
        await session.commit()

    asyncio.run(update())

  def _inventory(self) -> int:
    async def fetch() -> int:
      async with self.transactions_factory() as session:
        result = await session.execute(
          select(db.Inventory.quantity).where(
            db.Inventory.product_id == "gizmo"
          )
        )
        return result.one()[0]

    return asyncio.run(fetch())

  def _create_checkout(self, with_fulfillment: bool) -> str:
    r = self.client.post(
      "/checkout-sessions",
      headers=_headers(),
      json={
        "line_items": [{"item": {"id": "gizmo"}, "quantity": 1}],
        "buyer": {"first_name": "A", "email": "a@example.com"},
      },
    )
    self.assertEqual(r.status_code, 201, r.text)
    sid = r.json()["id"].split("/")[-1]
    if with_fulfillment:
      li_id = r.json()["line_items"][0]["id"]
      r = self.client.put(
        f"/checkout-sessions/{sid}",
        headers=_headers(),
        json={
          "line_items": [{"id": li_id, "item": {"id": "gizmo"}, "quantity": 1}],
          "fulfillment": _fulfillment(li_id),
        },
      )
      self.assertEqual(r.status_code, 200, r.text)
    return sid

  def _complete(self, sid: str, key: str, token: str = "success_token"):
    return self.client.post(
      f"/checkout-sessions/{sid}/complete",
      headers=_headers(key),
      json=_payment(token),
    )

  def test_missing_fulfillment_does_not_process_payment_even_on_retry(
    self,
  ) -> None:
    """A 400 for missing fulfillment, and its retry, take no payment."""
    with self.client:
      sid = self._create_checkout(with_fulfillment=False)
      key = str(uuid.uuid4())
      for _ in range(2):  # the original request, then a retry with its key
        r = self._complete(sid, key)
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("Fulfillment", r.text)
      self.assertEqual(self.payments.call_count, 0)

  def test_out_of_stock_does_not_process_payment(self) -> None:
    """A 409 for an out-of-stock line takes no payment."""
    with self.client:
      sid = self._create_checkout(with_fulfillment=True)
      self._set_inventory(0)
      r = self._complete(sid, str(uuid.uuid4()))
      self.assertEqual(r.status_code, 409, r.text)
      self.assertEqual(self.payments.call_count, 0)

  def test_declined_payment_releases_the_reservation(self) -> None:
    """A declined payment leaves stock and the checkout as they were."""
    with self.client:
      sid = self._create_checkout(with_fulfillment=True)
      r = self._complete(sid, str(uuid.uuid4()), token="fail_token")
      self.assertEqual(r.status_code, 402, r.text)
      self.assertEqual(self._inventory(), 5)
      r = self.client.get(f"/checkout-sessions/{sid}", headers=_headers())
      self.assertNotEqual(r.json()["status"], "completed")

  def test_successful_completion_processes_payment_once(self) -> None:
    """The happy path still takes the payment once and reserves stock."""
    with self.client:
      sid = self._create_checkout(with_fulfillment=True)
      r = self._complete(sid, str(uuid.uuid4()))
      self.assertEqual(r.status_code, 200, r.text)
      self.assertEqual(r.json()["status"], "completed")
      self.assertEqual(self.payments.call_count, 1)
      self.assertEqual(self._inventory(), 4)


if __name__ == "__main__":
  absltest.main()
