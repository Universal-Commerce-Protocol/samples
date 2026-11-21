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

"""Regression test: a create keeps UCP's own signal keys as sent.

Baseline: checkout and cart creates copy the request's `signals` with
`model_dump()` and no `by_alias=True`, so `dev.ucp.buyer_ip` becomes the
Python field name `dev_ucp_buyer_ip`. The response model's key pattern
refuses that name, and the create answers 500 for any platform that sends
the signals UCP defines for authorization and abuse prevention.
"""

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
import shutil
import tempfile
import uuid

from absl import flags
from absl.testing import absltest
import db
import dependencies
from fastapi.testclient import TestClient
from server.server import app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

SIGNALS = {
  "dev.ucp.buyer_ip": "203.0.113.7",
  "dev.ucp.user_agent": "Mozilla/5.0",
  "com.example.device_id": "device-123",
}


def _headers() -> dict[str, str]:
  return {
    "UCP-Agent": 'profile="https://agent.example/profile"',
    "request-id": str(uuid.uuid4()),
    "idempotency-key": str(uuid.uuid4()),
  }


class SignalsAliasTest(absltest.TestCase):
  """Checkout and cart creates answer the signals a platform sends."""

  def setUp(self) -> None:
    """Set up temp DBs, dependency overrides and seed data."""
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
    self.client = TestClient(app, raise_server_exceptions=False)

  def tearDown(self) -> None:
    """Clear overrides, dispose engines, and remove temp DBs."""
    app.dependency_overrides.clear()

    async def dispose() -> None:
      await self.products_engine.dispose()
      await self.transactions_engine.dispose()

    asyncio.run(dispose())
    shutil.rmtree(self.test_dir)
    super().tearDown()

  def test_checkout_create_keeps_ucp_signal_keys(self) -> None:
    """A checkout create answers 201 with each signal key as sent."""
    r = self.client.post(
      "/checkout-sessions",
      headers=_headers(),
      json={
        "line_items": [{"item": {"id": "gizmo"}, "quantity": 1}],
        "signals": SIGNALS,
      },
    )
    self.assertEqual(r.status_code, 201, r.text)
    self.assertEqual(r.json()["signals"], SIGNALS)

  def test_cart_create_keeps_ucp_signal_keys(self) -> None:
    """A cart create answers 201 with each signal key as sent."""
    r = self.client.post(
      "/carts",
      headers=_headers(),
      json={
        "line_items": [{"item": {"id": "gizmo"}, "quantity": 1}],
        "signals": SIGNALS,
      },
    )
    self.assertEqual(r.status_code, 201, r.text)
    self.assertEqual(r.json()["signals"], SIGNALS)


if __name__ == "__main__":
  absltest.main()
