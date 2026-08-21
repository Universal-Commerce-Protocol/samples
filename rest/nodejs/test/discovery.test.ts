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

type DiscoveryDeclaration = {
  version: string;
  spec: string;
  schema: string;
};

type DiscoveryResponse = {
  ucp: {
    services: Record<
      string,
      Array<DiscoveryDeclaration & { endpoint: string; transport: string }>
    >;
    capabilities: Record<string, DiscoveryDeclaration[]>;
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
  assert.equal(
    shoppingServices[0]?.spec,
    `https://ucp.dev/${discoveryService.ucpVersion}/specification/overview`
  );
  assert.equal(
    shoppingServices[0]?.schema,
    `https://ucp.dev/${discoveryService.ucpVersion}/services/shopping/rest.openapi.json`
  );

  assert.equal(Array.isArray(body.ucp.capabilities), false);
  assert.deepEqual(Object.keys(body.ucp.capabilities).sort(), [
    "dev.ucp.shopping.buyer_consent",
    "dev.ucp.shopping.checkout",
    "dev.ucp.shopping.discount",
    "dev.ucp.shopping.fulfillment",
    "dev.ucp.shopping.order",
  ]);

  const specSlugs: Record<string, string> = {
    "dev.ucp.shopping.buyer_consent": "buyer-consent",
    "dev.ucp.shopping.checkout": "checkout",
    "dev.ucp.shopping.discount": "discount",
    "dev.ucp.shopping.fulfillment": "fulfillment",
    "dev.ucp.shopping.order": "order",
  };
  for (const [name, declarations] of Object.entries(body.ucp.capabilities)) {
    assert.ok(Array.isArray(declarations), `${name} must be an array`);
    assert.equal(declarations.length, 1);
    assert.equal(declarations[0]?.version, discoveryService.ucpVersion);
    assert.equal(
      declarations[0]?.spec,
      `https://ucp.dev/${discoveryService.ucpVersion}/specification/${specSlugs[name]}`
    );
    assert.equal(
      declarations[0]?.schema,
      `https://ucp.dev/${discoveryService.ucpVersion}/schemas/shopping/${name.split(".").at(-1)}.json`
    );
  }
});

test("merchant profile sends a public, cacheable Cache-Control header", async () => {
  // overview.md (Discovery) MUST: "Profile responses MUST include a
  // Cache-Control header with `public` and `max-age` of at least 60 seconds.
  // Profiles MUST NOT be served with `private`, `no-store`, or `no-cache`
  // directives." (docs/specification/overview.md, "Profiles MUST" list).
  const app = new Hono();
  const discoveryService = new DiscoveryService();
  app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

  const response = await app.request("/.well-known/ucp");
  assert.equal(response.status, 200);

  const cacheControl = response.headers.get("Cache-Control");
  assert.ok(cacheControl, "profile response must carry a Cache-Control header");

  const directives = cacheControl.split(",").map((d) => d.trim().toLowerCase());
  assert.ok(
    directives.includes("public"),
    `Cache-Control must be public, got "${cacheControl}"`
  );
  for (const forbidden of ["private", "no-store", "no-cache"]) {
    assert.equal(
      directives.includes(forbidden),
      false,
      `Cache-Control must not include "${forbidden}", got "${cacheControl}"`
    );
  }

  const maxAge = directives
    .map((d) => /^max-age=(\d+)$/.exec(d))
    .find((m) => m !== null);
  assert.ok(maxAge, `Cache-Control must set max-age, got "${cacheControl}"`);
  assert.ok(
    Number(maxAge[1]) >= 60,
    `Cache-Control max-age must be at least 60, got "${cacheControl}"`
  );
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
