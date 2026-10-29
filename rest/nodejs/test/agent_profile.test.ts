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

// The order capability config of a platform carries the webhook URL the business
// delivers order events to (order.md, Webhook URL Configuration). The schema
// types it as a string with format uri (order.json, $defs/platform_schema),
// and the delivery path hands the stored value to new URL() and fetch(). A
// profile that publishes anything else must not be stored as the platform
// webhook target: it would be echoed on every response for that checkout and
// thrown on, or burned through retries, at delivery. This mirrors the
// Python reference, which drops a malformed profile value with a log line.

// A minimal app wired with just the checkout routes, the same convention as
// lifecycle.test.ts, so the agent profile path is exercised through
// app.request() with a real UCP-Agent header.
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

const VALID_WEBHOOK = "https://platform.example/ucp-webhook";
const CREATE_BODY = {
  currency: "USD",
  line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
  payment: {},
  buyer: { email: "john.doe@example.com" },
  fulfillment: {
    methods: [{ type: "shipping", selected_destination_id: "addr_1" }],
  },
};

// A platform profile whose order capability config carries `webhookUrl`,
// delivered as a data: URI so the server parses it without any network.
function agentHeader(webhookUrl: unknown): Record<string, string> {
  const profile = {
    ucp: {
      version: "2026-04-08",
      capabilities: {
        "dev.ucp.shopping.order": [
          {
            name: "dev.ucp.shopping.order",
            version: "2026-04-08",
            config: { webhook_url: webhookUrl },
          },
        ],
      },
    },
  };
  const encoded = Buffer.from(JSON.stringify(profile)).toString("base64");
  return {
    "Content-Type": "application/json",
    "UCP-Agent": `profile="data:application/json;base64,${encoded}"`,
  };
}

async function create(app: ReturnType<typeof buildApp>, webhookUrl: unknown) {
  const res = await app.request("/checkout-sessions", {
    method: "POST",
    headers: agentHeader(webhookUrl),
    body: JSON.stringify(CREATE_BODY),
  });
  const text = await res.text();
  assert.equal(res.status, 201, text);
  return JSON.parse(text) as {
    id: string;
    platform?: { webhook_url?: unknown };
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
}

// Runs fn with console.warn captured, restoring it afterwards. The drop must
// be loud: the log line is the only signal an operator gets that a platform
// published a value the business cannot deliver to.
async function captureWarnings<T>(
  fn: () => Promise<T>
): Promise<[T, unknown[][]]> {
  const warned: unknown[][] = [];
  const originalWarn = console.warn;
  console.warn = (...args: unknown[]) => {
    warned.push(args);
  };
  try {
    return [await fn(), warned];
  } finally {
    console.warn = originalWarn;
  }
}

test("a profile webhook_url that is a valid http(s) URL is stored and echoed", async () => {
  const app = buildApp();
  const created = await create(app, VALID_WEBHOOK);
  assert.deepEqual(created.platform, { webhook_url: VALID_WEBHOOK });
});

for (const [label, value] of [
  ["an ftp URL", "ftp://platform.invalid/hook"],
  ["an integer", 42],
  ["an object", { url: VALID_WEBHOOK }],
  ["a data: URL", "data:text/plain,ok"],
  ["a mailto: URL", "mailto:ops@platform.invalid"],
  ["a string that is not a URL", "xts-not-a-url-2030"],
  ["an array holding a valid URL", [VALID_WEBHOOK]],
] as const) {
  test(`a profile webhook_url that is ${label} is not stored or echoed`, async () => {
    const app = buildApp();
    const [created, warned] = await captureWarnings(() => create(app, value));
    assert.equal(
      created.platform,
      undefined,
      `platform must be absent, got ${JSON.stringify(created.platform)}`
    );
    assert.deepEqual(
      warned.filter(
        (args) => args[0] === "Ignoring malformed webhook_url in agent profile"
      ),
      [["Ignoring malformed webhook_url in agent profile", value]],
      "the dropped value must be logged once"
    );
    const fetched = await app.request(`/checkout-sessions/${created.id}`);
    assert.equal(fetched.status, 200);
    const body = (await fetched.json()) as { platform?: unknown };
    assert.equal(body.platform, undefined, "the value must not be persisted");
  });
}

test("an update whose profile webhook_url is malformed keeps the stored valid one", async () => {
  const app = buildApp();
  const created = await create(app, VALID_WEBHOOK);
  const res = await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: agentHeader("ftp://platform.invalid/hook"),
    body: JSON.stringify({
      currency: "USD",
      line_items: [
        { id: "line_1", item: { id: "bouquet_roses" }, quantity: 1 },
      ],
      buyer: { email: "john.doe@example.com" },
    }),
  });
  const text = await res.text();
  assert.equal(res.status, 200, text);
  const body = JSON.parse(text) as { platform?: { webhook_url?: unknown } };
  assert.deepEqual(body.platform, { webhook_url: VALID_WEBHOOK });
});

test("completing a checkout whose profile webhook_url is malformed attempts no delivery", async () => {
  const app = buildApp();
  const created = await create(app, "ftp://platform.invalid/hook");
  const group = created.fulfillment.methods[0]!.groups[0]!;
  const selected = await app.request(`/checkout-sessions/${created.id}`, {
    method: "PUT",
    headers: agentHeader("ftp://platform.invalid/hook"),
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
                selected_option_id: group.options[0]!.id,
              },
            ],
          },
        ],
      },
    }),
  });
  assert.equal(selected.status, 200, await selected.clone().text());

  const attempted: string[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request) => {
    attempted.push(String(url));
    return new Response(null, { status: 200 });
  }) as typeof globalThis.fetch;
  try {
    const res = await app.request(`/checkout-sessions/${created.id}/complete`, {
      method: "POST",
      headers: agentHeader("ftp://platform.invalid/hook"),
      body: JSON.stringify({
        payment: {
          instruments: [
            {
              id: "pi_1",
              handler_id: "mock_payment_handler",
              type: "card",
              brand: "visa",
              last_digits: "4242",
              credential: { type: "network_token", token: "success_token" },
            },
          ],
        },
      }),
    });
    const text = await res.text();
    assert.equal(res.status, 200, text);
    const body = JSON.parse(text) as { status: string };
    assert.equal(body.status, "completed");
  } finally {
    globalThis.fetch = originalFetch;
  }
  assert.deepEqual(
    attempted,
    [],
    "no webhook delivery may be attempted to a target that is not a URL"
  );
});
