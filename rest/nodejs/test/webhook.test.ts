import assert from "node:assert/strict";
import { test, before } from "node:test";

import { CheckoutService } from "../src/api/checkout";
import { initDbs, getTransactionsDb } from "../src/data/db";

// Per the UCP REST OpenAPI (source/services/shopping/rest.openapi.json), the
// orderEvent webhook's requestBody is `{ "$ref": "#/components/schemas/order" }`
// with `required: true` -- the delivered JSON body must BE the order object.
// The event type is carried out of band in the X-Event-Type header, and no
// notification may be sent when there is no order (the body must always be a
// valid order, never null/undefined or a custom envelope).

const WEBHOOK_URL = "https://platform.example/ucp-webhook";
const ORDER_ID = "order_wh_test";
const CHECKOUT_ID = "chk_wh_test";

// The eight top-level fields the order schema marks `required`, mirrored from
// the order the server itself builds when a checkout completes.
const ORDER_REQUIRED_FIELDS = [
  "ucp",
  "id",
  "checkout_id",
  "permalink_url",
  "line_items",
  "fulfillment",
  "currency",
  "totals",
] as const;

function seedOrder() {
  getTransactionsDb()
    .prepare("INSERT OR REPLACE INTO orders (id, data) VALUES (?, ?)")
    .run(
      ORDER_ID,
      JSON.stringify({
        ucp: { version: "2025-09-24" },
        id: ORDER_ID,
        checkout_id: CHECKOUT_ID,
        permalink_url: `http://localhost:8080/orders/${ORDER_ID}`,
        line_items: [
          {
            id: "li_1",
            item: { id: "bouquet_roses" },
            quantity: { total: 1, fulfilled: 0 },
            totals: [],
            status: "processing",
          },
        ],
        fulfillment: { expectations: [] },
        currency: "USD",
        totals: [{ type: "total", amount: 3500 }],
      })
    );
}

before(() => {
  initDbs(":memory:", ":memory:");
});

type CapturedRequest = {
  url: string;
  headers: Record<string, string>;
  body: unknown;
};

// Fire notifyWebhook with global fetch stubbed and return the captured POSTs,
// mirroring the delivered wire request exactly.
async function notifyAndCapture(
  checkout: unknown,
  eventType: string
): Promise<CapturedRequest[]> {
  const captured: CapturedRequest[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (
    url: string | URL | Request,
    init?: RequestInit
  ): Promise<Response> => {
    const headers = (init?.headers ?? {}) as Record<string, string>;
    const rawBody = init?.body;
    captured.push({
      url: String(url),
      headers,
      body: typeof rawBody === "string" ? JSON.parse(rawBody) : rawBody,
    });
    return new Response(null, { status: 200 });
  }) as typeof globalThis.fetch;

  try {
    await new CheckoutService()["notifyWebhook"](checkout as never, eventType);
  } finally {
    globalThis.fetch = originalFetch;
  }
  return captured;
}

test("webhook delivers the bare order object as the body", async () => {
  seedOrder();
  const checkout = {
    id: CHECKOUT_ID,
    platform: { webhook_url: WEBHOOK_URL },
    order: {
      id: ORDER_ID,
      permalink_url: `http://localhost:8080/orders/${ORDER_ID}`,
    },
  };

  const captured = await notifyAndCapture(checkout, "order_placed");

  assert.equal(captured.length, 1, "exactly one webhook must be delivered");
  const delivered = captured[0]!;
  assert.equal(delivered.url, WEBHOOK_URL);

  // The event type travels in the header, not the body.
  assert.equal(
    delivered.headers["X-Event-Type"],
    "order_placed",
    "event type must be carried in the X-Event-Type header"
  );

  const body = delivered.body as Record<string, unknown>;
  // The body IS the order: its own id, and every required field present.
  assert.equal(
    body.id,
    ORDER_ID,
    "body must be the order itself (top-level id)"
  );
  for (const field of ORDER_REQUIRED_FIELDS) {
    assert.ok(field in body, `order body missing required field '${field}'`);
  }

  // And it is NOT the old { event_type, checkout_id, order } envelope.
  assert.equal(
    body.event_type,
    undefined,
    "body must not carry an event_type key"
  );
  assert.equal(
    body.order,
    undefined,
    "body must not nest the order under 'order'"
  );
});

test("no webhook is delivered when there is no order", async () => {
  // A checkout with no order (e.g. created but not completed) must never post,
  // because the body must always be a valid order object.
  const checkout = {
    id: CHECKOUT_ID,
    platform: { webhook_url: WEBHOOK_URL },
    // no `order` field
  };

  const captured = await notifyAndCapture(checkout, "order_placed");

  assert.deepEqual(captured, [], "no webhook may be sent without an order");
});
