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
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import {
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
} from "../src/models";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

function buildApp() {
  const svc = new CheckoutService();
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
  return app;
}

before(() => {
  initDbs(":memory:", ":memory:");
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run("bouquet_roses", "Red Rose", 3500, "");
  getTransactionsDb()
    .prepare("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)")
    .run("bouquet_roses", 100);
});

const BODY = {
  currency: "USD",
  line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
  payment: {},
};

async function post(
  app: ReturnType<typeof buildApp>,
  body: unknown,
  key?: string
) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (key) headers["Idempotency-Key"] = key;
  return app.request("/checkout-sessions", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}

test("same idempotency key + same body replays the first response", async () => {
  const app = buildApp();
  const first = (await post(app, BODY, "key-a").then((r) => r.json())) as {
    id: string;
  };
  const second = await post(app, BODY, "key-a");
  assert.equal(second.status, 201);
  const replayed = (await second.json()) as { id: string };
  assert.equal(
    replayed.id,
    first.id,
    "a replayed idempotency key must return the original checkout, not a new one"
  );
});

test("same idempotency key + different body is a 409 conflict", async () => {
  const app = buildApp();
  await post(app, BODY, "key-b");
  const conflicting = await post(
    app,
    { ...BODY, line_items: [{ item: { id: "bouquet_roses" }, quantity: 2 }] },
    "key-b"
  );
  assert.equal(conflicting.status, 409);
});

test("no idempotency key creates independent checkouts", async () => {
  const app = buildApp();
  const a = (await post(app, BODY).then((r) => r.json())) as { id: string };
  const b = (await post(app, BODY).then((r) => r.json())) as { id: string };
  assert.notEqual(a.id, b.id, "distinct requests must get distinct ids");
});

// A fuller app wiring create/update/cancel so idempotency scoping across
// operations and checkouts can be exercised end to end.
function buildFullApp() {
  const svc = new CheckoutService();
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
  app.put(
    "/checkout-sessions/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", ExtendedCheckoutUpdateRequestSchema, prettyValidation),
    svc.updateCheckout
  );
  app.post(
    "/checkout-sessions/:id/cancel",
    zValidator("param", IdParamSchema, prettyValidation),
    svc.cancelCheckout
  );
  return app;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

async function newCheckout(app: ReturnType<typeof buildFullApp>) {
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(BODY),
  });
  assert.equal(res.status, 201);
  return (await res.json()) as { id: string };
}

// An idempotency key must be scoped to the checkout it was first used on:
// reusing the same key against a different checkout is a conflict (409), not a
// silent replay of the first checkout's response.
test("an idempotency key is scoped to the checkout (cancel)", async () => {
  const app = buildFullApp();
  const a = await newCheckout(app);
  const b = await newCheckout(app);
  const key = "shared-cancel-key";
  const first = await app.request(`/checkout-sessions/${a.id}/cancel`, {
    method: "POST",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
  });
  const second = await app.request(`/checkout-sessions/${b.id}/cancel`, {
    method: "POST",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
  });
  assert.equal(first.status, 200);
  assert.equal(
    second.status,
    409,
    "reusing a key to cancel a different checkout must conflict, not replay"
  );
});

test("an idempotency key is scoped to the checkout (update)", async () => {
  const app = buildFullApp();
  const a = await newCheckout(app);
  const b = await newCheckout(app);
  const key = "shared-update-key";
  const first = await app.request(`/checkout-sessions/${a.id}`, {
    method: "PUT",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
    body: JSON.stringify(BODY),
  });
  const second = await app.request(`/checkout-sessions/${b.id}`, {
    method: "PUT",
    headers: { ...JSON_HEADERS, "Idempotency-Key": key },
    body: JSON.stringify(BODY),
  });
  assert.equal(first.status, 200);
  assert.equal(
    second.status,
    409,
    "reusing a key to update a different checkout must conflict, not replay"
  );
});
