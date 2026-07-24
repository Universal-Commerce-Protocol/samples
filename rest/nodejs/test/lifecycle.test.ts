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
