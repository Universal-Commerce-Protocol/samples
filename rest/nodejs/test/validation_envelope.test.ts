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

// checkout-rest.md gives protocol errors one shape: a JSON body carrying
// code and content inside the UCP envelope. Requests rejected by payload
// validation are protocol errors like any other, so they must speak that
// shape too — a plain-text diagnostic gives the platform nothing to parse.

import assert from "node:assert/strict";
import { before, test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import { ExtendedCheckoutCreateRequestSchema } from "../src/models";
import { UCP_VERSION } from "../src/utils/config";
import { prettyValidation } from "../src/utils/validation";

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

async function create(app: ReturnType<typeof buildApp>, body: object) {
  return app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

test("validation failure answers with the UCP error envelope, not plain text", async () => {
  const app = buildApp();
  const res = await create(app, { line_items: "not-an-array" });
  assert.equal(res.status, 422);
  assert.match(
    res.headers.get("content-type") ?? "",
    /application\/json/,
    "validation errors must be JSON, not text"
  );
  const body = await res.json();
  assert.equal(body.ucp?.status, "error", "ucp.status must be 'error'");
  assert.equal(body.ucp?.version, UCP_VERSION);
  assert.ok(
    Array.isArray(body.messages) && body.messages.length > 0,
    "messages[] must carry the failure"
  );
  const msg = body.messages[0];
  assert.equal(msg.type, "error");
  assert.ok(msg.code, "code must be present");
  assert.ok(
    typeof msg.content === "string" && msg.content.includes("line_items"),
    "content must name the offending member"
  );
});

test("a valid create still succeeds after the envelope change", async () => {
  const app = buildApp();
  const res = await create(app, {
    line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
  });
  assert.equal(res.status, 201);
});
