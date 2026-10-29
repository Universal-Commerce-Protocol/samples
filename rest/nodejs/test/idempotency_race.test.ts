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

// Concurrent idempotency: one key raced against itself.
//
// createCheckout and updateCheckout read the record, await the agent profile,
// and then write. Requests sharing one Idempotency-Key that arrive while that
// fetch is in flight all find "no record" before any of them writes. The
// three race tests hold the profile fetch open until every racer has reached
// it, so the interleaving is reached on every run rather than by chance; the
// fourth plants a storage failure and sends no profile.

import assert from "node:assert/strict";
import { before, mock, test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import {
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
} from "../src/models";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

const RACERS = 8;

const PROFILE = {
  ucp: {
    version: "2026-04-08",
    capabilities: {
      "dev.ucp.shopping.order": [
        {
          name: "dev.ucp.shopping.order",
          config: { webhook_url: "https://agent.example/webhooks" },
        },
      ],
    },
  },
};

// The documented form of the header (overview/index.md, "UCP-Agent"): a
// profile URL the business fetches. Only this form awaits a network round
// trip inside the handler.
const AGENT_HEADERS = {
  "Content-Type": "application/json",
  "UCP-Agent": 'profile="https://agent.example/profiles/shopping-agent.json"',
};

function body(quantity: number) {
  return {
    currency: "USD",
    line_items: [{ item: { id: "bouquet_roses" }, quantity }],
    payment: {},
  };
}

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

// Replaces fetch with a profile server that answers only once `expected`
// callers are waiting on it. Every racer is then past its idempotency read
// before any racer can write. The timer is a backstop so that a change which
// stops some racers short of the fetch fails the test instead of hanging it.
function gateProfileFetch(expected: number) {
  let waiting = 0;
  let open!: () => void;
  const gate = new Promise<void>((resolve) => {
    open = resolve;
  });
  const backstop = setTimeout(open, 2000);
  mock.method(globalThis, "fetch", async () => {
    waiting += 1;
    if (waiting === expected) {
      clearTimeout(backstop);
      open();
    }
    await gate;
    return new Response(JSON.stringify(PROFILE), {
      headers: { "Content-Type": "application/json" },
    });
  });
}

function countCheckouts(): number {
  return (
    getTransactionsDb()
      .prepare("SELECT COUNT(*) AS n FROM checkouts")
      .get() as {
      n: number;
    }
  ).n;
}

function summary(responses: Response[]): string {
  const counts = new Map<number, number>();
  for (const r of responses)
    counts.set(r.status, (counts.get(r.status) ?? 0) + 1);
  return [...counts.entries()]
    .sort(([a], [b]) => a - b)
    .map(([status, n]) => `${n}x${status}`)
    .join(", ");
}

test("concurrent identical creates under one key persist one checkout", async (t) => {
  t.after(() => mock.restoreAll());
  const app = buildApp();
  gateProfileFetch(RACERS);
  const persisted = countCheckouts();

  const responses = await Promise.all(
    Array.from({ length: RACERS }, () =>
      app.request("/checkout-sessions", {
        method: "POST",
        headers: { ...AGENT_HEADERS, "Idempotency-Key": "race-create-same" },
        body: JSON.stringify(body(1)),
      })
    )
  );

  assert.equal(summary(responses), `${RACERS}x201`);
  const ids = new Set<string>();
  for (const r of responses) ids.add(((await r.json()) as { id: string }).id);
  assert.equal(
    ids.size,
    1,
    `identical retries must name ONE checkout; got ${ids.size}`
  );
  assert.equal(
    countCheckouts() - persisted,
    1,
    "only the winning request may persist a checkout"
  );
});

test("concurrent differing creates under one key admit exactly one", async (t) => {
  t.after(() => mock.restoreAll());
  const app = buildApp();
  gateProfileFetch(RACERS);
  const persisted = countCheckouts();

  const responses = await Promise.all(
    Array.from({ length: RACERS }, (_, i) =>
      app.request("/checkout-sessions", {
        method: "POST",
        headers: { ...AGENT_HEADERS, "Idempotency-Key": "race-create-differ" },
        body: JSON.stringify(body(i + 1)),
      })
    )
  );

  assert.equal(
    summary(responses),
    `1x201, ${RACERS - 1}x409`,
    "reusing a key with new parameters is a conflict, never a second checkout"
  );
  assert.equal(countCheckouts() - persisted, 1);
});

test("concurrent differing updates under one key admit exactly one", async (t) => {
  t.after(() => mock.restoreAll());
  const app = buildApp();
  const created = await app.request("/checkout-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body(1)),
  });
  assert.equal(created.status, 201);
  const { id } = (await created.json()) as { id: string };
  gateProfileFetch(RACERS);

  const responses = await Promise.all(
    Array.from({ length: RACERS }, (_, i) =>
      app.request(`/checkout-sessions/${id}`, {
        method: "PUT",
        headers: { ...AGENT_HEADERS, "Idempotency-Key": "race-update-differ" },
        body: JSON.stringify(body(i + 1)),
      })
    )
  );

  assert.equal(summary(responses), `1x200, ${RACERS - 1}x409`);
  const winner = responses.find((r) => r.status === 200)!;
  const winnerQty = (
    (await winner.json()) as { line_items: { quantity: number }[] }
  ).line_items[0].quantity;
  const stored = JSON.parse(
    (
      getTransactionsDb()
        .prepare("SELECT data FROM checkouts WHERE id = ?")
        .get(id) as { data: string }
    ).data
  ) as { line_items: { quantity: number }[] };
  assert.equal(
    stored.line_items[0].quantity,
    winnerQty,
    "the stored checkout must be the one the winner was told about"
  );
});

// The key is recorded before the checkout is stored, so the two writes must
// be one transaction: a key recorded for a checkout that was never stored
// would replay a 201 naming a checkout that does not exist, on every retry.
test("a key is never recorded for a checkout that was not stored", async (t) => {
  const app = buildApp();
  const db = getTransactionsDb();
  // Make the checkout write fail the way a full disk or a locked file would.
  db.exec(
    "CREATE TRIGGER planted_storage_failure BEFORE INSERT ON checkouts " +
      "BEGIN SELECT RAISE(ABORT, 'planted storage failure'); END"
  );
  t.after(() => db.exec("DROP TRIGGER IF EXISTS planted_storage_failure"));
  const headers = {
    "Content-Type": "application/json",
    "Idempotency-Key": "create-after-failed-write",
  };
  const failed = await app.request("/checkout-sessions", {
    method: "POST",
    headers,
    body: JSON.stringify(body(1)),
  });
  assert.equal(failed.status, 400);

  db.exec("DROP TRIGGER planted_storage_failure");
  const retried = await app.request("/checkout-sessions", {
    method: "POST",
    headers,
    body: JSON.stringify(body(1)),
  });
  assert.equal(retried.status, 201);
  const { id } = (await retried.json()) as { id: string };
  assert.ok(
    db.prepare("SELECT id FROM checkouts WHERE id = ?").get(id),
    "the retry must name a checkout that exists"
  );
});
