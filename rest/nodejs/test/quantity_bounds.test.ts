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

// line_item.json declares quantity as an integer with minimum 1, and
// checkout.md requires additive well known totals types to have non negative
// amounts. The schema boundary is where that holds: a quantity below 1 must
// be rejected at validation, never priced.

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

const JSON_HEADERS = { "Content-Type": "application/json" };

function buildApp() {
  const service = new CheckoutService();
  const app = new Hono<{ Variables: { logger: typeof console } }>();
  app.use(async (c, next) => {
    c.set("logger", console);
    await next();
  });
  app.post(
    "/checkout-sessions",
    zValidator("json", ExtendedCheckoutCreateRequestSchema, prettyValidation),
    service.createCheckout
  );
  app.put(
    "/checkout-sessions/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    zValidator("json", ExtendedCheckoutUpdateRequestSchema, prettyValidation),
    service.updateCheckout
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

async function create(app: ReturnType<typeof buildApp>, quantity: number) {
  return app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      line_items: [{ item: { id: "bouquet_roses" }, quantity }],
    }),
  });
}

test("create rejects quantity 0 and negative quantity at validation", async () => {
  const app = buildApp();
  for (const quantity of [0, -1]) {
    const res = await create(app, quantity);
    assert.equal(
      res.status,
      422,
      `quantity ${quantity} must be rejected, not priced`
    );
  }
});

test("create rejects a fractional quantity", async () => {
  const app = buildApp();
  const res = await create(app, 1.5);
  assert.equal(res.status, 422);
});

test("update rejects quantity below 1 on an existing session", async () => {
  const app = buildApp();
  const created = await create(app, 2);
  assert.equal(created.status, 201);
  const { id } = await created.json();
  const res = await app.request(`/checkout-sessions/${id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      line_items: [{ item: { id: "bouquet_roses" }, quantity: -1 }],
    }),
  });
  assert.equal(res.status, 422);
});

test("a positive integer quantity still succeeds and prices normally", async () => {
  const app = buildApp();
  const res = await create(app, 2);
  assert.equal(res.status, 201);
  const body = await res.json();
  const total = (body.totals ?? []).find(
    (t: { type?: string }) => t.type === "total"
  );
  assert.equal(total?.amount, 7000);
});
