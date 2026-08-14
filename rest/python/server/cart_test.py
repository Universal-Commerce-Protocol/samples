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
  ) -> cart_create_req.CartCreateRequest:
    """Create a cart payload using SDK models."""
    line_items = []
    for item_id, quantity in items:
      item = item_create_req.ItemCreateRequest(id=item_id)
      line_item = line_item_create_req.LineItemCreateRequest(
        quantity=quantity, item=item
      )
      line_items.append(line_item)

    return cart_create_req.CartCreateRequest(
      line_items=line_items,
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


if __name__ == "__main__":
  absltest.main()
