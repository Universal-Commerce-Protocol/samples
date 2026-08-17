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
import {
  getOrder,
  getProductsDb,
  getTransactionsDb,
  initDbs,
} from "../src/data";
import {
  CheckoutCompleteRequestSchema,
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
} from "../src/models";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

// A minimal app wired with just the checkout routes (no request logging
// middleware, which needs the node-server request context), so the fulfillment
// flow can be exercised end to end through app.request() — the same convention
// as lifecycle.test.ts.
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

const JSON_HEADERS = { "Content-Type": "application/json" };

// The mock merchant only surfaces shipping destinations (and therefore shipping
// options) for the known customer john.doe@example.com; a shipping method that
// selects one of those seeded destinations is what makes the merchant quote
// options. See constructFulfillmentResponse / recalculateTotals in checkout.ts.
const KNOWN_BUYER = { email: "john.doe@example.com" };
const LINE_ITEMS = [{ item: { id: "bouquet_roses" }, quantity: 1 }];

const SUCCESS_PAYMENT = {
  payment: {
    instruments: [
      {
        id: "pi_1",
        handler_id: "mock_payment_handler",
        type: "card",
        brand: "visa",
        last_digits: "4242",
        // A non-"card" credential type routes to the mock token handler, so the
        // token drives the outcome (success_token).
        credential: { type: "network_token", token: "success_token" },
      },
    ],
  },
};

type Total = { type: string; amount: number };
type Option = { id: string; totals: Total[] };
type Group = {
  id: string;
  line_item_ids: string[];
  selected_option_id?: string;
  options?: Option[];
};
type Method = { groups?: Group[] };
type Checkout = {
  id: string;
  status: string;
  totals: Total[];
  order?: { id: string };
  fulfillment?: { methods?: Method[] };
};

// The "total" amount the option contributes to the receipt.
function optionTotal(option: Option): number {
  return option.totals.find((t) => t.type === "total")?.amount ?? 0;
}
function totalOfType(totals: Total[], type: string): Total | undefined {
  return totals.find((t) => t.type === type);
}

// Create a checkout that has selected a shipping destination (which is what
// prompts the merchant to quote fulfillment options), returning the parsed body.
async function createWithDestination(
  app: ReturnType<typeof buildApp>
): Promise<Checkout> {
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: LINE_ITEMS,
      payment: {},
      buyer: KNOWN_BUYER,
      fulfillment: {
        methods: [{ type: "shipping", selected_destination_id: "addr_1" }],
      },
    }),
  });
  assert.equal(res.status, 201);
  return (await res.json()) as Checkout;
}

// Select a fulfillment option on an existing method group via an update,
// echoing the server-assigned group id and line_item_ids as the update schema
// requires, returning the parsed body.
async function selectOption(
  app: ReturnType<typeof buildApp>,
  checkout: Checkout,
  optionId: string
): Promise<Response> {
  const group = checkout.fulfillment!.methods![0].groups![0];
  return app.request(`/checkout-sessions/${checkout.id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: [{ id: "line_1", ...LINE_ITEMS[0] }],
      buyer: KNOWN_BUYER,
      fulfillment: {
        methods: [
          {
            type: "shipping",
            selected_destination_id: "addr_1",
            groups: [
              {
                id: group.id,
                line_item_ids: group.line_item_ids,
                selected_option_id: optionId,
              },
            ],
          },
        ],
      },
    }),
  });
}

test("a created checkout with a selected destination is quoted fulfillment options", async () => {
  const app = buildApp();
  const created = await createWithDestination(app);

  const options = created.fulfillment?.methods?.[0]?.groups?.[0]?.options;
  assert.ok(
    Array.isArray(options) && options.length > 0,
    "a destination-bearing checkout must expose at least one fulfillment option"
  );
  assert.ok(
    options.every((o) => typeof o.id === "string" && o.id.length > 0),
    "every quoted fulfillment option must carry an id to select it by"
  );
  assert.ok(
    options.every((o) => totalOfType(o.totals, "total") !== undefined),
    "every quoted fulfillment option must carry a receipt total"
  );
});

test("selecting a fulfillment option is reflected and adds its cost to the receipt", async () => {
  const app = buildApp();
  const created = await createWithDestination(app);

  const options = created.fulfillment!.methods![0].groups![0].options!;
  // Pick a priced option so the assertion that the selection moves the receipt
  // is non-vacuous (the mock quotes a paid express option alongside a free one).
  const priced = options.find((o) => optionTotal(o) > 0);
  assert.ok(priced, "the merchant must quote at least one priced option");

  const subtotal = totalOfType(created.totals, "subtotal")!.amount;

  const res = await selectOption(app, created, priced.id);
  assert.equal(res.status, 200);
  const updated = (await res.json()) as Checkout;

  assert.equal(
    updated.fulfillment?.methods?.[0]?.groups?.[0]?.selected_option_id,
    priced.id,
    "the chosen option must be marked selected on the group"
  );

  const fulfillmentTotal = totalOfType(updated.totals, "fulfillment");
  assert.ok(
    fulfillmentTotal,
    "selecting an option must surface a fulfillment totals[] entry"
  );
  assert.equal(
    fulfillmentTotal.amount,
    optionTotal(priced),
    "the fulfillment totals[] entry must equal the selected option's cost"
  );
  assert.equal(
    subtotal + fulfillmentTotal.amount,
    totalOfType(updated.totals, "total")!.amount,
    "subtotal plus the selected fulfillment cost must equal the total"
  );
});

test("completing a checkout with no fulfillment selected is rejected", async () => {
  const app = buildApp();
  // A plain checkout carries no fulfillment selection at all.
  const created = (await (
    await app.request("/checkout-sessions", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify({
        currency: "USD",
        line_items: LINE_ITEMS,
        payment: {},
      }),
    })
  ).json()) as Checkout;

  const res = await app.request(`/checkout-sessions/${created.id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(SUCCESS_PAYMENT),
  });
  assert.equal(res.status, 400);
  const body = (await res.json()) as {
    messages?: Array<{ code?: string; content?: string }>;
  };
  assert.equal(body.messages?.[0]?.code, "INVALID_REQUEST");
  assert.match(body.messages?.[0]?.content ?? "", /fulfillment/i);
});

test("a checkout with fulfillment fully selected can be completed", async () => {
  const app = buildApp();
  const created = await createWithDestination(app);
  const options = created.fulfillment!.methods![0].groups![0].options!;

  const selectRes = await selectOption(app, created, options[0].id);
  assert.equal(selectRes.status, 200);

  const res = await app.request(`/checkout-sessions/${created.id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(SUCCESS_PAYMENT),
  });
  assert.equal(res.status, 200);
  const body = (await res.json()) as Checkout;
  assert.equal(body.status, "completed");
  assert.ok(body.order?.id, "completion must assign an order id");
});

test("shipping an order includes its line items in the fulfillment event", async () => {
  const app = buildApp();
  const created = await createWithDestination(app);
  const options = created.fulfillment!.methods![0].groups![0].options!;

  const selectRes = await selectOption(app, created, options[0].id);
  assert.equal(selectRes.status, 200);

  const completeRes = await app.request(
    `/checkout-sessions/${created.id}/complete`,
    {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(SUCCESS_PAYMENT),
    }
  );
  assert.equal(completeRes.status, 200);
  const completed = (await completeRes.json()) as Checkout;
  assert.ok(completed.order?.id, "completion must assign an order id");

  await new CheckoutService().shipOrder(
    completed.order.id,
    "http://localhost:3000"
  );

  const order = getOrder(completed.order.id);
  assert.ok(order, "completed order must be persisted");
  const event = order.fulfillment.events?.at(-1);
  assert.equal(event?.type, "shipped");
  assert.deepEqual(
    event?.line_items,
    order.line_items.map((lineItem) => ({
      id: lineItem.id,
      quantity: lineItem.quantity.total,
    }))
  );
});

test("empty fulfillment methods array blocks completion", async () => {
  const app = buildApp();
  // Distinct from "no fulfillment at all": the request carries an explicit
  // fulfillment object whose methods array is empty. The completion gate must
  // not treat [].every(...) === true as "all methods satisfied".
  const created = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: LINE_ITEMS,
      payment: {},
      buyer: KNOWN_BUYER,
      fulfillment: { methods: [] },
    }),
  });
  assert.equal(created.status, 201);
  const checkout = (await created.json()) as Checkout;
  assert.ok(
    Array.isArray(checkout.fulfillment?.methods) &&
      checkout.fulfillment!.methods!.length === 0,
    "the empty methods array is what makes the gate a vacuous truth"
  );

  const res = await app.request(`/checkout-sessions/${checkout.id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(SUCCESS_PAYMENT),
  });
  assert.equal(res.status, 400);
  const body = (await res.json()) as {
    messages?: Array<{ code?: string; content?: string }>;
  };
  assert.equal(body.messages?.[0]?.code, "INVALID_REQUEST");
  assert.match(body.messages?.[0]?.content ?? "", /fulfillment/i);
});

// fulfillment.md "Business Response Behavior" requires one group per method
// under the default supports_multi_group: false. Only shipping methods with a
// resolvable destination used to get one, so every other method came back with
// groups: [] — which then satisfied the completion gate via
// [].every(...) === true, letting a checkout complete with nothing selected.
//
// This mock merchant quotes options for shipping only, so a pickup method it
// cannot serve reports a group with no options and stays uncompletable. That
// is the point: refusing is correct, and silently completing was the bug.
// Quoting real pickup options would be a new merchant capability, not a fix.
test("a method the merchant cannot quote options for still gets one group", async () => {
  const app = buildApp();
  const created = await app.request("/checkout-sessions", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      currency: "USD",
      line_items: LINE_ITEMS,
      payment: {},
      buyer: KNOWN_BUYER,
      fulfillment: {
        methods: [{ type: "pickup", selected_destination_id: "addr_1" }],
      },
    }),
  });
  assert.equal(created.status, 201);
  const checkout = (await created.json()) as Checkout;
  const groups = checkout.fulfillment?.methods?.[0]?.groups;
  assert.equal(groups?.length, 1, "one group per method");
  assert.deepEqual(
    groups?.[0].options,
    [],
    "no options the merchant can quote"
  );

  // With no option selectable, completion must still be refused.
  const res = await app.request(`/checkout-sessions/${checkout.id}/complete`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(SUCCESS_PAYMENT),
  });
  assert.equal(res.status, 400);
  const body = (await res.json()) as {
    messages?: Array<{ code?: string; content?: string }>;
  };
  assert.equal(body.messages?.[0]?.code, "INVALID_REQUEST");
  assert.match(body.messages?.[0]?.content ?? "", /fulfillment/i);
});
