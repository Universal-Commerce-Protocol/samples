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
import { ExtendedCheckoutCreateRequestSchema } from "../src/models";
import { prettyValidation } from "../src/utils/validation";

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
  // Two units in stock — enough to test the in-stock path and to exceed.
  getTransactionsDb()
    .prepare("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)")
    .run("bouquet_roses", 2);
});

async function create(app: ReturnType<typeof buildApp>, lineItems: unknown) {
  return app.request("/checkout-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      currency: "USD",
      line_items: lineItems,
      payment: {},
    }),
  });
}

test("an unknown product id is rejected", async () => {
  const app = buildApp();
  const res = await create(app, [
    { item: { id: "no_such_product" }, quantity: 1 },
  ]);
  assert.equal(res.status, 400);
  const body = (await res.json()) as {
    messages?: Array<{ code?: string; content?: string }>;
  };
  assert.equal(body.messages?.[0]?.code, "INVALID_REQUEST");
  assert.match(body.messages?.[0]?.content ?? "", /not found/i);
});

test("ordering more than the available stock is rejected", async () => {
  const app = buildApp();
  const res = await create(app, [
    { item: { id: "bouquet_roses" }, quantity: 5 },
  ]);
  assert.equal(res.status, 400);
  const body = (await res.json()) as {
    messages?: Array<{ code?: string; content?: string }>;
  };
  assert.equal(body.messages?.[0]?.code, "OUT_OF_STOCK");
  assert.match(body.messages?.[0]?.content ?? "", /stock/i);
});

test("ordering within the available stock succeeds", async () => {
  const app = buildApp();
  const res = await create(app, [
    { item: { id: "bouquet_roses" }, quantity: 2 },
  ]);
  assert.equal(res.status, 201);
});
