// Copyright 2026 UCP Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Regression test: completion takes the payment only after its checks pass.
//
// completeCheckout used to decide the payment before it checked that each
// product still exists and reserved stock. A completion refused by either
// check ends in a 4xx that records no idempotent response, so a retry with the
// same Idempotency-Key decided the payment again. The mock handler charges
// nothing, but a real handler would charge for a checkout that never
// completes. The Python reference had the same order and was fixed the same
// way (rest/python/server/complete_payment_order_test.py). The fulfillment
// selection check, the first of the Python cases, already runs before the
// payment here, so it has no counterpart below.

import assert from "node:assert/strict";
import { before, test, type TestContext } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { getIdempotencyRecord, getInventory } from "../src/data";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import {
  CheckoutCompleteRequestSchema,
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
} from "../src/models";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

before(() => {
  initDbs(":memory:", ":memory:");
});

// The payment step is private, so it is cast to a public shape that
// t.mock.method can name.
type PaymentStep = { processPayment(payment: unknown): void };

// Wires the checkout routes (as lifecycle.test.ts does) around a service whose
// payment step is spied on. Each payment decision, a decline included, appends
// the stock on hand for `productId` at that moment, so a test sees both how
// many there were and whether the line was already reserved at each one.
function buildApp(t: TestContext, productId: string) {
  const svc = new CheckoutService();
  const step = svc as unknown as PaymentStep;
  const processPayment = step.processPayment;
  const stockAtPayment: (number | undefined)[] = [];
  t.mock.method(
    step,
    "processPayment",
    function (this: PaymentStep, payment: unknown) {
      stockAtPayment.push(getInventory(productId));
      return processPayment.call(this, payment);
    }
  );

  const app = new Hono<{ Variables: { logger: typeof console } }>();
  app.use(async (c, next) => {
    c.set("logger", console);
    await next();
  });
  app.post(
    "/checkout-sessions",
    zValidator("json", ExtendedCheckoutCreateRequestSchema, prettyValidation),
    svc.createCheckout
  );
  app.get(
    "/checkout-sessions/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    svc.getCheckout
  );
  app.put(
    "/checkout-sessions/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", ExtendedCheckoutUpdateRequestSchema, prettyValidation),
    svc.updateCheckout
  );
  app.post(
    "/checkout-sessions/:id/complete",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", CheckoutCompleteRequestSchema, prettyValidation),
    svc.completeCheckout
  );
  return { app, stockAtPayment };
}

type App = ReturnType<typeof buildApp>["app"];

const JSON_HEADERS = { "Content-Type": "application/json" };

function addProduct(id: string, stock: number): void {
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run(id, "Test Item", 2000, "");
  getTransactionsDb()
    .prepare("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)")
    .run(id, stock);
}

function countOrders(): number {
  const row = getTransactionsDb()
    .prepare("SELECT COUNT(*) AS n FROM orders")
    .get() as { n: number };
  return row.n;
}

function paymentWith(token: string) {
  return {
    payment: {
      instruments: [
        {
          id: "pi_1",
          handler_id: "mock_payment_handler",
          type: "card",
          // A non-"card" credential type routes to the mock token handler, so
          // the token drives the outcome.
          credential: { type: "network_token", token },
        },
      ],
    },
  };
}

// Creates a checkout for one unit of `productId` with a fulfillment
// destination and option selected, so completion's own checks decide.
async function createReadyToComplete(
  app: App,
  productId: string
): Promise<string> {
  const created = (await (
    await app.request("/checkout-sessions", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({
        currency: "USD",
        line_items: [{ item: { id: productId }, quantity: 1 }],
        payment: {},
        buyer: { email: "john.doe@example.com" },
        fulfillment: {
          methods: [{ type: "shipping", selected_destination_id: "addr_1" }],
        },
      }),
    })
  ).json()) as {
    id: string;
    line_items: { id: string; item: { id: string }; quantity: number }[];
    fulfillment: {
      methods: {
        groups: {
          id: string;
          line_item_ids: string[];
          options: { id: string }[];
        }[];
      }[];
    };
  };

  const group = created.fulfillment.methods[0].groups[0];
  const updated = await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: created.line_items.map((line) => ({
        id: line.id,
        item: { id: line.item.id },
        quantity: line.quantity,
      })),
      buyer: { email: "john.doe@example.com" },
      fulfillment: {
        methods: [
          {
            type: "shipping",
            selected_destination_id: "addr_1",
            groups: [
              {
                id: group.id,
                line_item_ids: group.line_item_ids,
                selected_option_id: group.options[0].id,
              },
            ],
          },
        ],
      },
    }),
  });
  assert.equal(updated.status, 200);
  return created.id;
}

function complete(
  app: App,
  id: string,
  idempotencyKey: string,
  token = "success_token"
) {
  return app.request(`/checkout-sessions/${id}/complete`, {
    method: "POST",
    headers: { ...JSON_HEADERS, "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(paymentWith(token)),
  });
}

async function errorCode(res: Response): Promise<string> {
  const body = (await res.json()) as { messages: { code: string }[] };
  return body.messages[0].code;
}

test("an out-of-stock line takes no payment, nor does its retry", async (t) => {
  addProduct("sold_out", 5);
  const { app, stockAtPayment } = buildApp(t, "sold_out");
  const id = await createReadyToComplete(app, "sold_out");
  getTransactionsDb()
    .prepare("UPDATE inventory SET quantity = 0 WHERE product_id = ?")
    .run("sold_out");

  // The request, then a retry with its Idempotency-Key.
  for (let attempt = 0; attempt < 2; attempt++) {
    const res = await complete(app, id, "out-of-stock-key");
    assert.equal(res.status, 409);
    assert.equal(await errorCode(res), "OUT_OF_STOCK");
  }
  assert.equal(
    stockAtPayment.length,
    0,
    "a completion refused for stock must take no payment"
  );
});

test("a deleted product takes no payment, nor does its retry", async (t) => {
  addProduct("delisted", 5);
  const { app, stockAtPayment } = buildApp(t, "delisted");
  const id = await createReadyToComplete(app, "delisted");
  getProductsDb().prepare("DELETE FROM products WHERE id = ?").run("delisted");

  // The request, then a retry with its Idempotency-Key.
  for (let attempt = 0; attempt < 2; attempt++) {
    const res = await complete(app, id, "deleted-product-key");
    assert.equal(res.status, 400);
    const body = (await res.json()) as {
      messages: { code: string; content: string }[];
    };
    assert.equal(body.messages[0].code, "INVALID_REQUEST");
    // Other refusals share this status and code; the content names this one.
    assert.equal(body.messages[0].content, "Product delisted not found");
  }
  assert.equal(
    stockAtPayment.length,
    0,
    "a completion refused for a deleted product must take no payment"
  );
});

test("a declined payment releases the reservation and records nothing", async (t) => {
  addProduct("declined", 5);
  const { app, stockAtPayment } = buildApp(t, "declined");
  const id = await createReadyToComplete(app, "declined");
  const ordersBefore = countOrders();

  const res = await complete(app, id, "declined-key", "fail_token");
  assert.equal(res.status, 402);
  assert.equal(await errorCode(res), "INSUFFICIENT_FUNDS");

  assert.deepEqual(
    stockAtPayment,
    [4],
    "the payment must be decided with the line already reserved"
  );
  assert.equal(
    getInventory("declined"),
    5,
    "the decline must release the reservation"
  );
  assert.equal(countOrders(), ordersBefore, "no order may be persisted");
  assert.equal(
    getIdempotencyRecord("declined-key"),
    undefined,
    "a declined completion must record no response to replay"
  );
  const checkout = (await (
    await app.request(`/checkout-sessions/${id}`)
  ).json()) as { status: string; order?: unknown };
  assert.equal(checkout.status, "ready_for_complete");
  assert.equal(checkout.order, undefined, "no order reference may survive");
});

test("a successful completion takes the payment once, after reserving stock once", async (t) => {
  addProduct("in_stock", 5);
  const { app, stockAtPayment } = buildApp(t, "in_stock");
  const id = await createReadyToComplete(app, "in_stock");

  const res = await complete(app, id, "happy-path-key");
  assert.equal(res.status, 200);
  const body = (await res.json()) as { status: string };
  assert.equal(body.status, "completed");

  assert.deepEqual(
    stockAtPayment,
    [4],
    "one payment, taken once the line is reserved"
  );
  assert.equal(getInventory("in_stock"), 4, "stock must be reserved once");
});
