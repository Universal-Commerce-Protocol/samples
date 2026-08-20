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

// checkout.json marks continue_url, expires_at, messages and order as
// ucp_request: omit, so the business owns them on the response. The create
// handler copies the request body into the response with a spread, so a
// client that sends one of these members must not see its value come back
// or persist.

import assert from "node:assert/strict";
import { before, test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import { ExtendedCheckoutCreateRequestSchema } from "../src/models";
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
  app.get(
    "/checkout-sessions/:id",
    zValidator("param", IdParamSchema, prettyValidation),
    service.getCheckout
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

const CLIENT_VALUES = {
  continue_url: "https://platform.example/client-chosen",
  expires_at: "2030-01-01T00:00:00Z",
  messages: [{ type: "info", code: "custom", content: "client supplied text" }],
  order: {
    id: "order_client_chosen",
    checkout_session_id: "fake",
    permalink_url: "https://platform.example/order",
  },
};

test("create does not adopt client supplied omit members", async () => {
  const app = buildApp();
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
      ...CLIENT_VALUES,
    }),
  });
  assert.equal(res.status, 201);
  const body = await res.json();
  assert.notEqual(
    body.continue_url,
    CLIENT_VALUES.continue_url,
    "continue_url is business owned"
  );
  assert.notEqual(
    body.expires_at,
    CLIENT_VALUES.expires_at,
    "expires_at is business owned"
  );
  const contents = (body.messages ?? []).map(
    (m: { content?: string }) => m.content
  );
  assert.ok(
    !contents.includes("client supplied text"),
    "messages are business owned"
  );
  assert.notEqual(
    body.order?.id,
    CLIENT_VALUES.order.id,
    "order is business owned"
  );

  // And nothing persisted: read the session back.
  const got = await app.request(`/checkout-sessions/${body.id}`);
  assert.equal(got.status, 200);
  const stored = await got.json();
  assert.notEqual(stored.continue_url, CLIENT_VALUES.continue_url);
  assert.notEqual(stored.expires_at, CLIENT_VALUES.expires_at);
  const storedContents = (stored.messages ?? []).map(
    (m: { content?: string }) => m.content
  );
  assert.ok(!storedContents.includes("client supplied text"));
  assert.notEqual(stored.order?.id, CLIENT_VALUES.order.id);
});

test("a create without these members is unaffected", async () => {
  const app = buildApp();
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
    }),
  });
  assert.equal(res.status, 201);
});
