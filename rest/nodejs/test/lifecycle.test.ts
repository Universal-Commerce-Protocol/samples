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
  CheckoutCompleteRequestSchema,
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
} from "../src/models";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

// A minimal app wired with just the checkout routes (no request logging
// middleware, which needs the node-server request context), so the lifecycle
// can be exercised end to end through app.request() — the same convention as
// discovery.test.ts.
function buildApp() {
  const svc = new CheckoutService();
  const app = new Hono<{ Variables: { logger: typeof console } }>();
  // The validation hook logs via c.var.logger; provide one so the routes can
  // run without the production pino middleware (which needs a node-server ctx).
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
  app.post(
    "/checkout-sessions/:id/cancel",
    zValidator("param", IdParamSchema, prettyValidation),
    svc.cancelCheckout
  );
  return app;
}

before(() => {
  initDbs(":memory:", ":memory:");
  const db = getProductsDb();
  db.prepare(
    "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
  ).run("bouquet_roses", "Red Rose", 3500, "");
  getTransactionsDb()
    .prepare("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)")
    .run("bouquet_roses", 100);
});

const JSON_HEADERS = { "Content-Type": "application/json" };
const CREATE_BODY = {
  currency: "USD",
  line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
  payment: {},
};
function paymentWith(token: string) {
  return {
    payment: {
      instruments: [
        {
          id: "pi_1",
          handler_id: "mock_payment_handler",
          type: "card",
          brand: "visa",
          last_digits: "4242",
          // A non-"card" credential type routes to the mock token handler, so
          // the token drives the outcome (success_token / fail_token /
          // fraud_token).
          credential: { type: "network_token", token },
        },
      ],
    },
  };
}
const SUCCESS_PAYMENT = paymentWith("success_token");

async function create(app: ReturnType<typeof buildApp>) {
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(CREATE_BODY),
  });
  return res;
}

async function complete(
  app: ReturnType<typeof buildApp>,
  id: string,
  body: unknown = SUCCESS_PAYMENT
) {
  return app.request(`/checkout-sessions/${id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

// The merchant refuses to complete a checkout until a fulfillment destination
// and option are selected, so drive a checkout through that selection (create
// with a known-customer shipping destination, then choose the quoted option)
// and return its id ready to complete. See fulfillment.test.ts for the
// dedicated coverage of that selection flow.
async function createReadyToComplete(
  app: ReturnType<typeof buildApp>
): Promise<string> {
  const created = (await (
    await app.request("/checkout-sessions", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({
        currency: "USD",
        line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
        payment: {},
        buyer: { email: "john.doe@example.com" },
        fulfillment: {
          methods: [{ type: "shipping", selected_destination_id: "addr_1" }],
        },
      }),
    })
  ).json()) as {
    id: string;
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
  await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: [
        { id: "line_1", item: { id: "bouquet_roses" }, quantity: 1 },
      ],
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
  return created.id;
}

test("create returns 201 with an id and an incomplete status", async () => {
  const app = buildApp();
  const res = await create(app);
  assert.equal(res.status, 201);
  const body = (await res.json()) as { id: string; status: string };
  assert.ok(body.id, "checkout must carry a server-assigned id");
  assert.equal(body.status, "incomplete");
});

test("a created checkout is retrievable by id", async () => {
  const app = buildApp();
  const created = (await (await create(app)).json()) as { id: string };
  const res = await app.request(`/checkout-sessions/${created.id}`);
  assert.equal(res.status, 200);
  const got = (await res.json()) as { id: string };
  assert.equal(got.id, created.id);
});

test("complete moves the checkout to an order", async () => {
  const app = buildApp();
  const id = await createReadyToComplete(app);
  const res = await complete(app, id);
  assert.equal(res.status, 200);
  const body = (await res.json()) as { status: string; order?: { id: string } };
  assert.equal(body.status, "completed");
  assert.ok(body.order?.id, "completion must assign an order id");
});

test("completing an already-completed checkout is rejected (409)", async () => {
  const app = buildApp();
  const id = await createReadyToComplete(app);
  await complete(app, id);
  const again = await complete(app, id);
  assert.equal(again.status, 409);
});

test("a failing payment token surfaces a 402", async () => {
  const app = buildApp();
  const id = await createReadyToComplete(app);
  const res = await complete(app, id, paymentWith("fail_token"));
  assert.equal(res.status, 402);
});

test("cancel moves the checkout to canceled", async () => {
  const app = buildApp();
  const created = (await (await create(app)).json()) as { id: string };
  const res = await app.request(`/checkout-sessions/${created.id}/cancel`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({}),
  });
  assert.equal(res.status, 200);
  const body = (await res.json()) as { status: string };
  assert.equal(body.status, "canceled");
});

test("a canceled checkout cannot be completed (409)", async () => {
  const app = buildApp();
  const id = await createReadyToComplete(app);
  await app.request(`/checkout-sessions/${id}/cancel`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({}),
  });
  const res = await complete(app, id);
  assert.equal(res.status, 409);
});

// The 04-08 schema binds checkout responses to
// `ucp.json#/$defs/response_checkout_schema`, whose `allOf` adds
// `required: ["payment_handlers"]` to the `ucp` envelope. `payment_handlers`
// is typed as an object (a map of handler key -> handler[]); an empty object
// satisfies the requirement, which is exactly what the Python reference emits
// (`ResponseCheckout(..., payment_handlers={})`). Every checkout response path
// (create, get, update, complete, cancel) must therefore carry
// `ucp.payment_handlers` as a present, non-null object.
function assertPaymentHandlers(label: string, ucp: unknown): void {
  assert.ok(
    ucp && typeof ucp === "object",
    `${label}: response must carry a ucp envelope`
  );
  const envelope = ucp as { payment_handlers?: unknown };
  assert.ok(
    "payment_handlers" in envelope,
    `${label}: ucp.payment_handlers is required by response_checkout_schema`
  );
  const handlers = envelope.payment_handlers;
  assert.ok(
    handlers !== null &&
      typeof handlers === "object" &&
      !Array.isArray(handlers),
    `${label}: ucp.payment_handlers must be an object, got ${JSON.stringify(
      handlers
    )}`
  );
}

test("every checkout response carries ucp.payment_handlers (schema-required)", async () => {
  const app = buildApp();

  // create (POST /checkout-sessions -> 201)
  const createRes = await create(app);
  assert.equal(createRes.status, 201);
  const created = (await createRes.json()) as { id: string; ucp?: unknown };
  assertPaymentHandlers("create", created.ucp);

  // get (GET /checkout-sessions/:id -> 200)
  const getRes = await app.request(`/checkout-sessions/${created.id}`);
  assert.equal(getRes.status, 200);
  const got = (await getRes.json()) as { ucp?: unknown };
  assertPaymentHandlers("get", got.ucp);

  // update (PUT /checkout-sessions/:id -> 200)
  const updateRes = await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: [
        { id: "line_1", item: { id: "bouquet_roses" }, quantity: 2 },
      ],
    }),
  });
  assert.equal(updateRes.status, 200);
  const updated = (await updateRes.json()) as { ucp?: unknown };
  assertPaymentHandlers("update", updated.ucp);

  // complete (POST /checkout-sessions/:id/complete -> 200)
  const completeId = await createReadyToComplete(app);
  const completeRes = await complete(app, completeId);
  assert.equal(completeRes.status, 200);
  const completed = (await completeRes.json()) as { ucp?: unknown };
  assertPaymentHandlers("complete", completed.ucp);

  // cancel (POST /checkout-sessions/:id/cancel -> 200)
  const toCancel = (await (await create(app)).json()) as { id: string };
  const cancelRes = await app.request(
    `/checkout-sessions/${toCancel.id}/cancel`,
    {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({}),
    }
  );
  assert.equal(cancelRes.status, 200);
  const canceled = (await cancelRes.json()) as { ucp?: unknown };
  assertPaymentHandlers("cancel", canceled.ucp);
});

test("an idempotent create replay still carries ucp.payment_handlers", async () => {
  const app = buildApp();
  const headers = { ...JSON_HEADERS, "Idempotency-Key": "pay-handlers-replay" };
  const body = JSON.stringify(CREATE_BODY);

  const first = await app.request("/checkout-sessions", {
    method: "POST",
    headers,
    body,
  });
  assert.equal(first.status, 201);

  // Same key + same body -> served from the idempotency record.
  const replay = await app.request("/checkout-sessions", {
    method: "POST",
    headers,
    body,
  });
  assert.equal(replay.status, 201);
  const replayed = (await replay.json()) as { ucp?: unknown };
  assertPaymentHandlers("idempotent replay", replayed.ucp);
});
