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
import { test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";
import * as z from "zod";

import { IdParamSchema, prettyValidation } from "../src/utils/validation";

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

test("logs the request payload when JSON validation fails", async () => {
  const logLines: string[] = [];
  const logger = {
    info: (message: string) => logLines.push(String(message)),
    warn: (message: string) => logLines.push(String(message)),
  } as unknown as typeof console;
  const app = new Hono<{ Variables: { logger: typeof console } }>();
  app.use(async (c, next) => {
    c.set("logger", logger);
    await next();
  });
  app.post(
    "/items",
    zValidator("json", z.object({ quantity: z.number() }), prettyValidation),
    (c) => c.text("created", 201)
  );

  const response = await app.request("/items", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ request_id: "invalid-payload-marker" }),
  });

  assert.equal(response.status, 422);
  const payloadLog = logLines.find((line) =>
    line.startsWith("Request payload:\n")
  );
  assert.match(payloadLog ?? "", /"request_id": "invalid-payload-marker"/);
  assert.notEqual(payloadLog, "Request payload:\n{}");
});
