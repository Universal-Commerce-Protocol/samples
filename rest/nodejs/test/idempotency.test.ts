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
