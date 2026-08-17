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

// Webhook signing and delivery retry, mirroring the Python reference server.
//
// order.md (Webhook Signature Verification): webhook payloads MUST be signed
// by the business; every delivery carries UCP-Agent (the business profile
// URL), Signature, Signature-Input, and a Content-Digest over the exact raw
// body bytes, verifiable against the key the business publishes in its
// profile's signing_keys[]. Failed deliveries MUST be retried; retried
// attempts reuse the same Webhook-Id and Idempotency-Key so receivers can
// deduplicate. No private-key files are committed; all key material is
// generated at runtime.

import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { before, test } from "node:test";
import { isDeepStrictEqual } from "node:util";

import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { DiscoveryService } from "../src/api/discovery";
import { initDbs, getTransactionsDb } from "../src/data/db";
import { webhookConfig } from "../src/utils/config";
import {
  SignatureError,
  contentDigestMatches,
  jwkFromPublicKey,
  parseSignatureInput,
  verifyRequest,
  type Jwk,
} from "../src/utils/signature";
import {
  publicJwk,
  resetSigner,
  signingKey,
} from "../src/utils/webhook_signer";

const BASE_URL = "http://testserver";
const WEBHOOK_URL = "https://platform.example/ucp-webhook";
const ORDER_ID = "order_whsig_test";
const CHECKOUT_ID = "chk_whsig_test";

before(() => {
  initDbs(":memory:", ":memory:");
});

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

type CapturedRequest = {
  url: string;
  headers: Record<string, string>;
  raw: Buffer;
};

// Fire notifyWebhook with global fetch stubbed and return the captured POSTs,
// capturing the exact raw wire bytes. `respond` optionally scripts the
// receiver, one entry per delivery attempt: a number becomes that HTTP
// status, an Error instance is thrown as a transport failure. Defaults to
// every attempt answering 200.
async function notifyAndCapture(
  webhookUrl: string,
  eventType: string,
  respond?: Array<number | Error>
): Promise<CapturedRequest[]> {
  seedOrder();
  const checkout = {
    id: CHECKOUT_ID,
    platform: { webhook_url: webhookUrl },
    order: {
      id: ORDER_ID,
      permalink_url: `http://localhost:8080/orders/${ORDER_ID}`,
    },
  };
  const captured: CapturedRequest[] = [];
  const responses = respond ? [...respond] : [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (
    url: string | URL | Request,
    init?: RequestInit
  ): Promise<Response> => {
    const body = init?.body;
    captured.push({
      url: String(url),
      headers: { ...((init?.headers ?? {}) as Record<string, string>) },
      raw:
        body instanceof Uint8Array
          ? Buffer.from(body)
          : Buffer.from(String(body ?? ""), "utf-8"),
    });
    const next = responses.length ? responses.shift()! : 200;
    if (next instanceof Error) throw next;
    return new Response(null, { status: next });
  }) as typeof globalThis.fetch;

  try {
    await new CheckoutService()["notifyWebhook"](
      checkout as never,
      eventType,
      BASE_URL
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
  return captured;
}

// Runs `fn` with webhookConfig overrides, always restoring the previous
// values (the config is module state, like the Python server's FLAGS).
async function withConfig<T>(
  overrides: Partial<typeof webhookConfig>,
  fn: () => Promise<T>
): Promise<T> {
  const saved = { ...webhookConfig };
  Object.assign(webhookConfig, overrides);
  try {
    return await fn();
  } finally {
    Object.assign(webhookConfig, saved);
  }
}

// Fetches the discovery profile the way a platform would.
async function fetchProfile(): Promise<Record<string, unknown>> {
  const app = new Hono();
  app.get("/.well-known/ucp", new DiscoveryService().getMerchantProfile);
  const response = await app.request("/.well-known/ucp");
  assert.equal(response.status, 200);
  return (await response.json()) as Record<string, unknown>;
}

function lowercased(headers: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(headers)) out[k.toLowerCase()] = v;
  return out;
}

// Serializes a private key as unencrypted PKCS#8 PEM into a temp file.
function pemFile(privateKey: crypto.KeyObject): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ucp-webhook-key-"));
  const file = path.join(dir, "key.pem");
  fs.writeFileSync(
    file,
    privateKey.export({ type: "pkcs8", format: "pem" }) as string
  );
  return file;
}

/* Delivery-side: every webhook is signed as this business. */

test("webhook delivery carries the signature headers", async () => {
  // order.md, Webhook Signature Verification: UCP-Agent (the business
  // profile URL), Signature, Signature-Input, and Content-Digest are
  // required headers on every delivery.
  const captured = await notifyAndCapture(WEBHOOK_URL, "order_placed");
  assert.equal(captured.length, 1);
  const headers = captured[0]!.headers;
  for (const name of [
    "UCP-Agent",
    "Signature",
    "Signature-Input",
    "Content-Digest",
  ]) {
    assert.ok(headers[name], `delivery is missing ${name}`);
  }
  // The UCP-Agent profile member is the business's own well-known URL
  // (signatures.md, UCP-Agent parsing rule 4 for business profiles).
  assert.equal(
    headers["UCP-Agent"],
    'profile="http://testserver/.well-known/ucp"'
  );
});

test("webhook signature verifies against the published key", async () => {
  // order.md, Verification (Platform): Content-Digest matches the SHA-256 of
  // the raw body, and the signature verifies against the key the business
  // publishes in its profile's signing_keys with the declared kid. This test
  // IS that platform: it reads the served profile and runs the server's own
  // verify path over the captured delivery.
  const captured = await notifyAndCapture(WEBHOOK_URL, "order_placed");
  assert.equal(captured.length, 1);
  const delivered = captured[0]!;
  const raw = delivered.raw;
  const headers = lowercased(delivered.headers);

  assert.ok(
    contentDigestMatches(headers["content-digest"]!, raw),
    "Content-Digest must cover the exact raw body bytes on the wire"
  );

  const profile = await fetchProfile();
  const keys = profile["signing_keys"] as Jwk[];
  assert.ok(
    Array.isArray(keys) && keys.length,
    "profile must publish signing_keys for verifiers"
  );

  const url = new URL(delivered.url);
  const keyid = verifyRequest(
    "POST",
    url.host,
    url.pathname,
    url.search.slice(1),
    headers,
    raw,
    keys
  );
  assert.equal(keyid, publicJwk().kid);

  // Kill direction: a tampered body must NOT verify.
  assert.throws(
    () =>
      verifyRequest(
        "POST",
        url.host,
        url.pathname,
        url.search.slice(1),
        headers,
        Buffer.concat([raw, Buffer.from(" ")]),
        keys
      ),
    SignatureError
  );
});

test("webhook signed components cover identity and event", async () => {
  // signatures.md, REST Request Signing: @method/@authority/@path always;
  // @query when the platform URL has one; content-digest/content-type for
  // the body; idempotency-key on a state-changing POST; ucp-agent when the
  // header is present. Webhook-Id, Webhook-Timestamp, and X-Event-Type are
  // additionally bound: every header this server adds to the delivery is
  // signed, so the event identity the platform dedupes and dispatches on
  // cannot be altered in transit.
  const captured = await notifyAndCapture(
    `${WEBHOOK_URL}?token=t1`,
    "order_placed"
  );
  assert.equal(captured.length, 1);
  const delivered = captured[0]!;
  // The delivery reaches the URL exactly as the platform provided it.
  assert.equal(delivered.url, `${WEBHOOK_URL}?token=t1`);
  const parsed = parseSignatureInput(delivered.headers["Signature-Input"]!);
  assert.ok(parsed);
  const components = new Set(Object.values(parsed)[0]!.components);
  for (const name of [
    "@method",
    "@authority",
    "@path",
    "@query",
    "content-digest",
    "content-type",
    "idempotency-key",
    "ucp-agent",
    "webhook-id",
    "webhook-timestamp",
    "x-event-type",
  ]) {
    assert.ok(components.has(name), `signature does not cover ${name}`);
  }
  // Every signed header component is actually present on the delivery.
  for (const name of [
    "Idempotency-Key",
    "Webhook-Id",
    "Webhook-Timestamp",
    "X-Event-Type",
  ]) {
    assert.ok(delivered.headers[name], `delivery is missing ${name}`);
  }
});

/* Retry: order.md, Guidelines (Business): MUST retry failed deliveries. */

test("webhook retries after a 5xx and succeeds", async () => {
  // The retry is the SAME event: Webhook-Id and Idempotency-Key are stable
  // across attempts so the platform can deduplicate, and every attempt is
  // signed.
  const captured = await notifyAndCapture(
    WEBHOOK_URL,
    "order_placed",
    [500, 200]
  );
  assert.equal(
    captured.length,
    2,
    "a failed delivery must be retried once it 5xxes"
  );
  const [first, second] = captured;
  assert.equal(first!.headers["Webhook-Id"], second!.headers["Webhook-Id"]);
  assert.equal(
    first!.headers["Idempotency-Key"],
    second!.headers["Idempotency-Key"]
  );
  for (const attempt of captured) {
    assert.ok(attempt.headers["Signature"], "every attempt must be signed");
    const body = JSON.parse(attempt.raw.toString("utf-8")) as { id: string };
    assert.equal(body.id, ORDER_ID);
  }
});

test("a malformed webhook URL never throws into the order flow", async () => {
  // The webhook URL is platform-controlled data. A value the signer or the
  // transport cannot handle must degrade to a logged delivery failure, not an
  // exception in completeCheckout after the order is already placed.
  const captured = await notifyAndCapture("::not-a-url::", "order_placed");
  assert.equal(
    captured.length,
    0,
    "an unusable URL cannot produce a delivery, only a logged failure"
  );
});

test("each retry attempt is re-signed with a fresh created timestamp", async () => {
  // Each delivery attempt is its own signing operation: the signature's
  // `created` parameter reflects the actual send time of that attempt, not
  // the time of the first one. Deterministic via a stubbed clock that
  // advances by more than a second per reading; a signature hoisted out of
  // the retry loop would carry the same `created` on both attempts.
  const realNow = Date.now;
  let tick = 1_700_000_000_000;
  Date.now = () => {
    tick += 2_000;
    return tick;
  };
  try {
    const captured = await notifyAndCapture(
      WEBHOOK_URL,
      "order_placed",
      [500, 200]
    );
    assert.equal(captured.length, 2);
    const createdOf = (attempt: CapturedRequest): number => {
      const parsed = parseSignatureInput(attempt.headers["Signature-Input"]!);
      assert.ok(parsed);
      const created = Object.values(parsed)[0]!.params["created"];
      assert.ok(created, "signature must declare a created parameter");
      return Number(created);
    };
    const first = createdOf(captured[0]!);
    const second = createdOf(captured[1]!);
    assert.ok(
      second > first,
      `the retry must be freshly signed (created ${second} vs ${first})`
    );
  } finally {
    Date.now = realNow;
  }
});

test("the default identity is an ephemeral P-256 singleton", async () => {
  await withConfig({ signingKeyPath: undefined }, async () => {
    resetSigner();
    try {
      const first = signingKey();
      const second = signingKey();
      assert.equal(first.privateKey.asymmetricKeyType, "ec");
      assert.equal(first.privateKey, second.privateKey);
      assert.equal(first.kid, second.kid);
      assert.ok(first.kid.length > 0);
    } finally {
      resetSigner();
    }
  });
});

test("the public JWK matches the signing key and its RFC 7638 kid", async () => {
  await withConfig({ signingKeyPath: undefined }, async () => {
    resetSigner();
    try {
      const { privateKey, kid } = signingKey();
      const jwk = publicJwk();
      assert.equal(jwk.kid, kid);
      assert.equal(jwk.kty, "EC");
      assert.equal(jwk.crv, "P-256");
      const expected = jwkFromPublicKey(
        crypto.createPublicKey(privateKey),
        kid
      );
      assert.deepEqual(jwk, expected);
      // Independent RFC 7638 oracle: canonical JSON of the REQUIRED public
      // members in lexicographic order, SHA-256, base64url without padding.
      const canonical = `{"crv":"${jwk.crv}","kty":"${jwk.kty}","x":"${jwk.x}","y":"${jwk.y}"}`;
      const thumbprint = crypto
        .createHash("sha256")
        .update(canonical, "utf-8")
        .digest("base64url");
      assert.equal(kid, thumbprint);
    } finally {
      resetSigner();
    }
  });
});

test("WEBHOOK_SIGNING_KEY loads an operator P-256 PEM key", async () => {
  const provided = crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
  const file = pemFile(provided.privateKey);
  try {
    await withConfig({ signingKeyPath: file }, async () => {
      resetSigner();
      try {
        const { kid } = signingKey();
        const jwk = publicJwk();
        const expected = jwkFromPublicKey(provided.publicKey, kid);
        assert.deepEqual(jwk, expected);
      } finally {
        resetSigner();
      }
    });
  } finally {
    fs.rmSync(path.dirname(file), { recursive: true, force: true });
  }
});

test("WEBHOOK_SIGNING_KEY loads an Ed25519 PEM key; the JWK is OKP", async () => {
  const provided = crypto.generateKeyPairSync("ed25519");
  const file = pemFile(provided.privateKey);
  try {
    await withConfig({ signingKeyPath: file }, async () => {
      resetSigner();
      try {
        const { privateKey } = signingKey();
        assert.equal(privateKey.asymmetricKeyType, "ed25519");
        assert.equal(publicJwk().kty, "OKP");
      } finally {
        resetSigner();
      }
    });
  } finally {
    fs.rmSync(path.dirname(file), { recursive: true, force: true });
  }
});

test("the kid is deterministic for a given key", async () => {
  // The kid is the RFC 7638 JWK thumbprint: reloading the same PEM must
  // republish the same kid, so platforms that cache the profile keep
  // resolving the key after a server restart.
  const provided = crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
  const file = pemFile(provided.privateKey);
  try {
    await withConfig({ signingKeyPath: file }, async () => {
      resetSigner();
      try {
        const first = signingKey().kid;
        resetSigner();
        const second = signingKey().kid;
        assert.equal(first, second);
      } finally {
        resetSigner();
      }
    });
  } finally {
    fs.rmSync(path.dirname(file), { recursive: true, force: true });
  }
});

test("an unreadable key file fails loudly", async () => {
  // A bad key path is a configuration error, never a silent fallback: the
  // operator asked for a specific signing identity, and silently generating
  // an ephemeral key instead would sign as a different identity than the
  // one configured. src/index.ts loads the key at boot so this failure
  // aborts startup, not individual deliveries.
  await withConfig({ signingKeyPath: "/nonexistent/key.pem" }, async () => {
    resetSigner();
    try {
      assert.throws(() => signingKey());
    } finally {
      resetSigner();
    }
  });
});

test("an unsupported key type is rejected with a clear message", async () => {
  const wrongCurve = crypto.generateKeyPairSync("ec", {
    namedCurve: "secp384r1",
  });
  const file = pemFile(wrongCurve.privateKey);
  try {
    await withConfig({ signingKeyPath: file }, async () => {
      resetSigner();
      try {
        assert.throws(() => signingKey(), /EC P-256 \(ES256\) or Ed25519/);
      } finally {
        resetSigner();
      }
    });
  } finally {
    fs.rmSync(path.dirname(file), { recursive: true, force: true });
  }
});

/* Key discovery: the profile publishes the webhook public key. */

test("the profile publishes the webhook signing key", async () => {
  // signatures.md, Key Discovery: public keys live in the profile's
  // signing_keys[] (a top-level sibling of `ucp` per the discovery profile
  // schema). It is also mirrored into ucp.keys[], the JWK Set this server's
  // own verifier resolves.
  const profile = await fetchProfile();
  const jwk = publicJwk();
  const signingKeys = profile["signing_keys"] as Jwk[];
  assert.ok(
    Array.isArray(signingKeys) &&
      signingKeys.some((k) => isDeepStrictEqual(k, jwk)),
    "signing_keys[] must carry the webhook public JWK"
  );
  const ucp = profile["ucp"] as { keys?: Jwk[] };
  assert.ok(
    Array.isArray(ucp.keys) && ucp.keys.some((k) => isDeepStrictEqual(k, jwk)),
    "ucp.keys[] must mirror the webhook public JWK"
  );
});
