import assert from "node:assert/strict";
import { test } from "node:test";

import { IdParamSchema } from "../src/utils/validation";

test("accepts a required route ID", () => {
  const result = IdParamSchema.safeParse({ id: "item-123" });

  assert.equal(result.success, true);
  if (result.success) {
    assert.equal(result.data.id, "item-123");
  }
});

test("rejects a missing route ID", () => {
  const result = IdParamSchema.safeParse({});

  assert.equal(result.success, false);
});
