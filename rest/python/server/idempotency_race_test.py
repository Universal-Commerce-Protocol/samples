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

"""Concurrent idempotency: one key raced against itself.

Idempotency is only a promise if it holds when the retries ARRIVE AT ONCE,
which is the case a sequential test cannot reach. Every idempotent write here
reads the record, finds none, builds its response and inserts, so requests
sharing one Idempotency-Key all finish that read before any of them writes.
Because `idempotency_records.key` is a primary key, the losers collide at
commit.

The two obligations under test, both from the idempotency contract:

  · identical bytes   every response is 2xx and they all name ONE checkout,
                      because a retry of the same request is the same request.
  · different bytes   exactly one 2xx and every other response is 409
                      idempotency_conflict, because reusing a key with new
                      parameters is a client error, not a server fault.

Concurrency is driven through httpx's ASGI transport with asyncio.gather
rather than TestClient, which serialises requests and so cannot produce the
interleaving at all. That is why the existing integration tests pass while
this one does not.
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

RACERS = 8

# A create-checkout body in the shape integration_test builds from the SDK
# models. `id` is ucp_request: omit, so the server assigns the real one.
CHECKOUT_BODY = {
  "id": "race_checkout",
  "currency": "USD",
  "line_items": [{"item": {"id": "rose"}, "quantity": 1}],
  "payment": {"instruments": []},
  "fulfillment": {
    "methods": [
      {
        "id": "method_1",
        "type": "shipping",
        "line_item_ids": ["rose"],
        "selected_destination_id": "dest_1",
        "destinations": [
          {
            "id": "dest_1",
            "type": "shipping_address",
            "address_country": "US",
          }
        ],
        "groups": [
          {
            "id": "group_1",
            "line_item_ids": ["rose"],
            "selected_option_id": "std-ship",
          }
        ],
      }
    ]
  },
}


class IdempotencyRaceTest(absltest.TestCase):
  """Eight concurrent creates under one Idempotency-Key."""

  def setUp(self) -> None:
    """Only the temporary directory and the dependency overrides.

    The engines are built INSIDE the event loop that runs the race, not
    here. aiosqlite keeps a worker thread bound to the loop that opened
    each connection, so an engine created under one `asyncio.run` and used
    under the next hands back a pooled connection whose loop is gone; that
    surfaces as "attempt to write a readonly database" on the idempotency
    insert and looks exactly like the defect under test. NullPool below
    removes the reuse entirely.
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

  async def _race(self, bodies: list[dict]) -> list[httpx.Response]:
    """One POST per body, all at once, under a single Idempotency-Key."""
    key = f"race-{uuid.uuid4()}"
    # raise_app_exceptions=False so an unhandled server exception becomes
    # the 500 a real client sees instead of being re-raised into the test.
    # These two tests are about the STATUS a racing caller is given, and a
    # propagated traceback would hide it behind an error of our own.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
      transport=transport, base_url="http://samples.test"
    ) as client:
      return await asyncio.gather(
        *(
          client.post(
            "/checkout-sessions", headers=self._headers(key), json=body
          )
          for body in bodies
        )
      )

  def _run_race(self, bodies: list[dict]) -> list[httpx.Response]:
    """Prepare, race and dispose inside ONE loop (see setUp for why)."""

    async def scenario() -> list[httpx.Response]:
      await self._prepare()
      try:
        return await self._race(bodies)
      finally:
        await self._dispose()

    return asyncio.run(scenario())

  @staticmethod
  def _summary(responses: list[httpx.Response]) -> str:
    counts: dict[int, int] = {}
    for r in responses:
      counts[r.status_code] = counts.get(r.status_code, 0) + 1
    return ", ".join(f"{n}x{code}" for code, n in sorted(counts.items()))

  def test_identical_bodies_all_succeed_and_name_one_checkout(self) -> None:
    """A retry of the same request is the same request, even at once."""
    bodies = [copy.deepcopy(CHECKOUT_BODY) for _ in range(RACERS)]
    responses = self._run_race(bodies)

    server_errors = [r for r in responses if r.status_code >= 500]
    self.assertEqual(
      server_errors,
      [],
      "losing a primary-key race is not a server fault; got "
      f"{self._summary(responses)}",
    )
    for r in responses:
      self.assertLess(
        r.status_code,
        300,
        f"every identical retry must be 2xx; got {r.status_code}",
      )
    ids = {r.json().get("id") for r in responses}
    self.assertLen(
      ids, 1, f"identical retries must name ONE checkout; got {ids}"
    )

  def test_different_bodies_conflict_rather_than_crash(self) -> None:
    """Reusing a key with new parameters is a 409, never a 500."""
    bodies = []
    for i in range(RACERS):
      body = copy.deepcopy(CHECKOUT_BODY)
      body["line_items"][0]["quantity"] = i + 1  # each request differs
      bodies.append(body)
    responses = self._run_race(bodies)

    server_errors = [r for r in responses if r.status_code >= 500]
    self.assertEqual(
      server_errors,
      [],
      "an idempotency conflict is a 409, not a server fault; got "
      f"{self._summary(responses)}",
    )
    accepted = [r for r in responses if r.status_code < 300]
    conflicts = [r for r in responses if r.status_code == 409]
    self.assertLen(
      accepted, 1, f"exactly one racer may win; got {self._summary(responses)}"
    )
    self.assertLen(
      conflicts,
      RACERS - 1,
      "every loser must see 409 idempotency_conflict; got "
      f"{self._summary(responses)}",
    )


if __name__ == "__main__":
  absltest.main()
