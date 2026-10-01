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

import {
  DiscoveryService,
  type DiscoveryCapability,
} from "../src/api/discovery";

type DiscoveryResponse = {
  ucp: {
    services: Record<string, Array<{ endpoint: string; transport: string }>>;
    capabilities: Record<string, Array<{ version: string }>>;
    keys?: unknown;
  };
  signing_keys?: unknown;
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
    "dev.ucp.shopping.fulfillment",
    "dev.ucp.shopping.order",
  ]);

  for (const [name, declarations] of Object.entries(body.ucp.capabilities)) {
    assert.ok(Array.isArray(declarations), `${name} must be an array`);
    assert.equal(declarations.length, 1);
    assert.equal(declarations[0]?.version, discoveryService.ucpVersion);
  }
});

test("merchant profile declares no capability without a schema at its own version", async () => {
  // dev.ucp.shopping.refund/.return/.dispute have no schema file under
  // source/schemas/shopping/ at 2026-04-08 (this server's declared version)
  // or at 2026-08-25, no route implements them, and neither reference
  // python samples server (upstream or our 08-25 golden reference) declares
  // them. A capability catalog entry with nothing behind it is not a real
  // capability.
  const app = new Hono();
  const discoveryService = new DiscoveryService();
  app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

  const response = await app.request("/.well-known/ucp");
  const body = (await response.json()) as DiscoveryResponse;

  for (const nonSpecCapability of [
    "dev.ucp.shopping.refund",
    "dev.ucp.shopping.return",
    "dev.ucp.shopping.dispute",
  ]) {
    assert.equal(
      body.ucp.capabilities[nonSpecCapability],
      undefined,
      `${nonSpecCapability} has no schema at any pin and must not be declared`
    );
  }
});

test("merchant profile publishes signing_keys[] at the top level, not ucp.keys[]", async () => {
  // source/discovery/profile_schema.json $defs/base at the 2026-04-08 pin
  // this server declares (config.ts UCP_VERSION) requires `ucp` and
  // separately declares `signing_keys` as a top-level sibling of `ucp`.
  // That schema defines no `keys` field, nested or otherwise.
  const app = new Hono();
  const discoveryService = new DiscoveryService();
  app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

  const response = await app.request("/.well-known/ucp");
  const body = (await response.json()) as DiscoveryResponse;

  assert.ok(
    Array.isArray(body.signing_keys) && body.signing_keys.length > 0,
    "signing_keys[] must be published at the top level"
  );
  assert.equal(
    body.ucp.keys,
    undefined,
    "ucp.keys[] has no basis in the 2026-04-08 schema and must not be published"
  );
});

test("DiscoveryCapability.extends accepts a multi-parent array", () => {
  // capability.json $defs/base at both the 2026-04-08 pin (this server's
  // declared version) and 2026-08-25: extends is oneOf [reverse_domain_name,
  // array<reverse_domain_name> minItems 1] -- "Use array for multi-parent
  // extensions." This is a compile-time check: if extends is typed as a
  // bare string, this literal fails tsc; the assertion below is the runtime
  // half so the test still reports as a test, not just a build step.
  const multiParent: DiscoveryCapability = {
    version: "2026-04-08",
    spec: "https://ucp.dev/2026-04-08/specification/shopping/discount",
    schema: "https://ucp.dev/2026-04-08/schemas/shopping/discount.json",
    extends: ["dev.ucp.shopping.checkout", "dev.ucp.shopping.cart"],
  };
  assert.deepEqual(multiParent.extends, [
    "dev.ucp.shopping.checkout",
    "dev.ucp.shopping.cart",
  ]);
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
