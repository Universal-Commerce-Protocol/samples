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

"""Integration tests for the UCP Cart capability."""

import asyncio
import datetime
from typing import Any
from absl.testing import absltest
from integration_test import IntegrationTest, TestCheckout
from models import UnifiedCart as Cart
from sqlalchemy.sql import delete
from ucp_sdk.models.schemas.shopping import (
  cart_create_request as cart_create_req,
)
from ucp_sdk.models.schemas.shopping import (
  cart_update_request as cart_update_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  item_create_request as item_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  line_item_create_request as line_item_create_req,
)
from ucp_sdk.models.schemas.shopping.types import (
  line_item_update_request as line_item_update_req,
)
import db


class CartIntegrationTest(IntegrationTest):
  """Integration tests for Cart capability."""

  def _create_cart_payload(
    self,
    items: list[tuple[str, int]],
    **extra_fields: Any,
  ) -> cart_create_req.CartCreateRequest:
    """Create a cart payload using SDK models with optional field overrides."""
    line_items = []
    for item_id, quantity in items:
      item = item_create_req.ItemCreateRequest(id=item_id)
      line_item = line_item_create_req.LineItemCreateRequest(
        quantity=quantity, item=item
      )
      line_items.append(line_item)

    return cart_create_req.CartCreateRequest(
      line_items=line_items,
      **extra_fields,
    )

  def test_cart_lifecycle(self) -> None:
    """Test Create, Get, Update, and Cancel Cart."""
    with self.client:
      # 1. Create Cart
      payload = self._create_cart_payload([("rose", 2)])
      response = self.client.post(
        "/carts",
        headers=self._get_headers(idempotency_key="cart_1", request_id="r1"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      cart = Cart.model_validate(response.json())
      self.assertTrue(cart.id.startswith("cart_"))
      self.assertEqual(len(cart.line_items), 1)
      self.assertEqual(cart.line_items[0].item.id, "rose")
      self.assertEqual(cart.line_items[0].quantity, 2)
      self.assertEqual(cart.line_items[0].item.price, 1000)
      # Totals: subtotal = 2000, total = 2000
      subtotal = next(t.amount for t in cart.totals if t.type == "subtotal")
      total = next(t.amount for t in cart.totals if t.type == "total")
      self.assertEqual(subtotal, 2000)
      self.assertEqual(total, 2000)

      cart_id = cart.id

      # 2. Get Cart
      response = self.client.get(
        f"/carts/{cart_id}",
        headers=self._get_headers(request_id="r2"),
      )
      self.assertEqual(response.status_code, 200, response.text)
      cart = Cart.model_validate(response.json())
      self.assertEqual(cart.id, cart_id)
      self.assertEqual(cart.line_items[0].quantity, 2)

      # 3. Update Cart (Replace items: 1 rose, 1 tulip)
      line_items_update = [
        line_item_update_req.LineItemUpdateRequest(
          item={"id": "rose"},
          quantity=1,
        ),
        line_item_update_req.LineItemUpdateRequest(
          item={"id": "tulip"},
          quantity=1,
        ),
      ]
      update_payload = cart_update_req.CartUpdateRequest(
        id=cart_id,
        line_items=line_items_update,
      )
      response = self.client.put(
        f"/carts/{cart_id}",
        headers=self._get_headers(idempotency_key="cart_2", request_id="r3"),
        json=update_payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 200, response.text)
      cart = Cart.model_validate(response.json())
      self.assertEqual(cart.id, cart_id)
      self.assertEqual(len(cart.line_items), 2)
      # Totals: 1000 (rose) + 800 (tulip) = 1800
      subtotal = next(t.amount for t in cart.totals if t.type == "subtotal")
      total = next(t.amount for t in cart.totals if t.type == "total")
      self.assertEqual(subtotal, 1800)
      self.assertEqual(total, 1800)

      # 4. Cancel Cart
      response = self.client.post(
        f"/carts/{cart_id}/cancel",
        headers=self._get_headers(idempotency_key="cart_3", request_id="r4"),
      )
      self.assertEqual(response.status_code, 200, response.text)
      cart = Cart.model_validate(response.json())
      self.assertEqual(cart.id, cart_id)

      # 5. Verify Get Cart returns Not Found (HTTP 404 in our case because we
      # raise ResourceNotFoundError)
      response = self.client.get(
        f"/carts/{cart_id}",
        headers=self._get_headers(request_id="r5"),
      )
      self.assertEqual(response.status_code, 404, response.text)
      data = response.json()
      self.assertEqual(data["ucp"]["status"], "error")
      self.assertEqual(data["messages"][0]["code"], "RESOURCE_NOT_FOUND")

  def test_cart_to_checkout_conversion(self) -> None:
    """Test converting a cart to a checkout session."""
    with self.client:
      # 1. Create Cart
      payload = self._create_cart_payload([("rose", 2)])
      response = self.client.post(
        "/carts",
        headers=self._get_headers(idempotency_key="c_conv_1", request_id="rc1"),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      cart = Cart.model_validate(response.json())
      cart_id = cart.id

      # 2. Create Checkout using cart_id
      checkout_payload = self._create_checkout_payload(
        "test_checkout_from_cart", [("rose", "Red Rose", 1000, 99)]
      ).model_dump(mode="json", exclude_none=True)
      checkout_payload["cart_id"] = cart_id

      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="c_conv_2", request_id="rc2"),
        json=checkout_payload,
      )
      self.assertEqual(response.status_code, 201, response.text)
      checkout = TestCheckout.model_validate(response.json())
      checkout_id = self.get_resource_id(checkout.id)
      self.assertIsInstance(checkout_id, str)
      self.assertEqual(checkout.cart_id, cart_id)
      self.assertEqual(len(checkout.line_items), 1)
      self.assertEqual(checkout.line_items[0].item.id, "rose")
      self.assertEqual(checkout.line_items[0].quantity, 2)
      subtotal = next(t.amount for t in checkout.totals if t.type == "subtotal")
      self.assertEqual(subtotal, 2000)

      # 3. Idempotent Conversion: Create another checkout with same cart_id
      checkout_payload_2 = self._create_checkout_payload(
        "test_checkout_from_cart_2", [("rose", "Red Rose", 1000, 1)]
      ).model_dump(mode="json", exclude_none=True)
      checkout_payload_2["cart_id"] = cart_id

      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(idempotency_key="c_conv_3", request_id="rc3"),
        json=checkout_payload_2,
      )
      self.assertEqual(response.status_code, 201)
      checkout_2 = TestCheckout.model_validate(response.json())
      self.assertEqual(self.get_resource_id(checkout_2.id), checkout_id)
      self.assertEqual(checkout_2.cart_id, cart_id)

      # 4. Complete Checkout
      payment_payload = self._create_payment_payload()
      response = self.client.post(
        f"/checkout-sessions/{checkout_id}/complete",
        headers=self._get_headers(idempotency_key="c_conv_4", request_id="rc4"),
        json=payment_payload,
      )
      self.assertEqual(response.status_code, 200, response.text)
      checkout_comp = TestCheckout.model_validate(response.json())
      self.assertEqual(checkout_comp.status, "completed")

      # 5. Verify Cart is cleared (deleted) after completion
      response = self.client.get(
        f"/carts/{cart_id}",
        headers=self._get_headers(request_id="rc5"),
      )
      self.assertEqual(response.status_code, 404, response.text)

  def test_cart_with_discount(self) -> None:
    """Test applying a discount code to a cart."""

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
      # 1. Create Cart
      payload = self._create_cart_payload([("rose", 2)])
      response = self.client.post(
        "/carts",
        headers=self._get_headers(
          idempotency_key="cart_disc_1", request_id="rd1"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201)
      cart = Cart.model_validate(response.json())
      cart_id = cart.id

      # 2. Update Cart with discount code
      update_payload = {
        "id": cart_id,
        "line_items": [
          {"item": {"id": "rose"}, "quantity": 2},
        ],
        "discounts": {"codes": ["10OFF"]},
      }
      response = self.client.put(
        f"/carts/{cart_id}",
        headers=self._get_headers(
          idempotency_key="cart_disc_2", request_id="rd2"
        ),
        json=update_payload,
      )
      self.assertEqual(response.status_code, 200, response.text)
      cart = Cart.model_validate(response.json())
      self.assertEqual(cart.id, cart_id)

      # Verify discounts in response
      self.assertIsNotNone(cart.discounts)
      self.assertEqual(cart.discounts.codes, ["10OFF"])
      self.assertEqual(len(cart.discounts.applied), 1)
      self.assertEqual(cart.discounts.applied[0].code, "10OFF")
      self.assertEqual(cart.discounts.applied[0].amount, 200)

      # Verify totals
      subtotal = next(t.amount for t in cart.totals if t.type == "subtotal")
      discount = next(t.amount for t in cart.totals if t.type == "discount")
      total = next(t.amount for t in cart.totals if t.type == "total")
      self.assertEqual(subtotal, 2000)
      self.assertEqual(discount, -200)
      self.assertEqual(total, 1800)

  def test_cart_to_checkout_conversion_with_discount(self) -> None:
    """Test discount carry-forward during cart-to-checkout conversion."""

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
      # 1. Create Cart with discount
      create_payload = self._create_cart_payload([("rose", 2)]).model_dump(
        mode="json", exclude_none=True
      )
      create_payload["discounts"] = {"codes": ["10OFF"]}

      response = self.client.post(
        "/carts",
        headers=self._get_headers(
          idempotency_key="cart_c_disc_1", request_id="rcd1"
        ),
        json=create_payload,
      )
      self.assertEqual(response.status_code, 201)
      cart = Cart.model_validate(response.json())
      cart_id = cart.id
      self.assertEqual(len(cart.discounts.applied), 1)

      # 2. Convert to Checkout
      checkout_payload = self._create_checkout_payload(
        "test_checkout_from_cart_disc", [("rose", "Red Rose", 1000, 2)]
      ).model_dump(mode="json", exclude_none=True)
      checkout_payload["cart_id"] = cart_id

      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="cart_c_disc_2", request_id="rcd2"
        ),
        json=checkout_payload,
      )
      self.assertEqual(response.status_code, 201, response.text)
      checkout = TestCheckout.model_validate(response.json())
      checkout_id = self.get_resource_id(checkout.id)
      self.assertIsInstance(checkout_id, str)
      self.assertEqual(checkout.cart_id, cart_id)

      # Verify discounts carried forward
      self.assertIsNotNone(checkout.discounts)
      self.assertEqual(checkout.discounts.codes, ["10OFF"])
      self.assertEqual(len(checkout.discounts.applied), 1)
      self.assertEqual(checkout.discounts.applied[0].code, "10OFF")
      self.assertEqual(checkout.discounts.applied[0].amount, 200)

      # Verify totals
      subtotal = next(t.amount for t in checkout.totals if t.type == "subtotal")
      discount = next(t.amount for t in checkout.totals if t.type == "discount")
      total = next(t.amount for t in checkout.totals if t.type == "total")
      self.assertEqual(subtotal, 2000)
      self.assertEqual(discount, -200)
      self.assertEqual(total, 1800)

  def test_create_cart_does_not_adopt_client_supplied_omit_members(
    self,
  ) -> None:
    """Cart create carrying omit members must not adopt them or 500.

    cart.json marks ucp, currency, totals, continue_url, expires_at, messages,
    and links as ucp_request: omit, and id as omit on create. The create handler
    must exclude them from cart_data so keyword collisions (TypeError) and
    client value leaks are avoided.
    """
    client_values = {
      "currency": "XTS",
      "id": "cart_client_chosen",
      "totals": [{"type": "subtotal", "amount": 9999}],
      "continue_url": "https://platform.example/client-continue",
      "expires_at": "2030-01-01T00:00:00Z",
      "messages": [
        {
          "type": "info",
          "code": "custom",
          "content": "client text",
          "severity": "recoverable",
        }
      ],
      "links": [{"type": "terms_of_use", "url": "https://example.com/tos"}],
    }

    with self.client:
      payload = self._create_cart_payload(
        [("rose", 1)],
        **client_values,
      )
      payload.line_items[0].id = "client_line_1"

      response = self.client.post(
        "/carts",
        headers=self._get_headers(
          idempotency_key="cart_omit_1", request_id="co1"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      cart = Cart.model_validate(response.json())

      self.assertEqual(cart.currency, "USD")
      self.assertNotEqual(cart.id, client_values["id"])
      self.assertNotEqual(str(cart.continue_url), client_values["continue_url"])
      self.assertNotEqual(
        cart.expires_at.isoformat() if cart.expires_at else None,
        client_values["expires_at"],
      )
      contents = [m.content for m in (cart.messages or [])]
      self.assertNotIn("client text", contents)
      self.assertNotEqual(cart.links, client_values["links"])
      self.assertNotEqual(cart.line_items[0].id, "client_line_1")

      # Verify persistence: GET /carts/{cart_id}
      cart_id = cart.id
      get_res = self.client.get(
        f"/carts/{cart_id}",
        headers=self._get_headers(request_id="co1_get"),
      )
      self.assertEqual(get_res.status_code, 200, f"Response: {get_res.text}")
      stored = Cart.model_validate(get_res.json())
      self.assertEqual(stored.currency, "USD")
      self.assertNotEqual(
        str(stored.continue_url), client_values["continue_url"]
      )
      self.assertNotEqual(
        stored.expires_at.isoformat() if stored.expires_at else None,
        client_values["expires_at"],
      )
      stored_contents = [m.content for m in (stored.messages or [])]
      self.assertNotIn("client text", stored_contents)
      self.assertNotEqual(stored.links, client_values["links"])

  def test_create_cart_ignores_non_string_members(self) -> None:
    """A cart create carrying non-string members must never 500."""
    with self.client:
      response = self.client.post(
        "/carts",
        headers=self._get_headers(
          idempotency_key="cart_non_str_1", request_id="cns1"
        ),
        json={
          "line_items": [{"item": {"id": "rose"}, "quantity": 1, "id": 123}],
          "currency": 123,
          "id": 123,
        },
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      body = response.json()
      self.assertEqual(body.get("currency"), "USD")
      self.assertIsInstance(body.get("id"), str)
      self.assertIsInstance(body["line_items"][0].get("id"), str)

  def test_cart_with_attribution_converts_to_checkout(self) -> None:
    """A cart carrying attribution converts to checkout successfully."""
    with self.client:
      payload = self._create_cart_payload(
        [("rose", 1)],
        attribution={
          "campaign_id": "123",
          "campaign_source": "newsletter",
        },
      )

      response = self.client.post(
        "/carts",
        headers=self._get_headers(
          idempotency_key="cart_attr_1", request_id="ca1"
        ),
        json=payload.model_dump(mode="json", exclude_none=True),
      )
      self.assertEqual(response.status_code, 201, f"Response: {response.text}")
      cart = response.json()
      cart_id = cart["id"]
      self.assertEqual(cart.get("attribution", {}).get("campaign_id"), "123")

      # Convert to checkout
      checkout_payload = {
        "cart_id": cart_id,
      }
      res = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="cart_attr_conv_1", request_id="ca_conv1"
        ),
        json=checkout_payload,
      )
      self.assertEqual(res.status_code, 201, f"Response: {res.text}")
      checkout = res.json()
      self.assertIsNotNone(checkout.get("attribution"))
      self.assertEqual(
        checkout.get("attribution", {}).get("campaign_id"), "123"
      )

  def test_idempotency_key_does_not_replay_across_carts(self) -> None:
    """An idempotency key is scoped to one operation on one resource.

    Cancel Cart hashes only the request body, which is empty for a cancel, so
    every cancel of every cart produced the same fingerprint. Replaying one
    key against a different cart then returned the first cart and left the
    second one untouched. CheckoutService already scopes the fingerprint by
    operation and resource id, and answers 409 in the same situation.
    """
    with self.client:
      cart_ids = []
      for index in (1, 2):
        payload = self._create_cart_payload([("rose", index)])
        response = self.client.post(
          "/carts",
          headers=self._get_headers(
            idempotency_key=f"replay_create_{index}",
            request_id=f"replay_r{index}",
          ),
          json=payload.model_dump(mode="json", exclude_none=True),
        )
        self.assertEqual(response.status_code, 201, response.text)
        cart_ids.append(Cart.model_validate(response.json()).id)

      first_id, second_id = cart_ids
      self.assertNotEqual(first_id, second_id)

      shared_key = "replay_cancel_key"
      response = self.client.post(
        f"/carts/{first_id}/cancel",
        headers=self._get_headers(
          idempotency_key=shared_key, request_id="replay_r3"
        ),
      )
      self.assertEqual(response.status_code, 200, response.text)
      self.assertEqual(Cart.model_validate(response.json()).id, first_id)

      # The same key against a different cart is a different operation, so it
      # is a conflict rather than a replay.
      response = self.client.post(
        f"/carts/{second_id}/cancel",
        headers=self._get_headers(
          idempotency_key=shared_key, request_id="replay_r4"
        ),
      )
      self.assertEqual(response.status_code, 409, response.text)
      self.assertEqual(
        response.json()["messages"][0]["code"], "IDEMPOTENCY_CONFLICT"
      )

      # The second cart must still exist, because its cancel never ran.
      response = self.client.get(
        f"/carts/{second_id}",
        headers=self._get_headers(request_id="replay_r5"),
      )
      self.assertEqual(response.status_code, 200, response.text)
      self.assertEqual(Cart.model_validate(response.json()).id, second_id)

  def test_idempotency_key_does_not_replay_across_cart_updates(self) -> None:
    """The same scoping rule applies to Update Cart.

    Update hashed only the request body, so the same body sent under one key
    against two different carts replayed the response of the first cart and
    left
    the second cart unmodified.
    """
    with self.client:
      cart_ids = []
      for index in (3, 4):
        payload = self._create_cart_payload([("rose", 1)])
        response = self.client.post(
          "/carts",
          headers=self._get_headers(
            idempotency_key=f"replay_upd_create_{index}",
            request_id=f"replay_ur{index}",
          ),
          json=payload.model_dump(mode="json", exclude_none=True),
        )
        self.assertEqual(response.status_code, 201, response.text)
        cart_ids.append(Cart.model_validate(response.json()).id)

      first_id, second_id = cart_ids
      # The SAME body is sent to both carts, so the only thing distinguishing
      # the two requests is the resource they target. If the fingerprint does
      # not include that, the second request replays the first.
      update_body = self._create_cart_payload([("rose", 5)]).model_dump(
        mode="json", exclude_none=True
      )
      update_body["id"] = first_id

      shared_key = "replay_update_key"
      response = self.client.put(
        f"/carts/{first_id}",
        headers=self._get_headers(
          idempotency_key=shared_key, request_id="replay_ur5"
        ),
        json=update_body,
      )
      self.assertEqual(response.status_code, 200, response.text)

      response = self.client.put(
        f"/carts/{second_id}",
        headers=self._get_headers(
          idempotency_key=shared_key, request_id="replay_ur6"
        ),
        json=update_body,
      )
      self.assertEqual(response.status_code, 409, response.text)

      # The second cart must be unchanged, because its update never ran.
      response = self.client.get(
        f"/carts/{second_id}",
        headers=self._get_headers(request_id="replay_ur7"),
      )
      self.assertEqual(response.status_code, 200, response.text)
      self.assertEqual(
        Cart.model_validate(response.json()).line_items[0].quantity, 1
      )

  def _create_cart(self, key: str) -> str:
    """Create a one-rose cart and return its id."""
    response = self.client.post(
      "/carts",
      headers=self._get_headers(idempotency_key=key, request_id=key),
      json=self._create_cart_payload([("rose", 1)]).model_dump(
        mode="json", exclude_none=True
      ),
    )
    self.assertEqual(response.status_code, 201, response.text)
    return response.json()["id"]

  def _set_cart_expiry(self, cart_id: str, expires_at: str) -> None:
    """Overwrite a stored cart's expires_at."""

    async def update() -> None:
      async with self.transactions_session_factory() as session:
        row = await session.get(db.CartSession, cart_id)
        row.data = {**row.data, "expires_at": expires_at}
        await session.commit()

    asyncio.run(update())

  def test_expired_cart_is_not_found(self) -> None:
    """An expired cart answers not found instead of being served.

    cart.md, Get Cart: returns not_found if the cart does not exist, has
    expired, or was canceled. The cart's expires_at was never checked, so a
    cart past it was still returned.
    """
    with self.client:
      cart_id = self._create_cart("expired_get_1")
      self._set_cart_expiry(cart_id, "2020-01-01T00:00:00Z")

      response = self.client.get(
        f"/carts/{cart_id}", headers=self._get_headers(request_id="exp_get")
      )
      self.assertEqual(response.status_code, 404, response.text)
      error = response.json()
      self.assertEqual(error["ucp"]["status"], "error")
      self.assertEqual(error["messages"][0]["code"], "RESOURCE_NOT_FOUND")

  def test_expired_cart_cannot_become_a_checkout(self) -> None:
    """A checkout cannot be created from a cart that has expired."""
    with self.client:
      cart_id = self._create_cart("expired_conv_1")
      self._set_cart_expiry(cart_id, "2020-01-01T00:00:00Z")

      checkout_payload = self._create_checkout_payload(
        "expired_conv", [("rose", "Red Rose", 1000, 99)]
      ).model_dump(mode="json", exclude_none=True)
      checkout_payload["cart_id"] = cart_id
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="expired_conv_2", request_id="exp_conv"
        ),
        json=checkout_payload,
      )
      self.assertEqual(response.status_code, 404, response.text)
      error = response.json()
      self.assertEqual(error["ucp"]["status"], "error")
      self.assertEqual(error["messages"][0]["code"], "RESOURCE_NOT_FOUND")

      async def count_checkouts() -> int:
        async with self.transactions_session_factory() as session:
          return len(await db.get_checkouts_by_cart_id(session, cart_id))

      self.assertEqual(asyncio.run(count_checkouts()), 0)

  def test_expired_update_and_cancel_preserve_state(self) -> None:
    """Expired mutations return not found without changing stored state."""

    async def stored_state(
      cart_id: str, key: str
    ) -> tuple[dict[str, Any] | None, db.IdempotencyRecord | None]:
      async with self.transactions_session_factory() as session:
        return (
          await db.get_cart_session(session, cart_id),
          await db.get_idempotency_record(session, key),
        )

    with self.client:
      for operation in ("update", "cancel"):
        with self.subTest(operation=operation):
          cart_id = self._create_cart(f"expired_{operation}_create")
          self._set_cart_expiry(cart_id, "2020-01-01T00:00:00Z")
          key = f"expired_{operation}_mutation"

          before, _ = asyncio.run(stored_state(cart_id, key))
          headers = self._get_headers(idempotency_key=key, request_id=key)
          if operation == "update":
            body = self._create_cart_payload([("rose", 5)]).model_dump(
              mode="json", exclude_none=True
            )
            body["id"] = cart_id
            response = self.client.put(
              f"/carts/{cart_id}", headers=headers, json=body
            )
          else:
            response = self.client.post(
              f"/carts/{cart_id}/cancel", headers=headers
            )

          self.assertEqual(response.status_code, 404, response.text)
          error = response.json()
          self.assertEqual(error["ucp"]["status"], "error")
          self.assertEqual(error["messages"][0]["code"], "RESOURCE_NOT_FOUND")
          after, idempotency_record = asyncio.run(stored_state(cart_id, key))
          self.assertEqual(after, before)
          self.assertIsNone(idempotency_record)

  def test_unexpired_cart_is_served_and_converted(self) -> None:
    """A cart with a future expires_at still reads and converts."""
    with self.client:
      cart_id = self._create_cart("unexpired_1")
      self._set_cart_expiry(cart_id, "2999-01-01T00:00:00Z")

      response = self.client.get(
        f"/carts/{cart_id}", headers=self._get_headers(request_id="unexp_get")
      )
      self.assertEqual(response.status_code, 200, response.text)

      checkout_payload = self._create_checkout_payload(
        "unexpired_conv", [("rose", "Red Rose", 1000, 99)]
      ).model_dump(mode="json", exclude_none=True)
      checkout_payload["cart_id"] = cart_id
      response = self.client.post(
        "/checkout-sessions",
        headers=self._get_headers(
          idempotency_key="unexpired_2", request_id="unexp_conv"
        ),
        json=checkout_payload,
      )
      self.assertEqual(response.status_code, 201, response.text)

  def test_cart_expiry_boundary(self) -> None:
    """A cart is expired from the instant expires_at is reached."""
    from services.cart_service import is_cart_expired

    now = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    one_tick = datetime.timedelta(microseconds=1)

    def cart(expires_at: datetime.datetime) -> dict[str, Any]:
      return {"expires_at": expires_at.isoformat().replace("+00:00", "Z")}

    self.assertTrue(is_cart_expired(cart(now - one_tick), now))
    self.assertTrue(is_cart_expired(cart(now), now))
    self.assertFalse(is_cart_expired(cart(now + one_tick), now))
    # A cart that sets no expiry never expires.
    self.assertFalse(is_cart_expired({}, now))

  def test_cart_expiry_timestamp_formats(self) -> None:
    """UTC suffixes, offsets, and naive stored times share the same boundary."""
    from services.cart_service import is_cart_expired

    now = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    for suffix, hour in (("Z", 12), ("z", 12), ("", 12), ("+02:00", 14)):
      for second, expected in (("00", True), ("00.000001", False)):
        expires_at = f"2026-01-01T{hour:02}:00:{second}{suffix}"
        with self.subTest(expires_at=expires_at):
          self.assertEqual(
            is_cart_expired({"expires_at": expires_at}, now), expected
          )


if __name__ == "__main__":
  absltest.main()
