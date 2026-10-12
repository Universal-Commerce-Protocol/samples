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

import assert from "node:assert/strict";
import { before, test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { OrderService } from "../src/api/order";
import { TestingService } from "../src/api/testing";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import {
  CheckoutCompleteRequestSchema,
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
  OrderSchema,
  type Order,
} from "../src/models";
import { UCP_VERSION } from "../src/utils/config";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

// Checkout/order business and protocol failures must answer with the UCP error
// envelope — `ucp.status: "error"` plus a typed `messages[]` entry carrying
// `code` and `content` — matching the Python reference server
// (rest/python/server/exceptions.py + server.py ucp_exception_handler),
// rather than a flat `{ detail }` or `{ error }` shape.
function buildApp() {
  const svc = new CheckoutService();
  const orderSvc = new OrderService();
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
  app.get(
    "/orders/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    orderSvc.getOrder
  );
  app.put(
    "/orders/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", OrderSchema, prettyValidation),
    orderSvc.updateOrder
  );
  app.post(
    "/checkout-sessions/:id/complete",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", CheckoutCompleteRequestSchema, prettyValidation),
    svc.completeCheckout
  );
  app.post(
    "/checkout-sessions/:id/cancel",
    zValidator("param", IdParamSchema, prettyValidation),
    svc.cancelCheckout
  );
  const testingSvc = new TestingService(svc);
  app.post(
    "/testing/simulate-shipping/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    testingSvc.shipOrder
  );
  return app;
}

before(() => {
  initDbs(":memory:", ":memory:");
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run("bouquet_roses", "Red Rose", 3500, "");
  const inv = getTransactionsDb().prepare(
    "INSERT INTO inventory (product_id, quantity) VALUES (?, ?)"
  );
  inv.run("bouquet_roses", 100);
  // A product whose stock is exhausted, for the OUT_OF_STOCK path.
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run("gardenias", "Gardenia", 2000, "");
  inv.run("gardenias", 0);
});

const JSON_HEADERS = { "Content-Type": "application/json" };
const CREATE_BODY = {
  currency: "USD",
  line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
  payment: {},
};

const ORDER_BODY: TestOrderBody = {
  checkout_id: "chk_order_envelope",
  currency: "USD",
  fulfillment: {},
  id: "ord_missing_envelope",
  line_items: [
    {
      id: "line_1",
      item: {
        id: "bouquet_roses",
        price: 3500,
        title: "Red Rose",
      },
      quantity: { fulfilled: 0, total: 1 },
      status: "processing",
      totals: [{ amount: 3500, type: "subtotal" }],
    },
  ],
  permalink_url: "https://example.com/orders/ord_missing_envelope",
  totals: [
    { amount: 3500, type: "subtotal" },
    { amount: 3500, type: "total" },
  ],
  ucp: { capabilities: {}, version: UCP_VERSION },
};

interface UcpErrorBody {
  ucp?: { version?: string; status?: string };
  messages?: Array<{
    type?: string;
    code?: string;
    content?: string;
    severity?: string;
  }>;
  detail?: string;
  error?: string;
}

type TestOrderBody = Order;

function assertUcpError(
  body: UcpErrorBody,
  code: string,
  severity = "unrecoverable"
) {
  assert.equal(body.detail, undefined, "flat detail shape must be gone");
  assert.equal(body.error, undefined, "flat error shape must be gone");
  assert.equal(body.ucp?.status, "error", "ucp.status must be 'error'");
  assert.equal(body.ucp?.version, UCP_VERSION);
  assert.ok(
    Array.isArray(body.messages) && body.messages.length > 0,
    "messages[] must carry the failure"
  );
  const msg = body.messages![0];
  assert.equal(msg.type, "error");
  assert.equal(msg.code, code);
  assert.ok(msg.content, "content must state the failure");
  assert.equal(msg.severity, severity);
}

async function create(app: ReturnType<typeof buildApp>, extra?: object) {
  return app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ ...CREATE_BODY, ...extra }),
  });
}

test("idempotency conflict answers 409 with an IDEMPOTENCY_CONFLICT envelope", async () => {
  const app = buildApp();
  const key = `key_${Date.now()}_envelope`;
  const first = await app.request("/checkout-sessions", {
    method: "POST",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
    body: JSON.stringify(CREATE_BODY),
  });
  assert.equal(first.status, 201);

  const conflicting = await app.request("/checkout-sessions", {
    method: "POST",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
    body: JSON.stringify({
      ...CREATE_BODY,
      line_items: [{ item: { id: "bouquet_roses" }, quantity: 2 }],
    }),
  });
  assert.equal(conflicting.status, 409);
  assertUcpError(
    (await conflicting.json()) as UcpErrorBody,
    "IDEMPOTENCY_CONFLICT"
  );
});

test("unknown checkout id answers 404 with a RESOURCE_NOT_FOUND envelope", async () => {
  const app = buildApp();
  const res = await app.request("/checkout-sessions/no_such_session");
  assert.equal(res.status, 404);
  assertUcpError((await res.json()) as UcpErrorBody, "RESOURCE_NOT_FOUND");
});

test("unknown order id answers 404 with a RESOURCE_NOT_FOUND envelope", async () => {
  const app = buildApp();
  const res = await app.request("/orders/no_such_order");
  assert.equal(res.status, 404);
  assertUcpError((await res.json()) as UcpErrorBody, "RESOURCE_NOT_FOUND");
});

test("updating an unknown order answers 404 with a RESOURCE_NOT_FOUND envelope", async () => {
  const app = buildApp();
  const res = await app.request("/orders/no_such_order", {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(ORDER_BODY),
  });
  assert.equal(res.status, 404);
  assertUcpError((await res.json()) as UcpErrorBody, "RESOURCE_NOT_FOUND");
});

test("simulate-shipping an unknown order answers 404 with a RESOURCE_NOT_FOUND envelope", async () => {
  const app = buildApp();
  const res = await app.request(
    "/testing/simulate-shipping/ord_missing_envelope",
    {
      method: "POST",
      headers: {
        "Simulation-Secret":
          process.env.SIMULATION_SECRET || "super-secret-sim-key",
      },
    }
  );
  assert.equal(res.status, 404);
  assertUcpError((await res.json()) as UcpErrorBody, "RESOURCE_NOT_FOUND");
});

test("updating a canceled checkout answers 409 with a CHECKOUT_NOT_MODIFIABLE envelope", async () => {
  const app = buildApp();
  const created = (await (await create(app)).json()) as { id: string };
  const canceled = await app.request(
    `/checkout-sessions/${created.id}/cancel`,
    { method: "POST", headers: JSON_HEADERS }
  );
  assert.equal(canceled.status, 200);

  const res = await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(CREATE_BODY),
  });
  assert.equal(res.status, 409);
  assertUcpError((await res.json()) as UcpErrorBody, "CHECKOUT_NOT_MODIFIABLE");
});

test("insufficient stock answers with an OUT_OF_STOCK envelope", async () => {
  const app = buildApp();
  const res = await create(app, {
    line_items: [{ item: { id: "gardenias" }, quantity: 1 }],
  });
  assert.equal(res.status, 400);
  assertUcpError((await res.json()) as UcpErrorBody, "OUT_OF_STOCK");
});

test("an unknown product answers with an INVALID_REQUEST envelope", async () => {
  const app = buildApp();
  const res = await create(app, {
    line_items: [{ item: { id: "no_such_product" }, quantity: 1 }],
  });
  assert.equal(res.status, 400);
  assertUcpError((await res.json()) as UcpErrorBody, "INVALID_REQUEST");
});

test("completion without fulfillment answers with an INVALID_REQUEST envelope", async () => {
  const app = buildApp();
  const created = (await (await create(app)).json()) as { id: string };
  const res = await app.request(`/checkout-sessions/${created.id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      payment: {
        instruments: [
          {
            id: "pi_1",
            handler_id: "mock_payment_handler",
            type: "card",
            brand: "visa",
            last_digits: "4242",
            credential: { type: "network_token", token: "success_token" },
          },
        ],
      },
    }),
  });
  assert.equal(res.status, 400);
  assertUcpError((await res.json()) as UcpErrorBody, "INVALID_REQUEST");
});
