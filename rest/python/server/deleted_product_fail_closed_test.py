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

"""Regression test: completion fails loudly for a deleted product.

Baseline: `complete_checkout`'s "Atomic Inventory Reservation" block
skips the reservation body when `db.get_product` returns None (product
deleted after checkout creation), then still creates the order — the
completion succeeds at HTTP 200 with a dangling product reference and
stale stored prices while inventory is untouched. The fix fails the
completion loudly with a 4xx instead. No pricing behavior is changed.

Two tests: the minimal single-line case, and a two-line case proving the
earlier reservation is rolled back (inventory restored), the checkout
stays uncompleted, no order is created, and no successful idempotency
record survives the failed attempt.
"""

import asyncio
from collections.abc import AsyncGenerator
import shutil
import tempfile
from pathlib import Path
import uuid

from absl import flags
from absl.testing import absltest
import db
import dependencies
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import delete
from server import app

FLAGS = flags.FLAGS


def _headers(**overrides: str) -> dict[str, str]:
  headers = {
    "UCP-Agent": 'profile="https://agent.example/profile"',
    "request-id": str(uuid.uuid4()),
    "idempotency-key": str(uuid.uuid4()),
  }
  headers.update(overrides)
  return headers


def _fulfillment(line_item_ids: list[str]) -> dict:
  return {
    "methods": [
      {
        "id": "method_1",
        "line_item_ids": line_item_ids,
        "type": "shipping",
        "destinations": [{"id": "dest_1", "address_country": "US"}],
        "selected_destination_id": "dest_1",
        "groups": [
          {
            "id": "group_1",
            "line_item_ids": line_item_ids,
            "selected_option_id": "std-ship",
          }
        ],
      }
    ]
  }


def _payment() -> dict:
  return {
    "payment": {
      "instruments": [
        {
          "id": "instr_1",
          "handler_id": "mock_payment_handler",
          "type": "card",
          "display": {"brand": "Visa", "last_digits": "1234"},
          "credential": {"type": "token", "token": "success_token"},
        }
      ]
    },
    "risk_signals": {},
  }


class DeletedProductFailClosedTest(absltest.TestCase):
  """Completion must fail loudly when a line item's product is gone."""

  def setUp(self) -> None:
    """Set up temp DBs, dependency overrides, and seed data."""
    flags.FLAGS(["test"])
    super().setUp()
    self.test_dir = Path(tempfile.mkdtemp())
    prod_url = f"sqlite+aiosqlite:///{self.test_dir / 'products.db'}"
    trans_url = f"sqlite+aiosqlite:///{self.test_dir / 'transactions.db'}"
    self.products_engine = create_async_engine(prod_url, echo=False)
    self.transactions_engine = create_async_engine(trans_url, echo=False)
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
    self._seed()

  def tearDown(self) -> None:
    """Clear overrides, dispose engines, and remove temp DBs."""
    app.dependency_overrides.clear()

    async def dispose() -> None:
      await self.products_engine.dispose()
      await self.transactions_engine.dispose()

    asyncio.run(dispose())
    shutil.rmtree(self.test_dir)
    super().tearDown()

  def _seed(self) -> None:
    async def seed() -> None:
      async with self.products_factory() as session:
        await session.execute(delete(db.Product))
        session.add(db.Product(id="gizmo", title="Gizmo Pro", price=5000))
        session.add(db.Product(id="widget", title="Widget Mini", price=3000))
        await session.commit()
      async with self.transactions_factory() as session:
        await session.execute(delete(db.Inventory))
        session.add(db.Inventory(product_id="gizmo", quantity=5))
        session.add(db.Inventory(product_id="widget", quantity=5))
        await session.commit()

    asyncio.run(seed())

  def _delete_product(self, product_id: str) -> None:
    async def delete_product() -> None:
      async with self.products_factory() as session:
        product = await session.get(db.Product, product_id)
        await session.delete(product)
        await session.commit()

    asyncio.run(delete_product())

  def _order_ids(self) -> list[str]:
    async def fetch() -> list[str]:
      async with self.transactions_factory() as session:
        result = await session.execute(select(db.Order.id))
        return [row[0] for row in result.all()]

    return asyncio.run(fetch())

  def _inventory(self, product_id: str) -> int:
    async def fetch() -> int:
      async with self.transactions_factory() as session:
        result = await session.execute(
          select(db.Inventory.quantity).where(
            db.Inventory.product_id == product_id
          )
        )
        return result.one()[0]

    return asyncio.run(fetch())

  def _checkout_status(self, sid: str) -> str:
    r = self.client.get(f"/checkout-sessions/{sid}", headers=_headers())
    self.assertEqual(r.status_code, 200, r.text)
    return r.json()["status"]

  def test_complete_fails_loudly_when_product_deleted(self) -> None:
    """A deleted product must fail completion at 4xx, not complete."""
    with self.client:
      r = self.client.post(
        "/checkout-sessions",
        headers=_headers(),
        json={
          "line_items": [{"item": {"id": "gizmo"}, "quantity": 1}],
          "buyer": {"first_name": "A", "email": "a@example.com"},
        },
      )
      self.assertEqual(r.status_code, 201, r.text)
      body = r.json()
      sid = body["id"].split("/")[-1]
      li_id = body["line_items"][0]["id"]
      # Attach fulfillment so completion is allowed.
      r = self.client.put(
        f"/checkout-sessions/{sid}",
        headers=_headers(),
        json={
          "line_items": [{"id": li_id, "item": {"id": "gizmo"}, "quantity": 1}],
          "fulfillment": _fulfillment([li_id]),
        },
      )
      self.assertEqual(r.status_code, 200, r.text)

      # Seller deletes the product after checkout creation.
      self._delete_product("gizmo")

      r = self.client.post(
        f"/checkout-sessions/{sid}/complete",
        headers=_headers(),
        json=_payment(),
      )
      self.assertEqual(r.status_code, 400, r.text)
      self.assertIn("not found", r.text.lower())
      # No order may be created for a product that no longer exists.
      self.assertEmpty(self._order_ids())

  def test_complete_rolls_back_earlier_reservation_when_later_product_deleted(
    self,
  ) -> None:
    """Two lines: an earlier reservation must roll back on a later 4xx.

    Line 1 (widget) exists and is reserved first; line 2 (gizmo) is
    deleted before completion. The completion must fail loudly at 400,
    the widget reservation must be rolled back (inventory restored), the
    checkout must remain uncompleted, no order may be created, and the
    failed attempt must not leave a replayable success idempotency
    record.
    """
    with self.client:
      r = self.client.post(
        "/checkout-sessions",
        headers=_headers(),
        json={
          "line_items": [
            {"item": {"id": "widget"}, "quantity": 1},
            {"item": {"id": "gizmo"}, "quantity": 1},
          ],
          "buyer": {"first_name": "A", "email": "a@example.com"},
        },
      )
      self.assertEqual(r.status_code, 201, r.text)
      body = r.json()
      sid = body["id"].split("/")[-1]
      li_ids = {li["item"]["id"]: li["id"] for li in body["line_items"]}
      r = self.client.put(
        f"/checkout-sessions/{sid}",
        headers=_headers(),
        json={
          "line_items": [
            {
              "id": li_ids["widget"],
              "item": {"id": "widget"},
              "quantity": 1,
            },
            {"id": li_ids["gizmo"], "item": {"id": "gizmo"}, "quantity": 1},
          ],
          "fulfillment": _fulfillment([li_ids["widget"], li_ids["gizmo"]]),
        },
      )
      self.assertEqual(r.status_code, 200, r.text)

      # Capture the pre-completion state: checkout is ready, not completed.
      status_before = self._checkout_status(sid)
      self.assertNotEqual(status_before, "completed")
      inventory_before = self._inventory("widget")
      self.assertEqual(inventory_before, 5)

      # Seller deletes the second product after checkout creation.
      self._delete_product("gizmo")

      complete_key = str(uuid.uuid4())
      r = self.client.post(
        f"/checkout-sessions/{sid}/complete",
        headers=_headers(**{"idempotency-key": complete_key}),
        json=_payment(),
      )
      self.assertEqual(r.status_code, 400, r.text)
      self.assertIn("not found", r.text.lower())

      # The earlier widget reservation must have been rolled back.
      self.assertEqual(self._inventory("widget"), inventory_before)
      # The checkout must remain uncompleted, with no order attached.
      self.assertEqual(self._checkout_status(sid), status_before)
      # No order may be created.
      self.assertEmpty(self._order_ids())
      # No successful idempotency record: retrying with the same key
      # re-executes and fails again instead of replaying a success.
      r = self.client.post(
        f"/checkout-sessions/{sid}/complete",
        headers=_headers(**{"idempotency-key": complete_key}),
        json=_payment(),
      )
      self.assertEqual(r.status_code, 400, r.text)
      self.assertIn("not found", r.text.lower())
      self.assertEmpty(self._order_ids())


if __name__ == "__main__":
  absltest.main()
