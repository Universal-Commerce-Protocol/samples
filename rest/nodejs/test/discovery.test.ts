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

import { Hono } from "hono";

import { DiscoveryService } from "../src/api/discovery";

type DiscoveryResponse = {
  ucp: {
    services: Record<string, Array<{ endpoint: string; transport: string }>>;
    capabilities: Record<string, Array<{ version: string }>>;
  };
};

test("merchant profile uses schema-compliant discovery registries", async () => {
  const app = new Hono();
  const discoveryService = new DiscoveryService();
  app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

  const response = await app.request("/.well-known/ucp");
  const body = (await response.json()) as DiscoveryResponse;

  assert.equal(response.status, 200);

  const shoppingServices = body.ucp.services["dev.ucp.shopping"];
  assert.ok(Array.isArray(shoppingServices));
  assert.equal(shoppingServices.length, 1);
  assert.equal(shoppingServices[0]?.transport, "rest");
  assert.equal(shoppingServices[0]?.endpoint, "http://localhost");

  assert.equal(Array.isArray(body.ucp.capabilities), false);
  assert.deepEqual(Object.keys(body.ucp.capabilities).sort(), [
    "dev.ucp.shopping.buyer_consent",
    "dev.ucp.shopping.checkout",
    "dev.ucp.shopping.discount",
    "dev.ucp.shopping.dispute",
    "dev.ucp.shopping.fulfillment",
    "dev.ucp.shopping.order",
    "dev.ucp.shopping.refund",
    "dev.ucp.shopping.return",
  ]);

  for (const [name, declarations] of Object.entries(body.ucp.capabilities)) {
    assert.ok(Array.isArray(declarations), `${name} must be an array`);
    assert.equal(declarations.length, 1);
    assert.equal(declarations[0]?.version, discoveryService.ucpVersion);
  }
});

test("merchant profile derives the REST endpoint from the request origin", async () => {
  const app = new Hono();
  const discoveryService = new DiscoveryService();
  app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

  const response = await app.request(
    "https://merchant.example:8443/.well-known/ucp"
  );
  const body = (await response.json()) as DiscoveryResponse;

  assert.equal(response.status, 200);
  assert.equal(
    body.ucp.services["dev.ucp.shopping"]?.[0]?.endpoint,
    "https://merchant.example:8443"
  );
});
