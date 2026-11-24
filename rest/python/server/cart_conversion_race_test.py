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

"""Concurrent cart conversion: one cart, several idempotency keys.

The Cart specification says a cart with an incomplete checkout converts to
that checkout and that a cart has ONE active checkout. Both promises are only
real when the conversions ARRIVE AT ONCE, which a sequential test cannot
reach: every conversion reads the cart's existing checkouts, finds none,
builds its response and inserts, so independent keys all finish the read
before any of them writes.

The two obligations under test:

  · concurrency     every conversion of one cart answers 2xx and they all
                    name ONE checkout; the store holds one active checkout.
  · key binding     converting again with a new key binds that key to the
                    returned checkout, so reusing it with a different cart is
                    409 idempotency_conflict, not a second conversion.

Concurrency is driven through httpx's ASGI transport with asyncio.gather
rather than TestClient, which serialises requests and so cannot produce the
interleaving at all.
"""

import asyncio
from collections.abc import AsyncGenerator
import copy
from pathlib import Path
import shutil
import tempfile
import uuid

from absl import flags
from absl.testing import absltest
import db
import dependencies
import httpx
from server.server import app
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

RACERS = 4

# A cart body in the shape integration_test builds from the SDK models.
CART_BODY = {
  "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
}

# A cart conversion only needs the cart; the server takes currency, line
# items and buyer from the cart itself.
CONVERT_BODY = {"currency": "USD"}

ACTIVE_STATUSES = ("incomplete", "requires_escalation", "ready_for_complete")


class CartConversionRaceTest(absltest.TestCase):
  """Concurrent conversions of one cart under different Idempotency-Keys."""

  def setUp(self) -> None:
    """Only the temporary directory and the dependency overrides.

    The engines are built INSIDE the event loop that runs the race, not
    here. aiosqlite keeps a worker thread bound to the loop that opened
    each connection, so an engine created under one `asyncio.run` and used
    under the next hands back a pooled connection whose loop is gone; that
    surfaces as "attempt to write a readonly database" and looks exactly
    like the defect under test. NullPool below removes the reuse entirely.
    """
    flags.FLAGS(["test"])
    super().setUp()
    self.test_dir = Path(tempfile.mkdtemp())

    async def override_get_products_db() -> AsyncGenerator[AsyncSession, None]:
      async with self.products_session_factory() as session:
        yield session

    async def override_get_transactions_db() -> AsyncGenerator[
      AsyncSession, None
    ]:
      async with self.transactions_session_factory() as session:
        yield session

    app.dependency_overrides[dependencies.get_products_db] = (
      override_get_products_db
    )
    app.dependency_overrides[dependencies.get_transactions_db] = (
      override_get_transactions_db
    )

  def tearDown(self) -> None:
    """Drop the overrides and the temporary databases."""
    app.dependency_overrides.clear()
    shutil.rmtree(self.test_dir, ignore_errors=True)
    super().tearDown()

  async def _prepare(self) -> None:
    """Engines, schemas, and one product with stock well above RACERS."""
    self.products_engine = create_async_engine(
      f"sqlite+aiosqlite:///{self.test_dir / 'products.db'}",
      echo=False,
      poolclass=NullPool,
    )
    self.products_session_factory = sessionmaker(
      self.products_engine, expire_on_commit=False, class_=AsyncSession
    )
    self.transactions_engine = create_async_engine(
      f"sqlite+aiosqlite:///{self.test_dir / 'transactions.db'}",
      echo=False,
      poolclass=NullPool,
    )
    self.transactions_session_factory = sessionmaker(
      self.transactions_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with self.products_engine.begin() as conn:
      await conn.run_sync(db.ProductBase.metadata.create_all)
    async with self.transactions_engine.begin() as conn:
      await conn.run_sync(db.TransactionBase.metadata.create_all)
    async with self.products_session_factory() as session:
      await session.execute(delete(db.Product))
      session.add(
        db.Product(
          id="rose",
          title="Red Rose",
          price=1000,
          image_url="http://rose.com",
        )
      )
      await session.commit()
    async with self.transactions_session_factory() as session:
      await session.execute(delete(db.Inventory))
      session.add(db.Inventory(product_id="rose", quantity=100))
      await session.commit()

  async def _dispose(self) -> None:
    await self.products_engine.dispose()
    await self.transactions_engine.dispose()

  @staticmethod
  def _headers(key: str) -> dict[str, str]:
    return {
      "UCP-Agent": 'profile="https://agent.example/profile"',
      "request-signature": "test",
      "idempotency-key": key,
      "request-id": str(uuid.uuid4()),
    }

  async def _create_cart(self, client: httpx.AsyncClient, key: str) -> str:
    response = await client.post(
      "/carts", headers=self._headers(key), json=copy.deepcopy(CART_BODY)
    )
    self.assertEqual(response.status_code, 201, response.text)
    return response.json()["id"]

  async def _active_checkouts(self, cart_id: str) -> list[dict]:
    async with self.transactions_session_factory() as session:
      rows = await db.get_checkouts_by_cart_id(session, cart_id)
    return [row for row in rows if row.get("status") in ACTIVE_STATUSES]

  def _run(self, scenario):
    """Prepare, run and dispose inside ONE loop (see setUp for why)."""

    async def run():
      await self._prepare()
      try:
        return await scenario()
      finally:
        await self._dispose()

    return asyncio.run(run())

  @staticmethod
  def _summary(responses: list[httpx.Response]) -> str:
    counts: dict[int, int] = {}
    for response in responses:
      counts[response.status_code] = counts.get(response.status_code, 0) + 1
    return ", ".join(f"{n}x{code}" for code, n in sorted(counts.items()))

  def test_concurrent_keys_leave_one_active_checkout(self) -> None:
    """Two conversions that arrive together must not create two checkouts."""

    async def scenario():
      transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
      async with httpx.AsyncClient(
        transport=transport, base_url="http://samples.test"
      ) as client:
        cart_id = await self._create_cart(client, "cart-create")
        body = dict(copy.deepcopy(CONVERT_BODY), cart_id=cart_id)
        responses = await asyncio.gather(
          *(
            client.post(
              "/checkout-sessions",
              headers=self._headers(f"convert-{uuid.uuid4()}"),
              json=body,
            )
            for _ in range(RACERS)
          )
        )
        return cart_id, responses, await self._active_checkouts(cart_id)

    cart_id, responses, active = self._run(scenario)

    server_errors = [r for r in responses if r.status_code >= 500]
    self.assertEqual(
      server_errors,
      [],
      "a concurrent conversion is not a server fault; got "
      f"{self._summary(responses)}",
    )
    ids = {r.json().get("id") for r in responses if r.status_code < 300}
    self.assertLen(
      ids,
      1,
      "every conversion must name ONE checkout; got "
      f"{self._summary(responses)} -> {ids}",
    )
    self.assertLen(
      active,
      1,
      f"cart {cart_id} must hold one active checkout; got {len(active)}",
    )

  def test_spent_key_conflicts_on_another_cart(self) -> None:
    """A key spent on one cart may not convert a second cart."""

    async def scenario():
      transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
      async with httpx.AsyncClient(
        transport=transport, base_url="http://samples.test"
      ) as client:
        cart_a = await self._create_cart(client, "cart-a")
        cart_b = await self._create_cart(client, "cart-b")
        key_a = f"convert-a-{uuid.uuid4()}"
        key_b = f"convert-b-{uuid.uuid4()}"
        first = await client.post(
          "/checkout-sessions",
          headers=self._headers(key_a),
          json=dict(CONVERT_BODY, cart_id=cart_a),
        )
        # Same cart, new key: the server returns the existing checkout and
        # must remember key B against it.
        second = await client.post(
          "/checkout-sessions",
          headers=self._headers(key_b),
          json=dict(CONVERT_BODY, cart_id=cart_a),
        )
        # Reusing key B with a different cart must be a conflict.
        third = await client.post(
          "/checkout-sessions",
          headers=self._headers(key_b),
          json=dict(CONVERT_BODY, cart_id=cart_b),
        )
        return first, second, third

    first, second, third = self._run(scenario)

    self.assertEqual(first.status_code, 201, first.text)
    self.assertLess(second.status_code, 300, second.text)
    self.assertEqual(
      second.json()["id"],
      first.json()["id"],
      "a new key on a converted cart must return the existing checkout",
    )
    self.assertEqual(
      third.status_code,
      409,
      "reusing a spent key with a different cart must be a conflict; got "
      f"{third.status_code}",
    )


if __name__ == "__main__":
  absltest.main()
