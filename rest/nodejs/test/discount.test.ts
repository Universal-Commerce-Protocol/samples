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
import { test, before } from "node:test";

import { CheckoutService } from "../src/api/checkout";
import { initDbs, getProductsDb } from "../src/data/db";

// Seed an in-memory catalog once so recalculateTotals can resolve the product.
before(() => {
  initDbs(":memory:", ":memory:");
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run("bouquet_roses", "Red Rose", 3500, "");
});

function checkoutWithDiscount() {
  return {
    id: "chk_test",
    currency: "USD",
    line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
    discounts: { codes: ["10OFF"] },
    totals: [],
  } as never;
}

// Per discount.md, the applied[].amount is the magnitude (positive) while the
// totals[] entry is its signed effect on the receipt (negative for a discount);
// total.json constrains discount amounts with exclusiveMaximum: 0.
test("discount totals[] entry is negative and the receipt reconciles", () => {
  const checkout = checkoutWithDiscount();
  new CheckoutService()["recalculateTotals"](checkout);

  const totals: Array<{ type: string; amount: number }> = (
    checkout as unknown as { totals: Array<{ type: string; amount: number }> }
  ).totals;
  const by = (t: string) => totals.find((x) => x.type === t)!;

  assert.ok(
    by("discount").amount < 0,
    "discount totals[] entry must be negative"
  );
  assert.equal(
    by("subtotal").amount + by("discount").amount,
    by("total").amount,
    "subtotal plus the signed discount must equal the total"
  );
});

test("applied[].amount stays the positive magnitude", () => {
  const checkout = checkoutWithDiscount();
  new CheckoutService()["recalculateTotals"](checkout);

  const applied = (
    checkout as unknown as { discounts: { applied: Array<{ amount: number }> } }
  ).discounts.applied;
  assert.ok(
    applied.length > 0 && applied.every((a) => a.amount > 0),
    "applied[].amount is the positive magnitude, not the signed receipt effect"
  );
});

function checkoutWithCodes(codes: string[]) {
  return {
    id: "chk_test",
    currency: "USD",
    line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
    discounts: { codes },
    totals: [],
  } as never;
}

// Per discount.md a code is matched case-insensitively by the business.
test("a discount code matches case-insensitively", () => {
  const checkout = checkoutWithCodes(["10off"]);
  new CheckoutService()["recalculateTotals"](checkout);

  const applied = (checkout as unknown as { discounts: { applied: unknown[] } })
    .discounts.applied;
  assert.ok(
    applied.length > 0,
    "a lowercase '10off' must still match the '10OFF' code"
  );
});

// An empty codes[] clears all discounts (discount.md).
test("an empty codes[] removes all discounts", () => {
  const checkout = checkoutWithCodes([]);
  new CheckoutService()["recalculateTotals"](checkout);

  const c = checkout as unknown as {
    discounts: { applied: unknown[] };
    totals: Array<{ type: string }>;
  };
  assert.equal(
    c.discounts.applied.length,
    0,
    "an empty code set must produce no applied discounts"
  );
  assert.ok(
    !c.totals.some((t) => t.type === "discount"),
    "an empty code set must leave no discount entry in totals[]"
  );
});

// An applied discount's allocations must reconcile to its amount — a
// cross-field invariant the schema cannot express.
test("an applied discount's allocations sum to its amount", () => {
  const checkout = checkoutWithCodes(["10OFF"]);
  new CheckoutService()["recalculateTotals"](checkout);

  const applied = (
    checkout as unknown as {
      discounts: {
        applied: Array<{
          amount: number;
          allocations?: Array<{ amount: number }>;
        }>;
      };
    }
  ).discounts.applied;
  let checked = 0;
  for (const a of applied) {
    const allocs = a.allocations ?? [];
    if (allocs.length === 0) continue;
    checked += 1;
    assert.equal(
      allocs.reduce((sum, x) => sum + x.amount, 0),
      a.amount,
      "allocations must sum to the applied discount amount"
    );
  }
  assert.ok(checked > 0, "expected at least one discount carrying allocations");
});

// An allocation target must be expressed as a JSONPath (discount.json:
// allocation.path), so a platform can resolve where the discount applied —
// not a bare label like "subtotal".
test("an applied discount's allocation path is a JSONPath", () => {
  const checkout = checkoutWithCodes(["10OFF"]);
  new CheckoutService()["recalculateTotals"](checkout);

  const applied = (
    checkout as unknown as {
      discounts: {
        applied: Array<{
          allocations?: Array<{ path: string; amount: number }>;
        }>;
      };
    }
  ).discounts.applied;

  let checked = 0;
  for (const a of applied) {
    for (const alloc of a.allocations ?? []) {
      checked += 1;
      assert.ok(
        alloc.path.startsWith("$."),
        `allocation path "${alloc.path}" must be a JSONPath rooted at "$."`
      );
    }
  }
  assert.ok(checked > 0, "expected at least one allocation to check");
});
