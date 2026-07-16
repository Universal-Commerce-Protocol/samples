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
