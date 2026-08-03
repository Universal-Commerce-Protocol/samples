import assert from "node:assert/strict";
import crypto from "node:crypto";
import http from "node:http";
import { after, afterEach, before, test } from "node:test";

import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";

import { CheckoutService } from "../src/api/checkout";
import { OrderService } from "../src/api/order";
import { getProductsDb, getTransactionsDb, initDbs } from "../src/data/db";
import { ExtendedCheckoutCreateRequestSchema } from "../src/models";
import { signatureConfig } from "../src/utils/config";
import {
  buildSignatureBase,
  clearKeyCache,
  contentDigest,
  jwkFromPublicKey,
  parseSignatureInput,
  signRequest,
  verifySignature,
} from "../src/utils/signature";
import { IdParamSchema, prettyValidation } from "../src/utils/validation";

// End-to-end twin of the Python server's signature_integration_test.py: the
// permissive default leaves unsigned clients untouched while still verifying
// real signatures, and enforcement returns the spec's error code for every
// failure mode. Signer keys are discovered from a localhost profile server via
// the UCP-Agent header, as in the official conformance harness topology.

const AUTHORITY = "merchant.test";
const ORIGIN = `http://${AUTHORITY}`;

type ErrorEnvelope = {
  detail: { status: string; errors: Array<{ code: string; message: string }> };
};

// A minimal app wired like src/index.ts (verifySignature ahead of validation)
// but without the pino middleware, following the lifecycle.test.ts convention.
function buildApp() {
  const checkoutService = new CheckoutService();
  const orderService = new OrderService();
  const app = new Hono<{ Variables: { logger: typeof console } }>();
  app.use(async (c, next) => {
    c.set("logger", quietLogger as unknown as typeof console);
    await next();
  });
  app.post(
    "/checkout-sessions",
    verifySignature,
    zValidator("json", ExtendedCheckoutCreateRequestSchema, prettyValidation),
    checkoutService.createCheckout
  );
  app.get(
    "/checkout-sessions/:id",
    verifySignature,
    zValidator("param", IdParamSchema, prettyValidation),
    checkoutService.getCheckout
  );
  app.get(
    "/orders/:id",
    verifySignature,
    zValidator("param", IdParamSchema, prettyValidation),
    orderService.getOrder
  );
  return app;
}

// Captures verification log lines so tests can assert on them, and keeps the
// validation hook's payload dumps out of the test output.
const logLines: string[] = [];
const quietLogger = {
  info: (msg: string) => logLines.push(String(msg)),
  warn: (msg: string) => logLines.push(String(msg)),
  debug: (msg: string) => logLines.push(String(msg)),
};

let app: ReturnType<typeof buildApp>;
let profileServer: http.Server;
let profileHits: string[] = [];
let profileUrl: string;
let keylessUrl: string;
let port: number;

const agentKeys = crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
const AGENT_KID = "test-agent-key";
const edKeys = crypto.generateKeyPairSync("ed25519");
const ED_KID = "test-agent-ed25519";

before(async () => {
  initDbs(":memory:", ":memory:");
  getProductsDb()
    .prepare(
      "INSERT INTO products (id, title, price, image_url) VALUES (?, ?, ?, ?)"
    )
    .run("bouquet_roses", "Red Rose", 3500, "");
  getTransactionsDb()
    .prepare("INSERT INTO inventory (product_id, quantity) VALUES (?, ?)")
    .run("bouquet_roses", 100);

  const agentJwk = jwkFromPublicKey(agentKeys.publicKey, AGENT_KID);
  const edJwk = jwkFromPublicKey(edKeys.publicKey, ED_KID);
  // A deliberately unsupported (RSA) JWK to exercise algorithm_unsupported.
  const rsaJwk = { kid: "rsa-key", kty: "RSA", n: "abc", e: "AQAB" };
  const good = JSON.stringify({
    ucp: { keys: [agentJwk, edJwk, rsaJwk] },
  });
  const keyless = JSON.stringify({ ucp: {} });

  profileServer = http.createServer((req, res) => {
    profileHits.push(req.url ?? "");
    const body = req.url === "/profile.json" ? good : keyless;
    if (req.url !== "/profile.json" && req.url !== "/keyless.json") {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, { "content-type": "application/json" }).end(body);
  });
  await new Promise<void>((resolve) =>
    profileServer.listen(0, "127.0.0.1", resolve)
  );
  const address = profileServer.address();
  port = typeof address === "object" && address ? address.port : 0;
  profileUrl = `http://127.0.0.1:${port}/profile.json`;
  keylessUrl = `http://127.0.0.1:${port}/keyless.json`;

  app = buildApp();
});

after(() => {
  profileServer.close();
});

afterEach(() => {
  signatureConfig.requireSignatures = false;
  signatureConfig.allowInsecureProfileUrls = false;
  clearKeyCache();
  logLines.length = 0;
  profileHits = [];
});

function enforce() {
  signatureConfig.requireSignatures = true;
  signatureConfig.allowInsecureProfileUrls = true;
}

function permissive() {
  signatureConfig.requireSignatures = false;
  signatureConfig.allowInsecureProfileUrls = true;
}

function checkoutBody(): string {
  return JSON.stringify({
    currency: "USD",
    line_items: [{ item: { id: "bouquet_roses" }, quantity: 1 }],
    payment: {},
  });
}

type SignedOptions = {
  key?: crypto.KeyObject;
  kid?: string;
  profile?: string;
  created?: number;
  coverUcpAgent?: boolean;
};

function signedHeaders(
  method: string,
  path: string,
  body: string,
  options: SignedOptions = {}
): Record<string, string> {
  const key = options.key ?? agentKeys.privateKey;
  const kid = options.kid ?? AGENT_KID;
  const profile = options.profile ?? profileUrl;
  const headers: Record<string, string> = {
    "UCP-Agent": `profile="${profile}"`,
    "Idempotency-Key": crypto.randomUUID(),
    "Request-Id": crypto.randomUUID(),
  };
  const signHeaders: Record<string, string> = { ...headers };
  if (options.coverUcpAgent === false) delete signHeaders["UCP-Agent"];
  const additions = signRequest(
    key,
    kid,
    method,
    `${ORIGIN}${path}`,
    signHeaders,
    Buffer.from(body),
    options.created
  );
  return { ...headers, ...additions };
}

async function postCheckout(headers: Record<string, string>, body: string) {
  return app.request(`${ORIGIN}/checkout-sessions`, {
    method: "POST",
    headers,
    body,
  });
}

async function assertError(
  response: Response,
  status: number,
  code: string
): Promise<void> {
  assert.equal(response.status, status, await response.clone().text());
  const envelope = (await response.json()) as ErrorEnvelope;
  assert.equal(envelope.detail.status, "error");
  assert.equal(envelope.detail.errors[0]?.code, code);
}

/* Permissive (default) mode: existing clients keep working. */

test("permissive: an unsigned request skips verification entirely", async () => {
  permissive();
  const body = checkoutBody();
  // The checkout handler itself fetches the profile for webhook resolution,
  // so a raw hit count cannot isolate the middleware; the skip branch (which
  // never fetches keys) is asserted through its log line instead.
  const response = await postCheckout(
    {
      "UCP-Agent": `profile="${profileUrl}"`,
      "request-signature": "test",
      "idempotency-key": crypto.randomUUID(),
      "request-id": "1",
      "content-type": "application/json",
    },
    body
  );
  assert.equal(response.status, 201, await response.clone().text());
  assert.ok(
    logLines.some((line) =>
      line.includes("No request signature present; skipping verification")
    ),
    logLines.join("\n")
  );
});

test("permissive: omitting Request-Signature entirely still succeeds", async () => {
  permissive();
  const response = await postCheckout(
    {
      "UCP-Agent": 'profile="https://agent.example/profile"',
      "idempotency-key": crypto.randomUUID(),
      "request-id": "1",
      "content-type": "application/json",
    },
    checkoutBody()
  );
  assert.equal(response.status, 201, await response.clone().text());
});

test("permissive: a signed request without profile= is allowed", async () => {
  permissive();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["UCP-Agent"] = 'version="2026-04-08"';
  const response = await postCheckout(headers, body);
  assert.equal(response.status, 201, await response.clone().text());
});

test("permissive: a valid signature is verified and logged", async () => {
  permissive();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  const response = await postCheckout(headers, body);
  assert.equal(response.status, 201, await response.clone().text());
  assert.ok(
    logLines.some((line) => line.includes("RFC 9421 signature verified")),
    logLines.join("\n")
  );
});

test("permissive: an invalid signature is allowed but warned about", async () => {
  permissive();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  const response = await postCheckout(headers, body + " ");
  assert.equal(response.status, 201, await response.clone().text());
  assert.ok(
    logLines.some((line) => line.includes("verification failed")),
    logLines.join("\n")
  );
});

/* Enforcement on: every failure mode returns its spec error code. */

test("enforced: a correctly signed request is accepted", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  const response = await postCheckout(headers, body);
  assert.equal(response.status, 201, await response.clone().text());
});

test("enforced: an Ed25519-signed request is accepted", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    key: edKeys.privateKey,
    kid: ED_KID,
  });
  const response = await postCheckout(headers, body);
  assert.equal(response.status, 201, await response.clone().text());
});

test("enforced: an unsigned request is rejected with signature_missing", async () => {
  enforce();
  const response = await postCheckout(
    {
      "UCP-Agent": `profile="${profileUrl}"`,
      "idempotency-key": crypto.randomUUID(),
      "request-id": "1",
      "content-type": "application/json",
    },
    checkoutBody()
  );
  await assertError(response, 401, "signature_missing");
});

test("enforced: an unsigned GET on the order route is rejected", async () => {
  enforce();
  const response = await app.request(`${ORIGIN}/orders/order_1`, {
    headers: { "UCP-Agent": `profile="${profileUrl}"` },
  });
  await assertError(response, 401, "signature_missing");
});

test("enforced: a signed GET on the checkout route verifies end to end", async () => {
  enforce();
  const headers = signedHeaders("GET", "/checkout-sessions/nonexistent", "");
  const response = await app.request(
    `${ORIGIN}/checkout-sessions/nonexistent`,
    {
      headers,
    }
  );
  // Verification passed; the 404 comes from the handler, not the signature.
  assert.equal(response.status, 404, await response.clone().text());
});

test("enforced: a signature without a profile= is signature_invalid", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["UCP-Agent"] = 'version="2026-04-08"';
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: a tampered body yields digest_mismatch", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  const response = await postCheckout(headers, body + " ");
  await assertError(response, 400, "digest_mismatch");
});

test("enforced: a garbage signature value yields signature_invalid", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["Signature"] = `sig1=:${crypto.randomBytes(64).toString("base64")}:`;
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: a signature from an unpublished key is signature_invalid", async () => {
  enforce();
  const other = crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    key: other.privateKey,
  });
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: a keyid not in the published set is key_not_found", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    kid: "nonexistent",
  });
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "key_not_found");
});

test("enforced: a DER-encoded signature on the wire is signature_invalid", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  // Re-sign the exact base as DER to violate the raw-r||s requirement.
  const parsed = parseSignatureInput(headers["Signature-Input"]!);
  assert.ok(parsed);
  const member = parsed["sig1"]!;
  const digest = contentDigest(Buffer.from(body));
  const values: Record<string, string> = {
    "@method": "POST",
    "@authority": AUTHORITY,
    "@path": "/checkout-sessions",
    "content-digest": digest,
    "content-type": "application/json",
    "idempotency-key": headers["Idempotency-Key"]!,
    "ucp-agent": headers["UCP-Agent"]!,
  };
  const base = buildSignatureBase(
    member.components,
    member.raw,
    (name) => values[name]
  );
  assert.ok(base);
  const der = crypto.sign("sha256", base, agentKeys.privateKey);
  headers["Signature"] = `sig1=:${der.toString("base64")}:`;
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: omitting a required covered component is signature_invalid", async () => {
  enforce();
  const body = checkoutBody();
  // Sign WITHOUT ucp-agent in the covered set, then send the header anyway.
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    coverUcpAgent: false,
  });
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: an alg parameter yields signature_invalid", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["Signature-Input"] = headers["Signature-Input"]!.replace(
    ";created",
    ';alg="ecdsa-p256-sha256";created'
  );
  const response = await postCheckout(headers, body);
  await assertError(response, 401, "signature_invalid");
});

test("enforced: a keyid selecting an RSA key is algorithm_unsupported", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["Signature-Input"] = headers["Signature-Input"]!.replace(
    `keyid="${AGENT_KID}"`,
    'keyid="rsa-key"'
  );
  const response = await postCheckout(headers, body);
  await assertError(response, 400, "algorithm_unsupported");
});

test("enforced: a dead profile port yields profile_unreachable", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    profile: "http://127.0.0.1:1/profile.json",
  });
  const response = await postCheckout(headers, body);
  await assertError(response, 424, "profile_unreachable");
});

test("enforced: a keyless profile yields profile_malformed", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body, {
    profile: keylessUrl,
  });
  const response = await postCheckout(headers, body);
  await assertError(response, 422, "profile_malformed");
});

test("enforced: an http profile URL without the carve-out is rejected", async () => {
  enforce();
  signatureConfig.allowInsecureProfileUrls = false;
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  const response = await postCheckout(headers, body);
  await assertError(response, 400, "invalid_profile_url");
});

test("enforced: one bad and one valid signature is accepted", async () => {
  enforce();
  const body = checkoutBody();
  const headers = signedHeaders("POST", "/checkout-sessions", body);
  headers["Signature-Input"] +=
    `, sig2=("@method");created=1;keyid="${AGENT_KID}"`;
  headers["Signature"] += ", sig2=:AAAA:";
  const response = await postCheckout(headers, body);
  assert.equal(response.status, 201, await response.clone().text());
});

test("enforced: created far in the past or future is still accepted", async () => {
  // The created parameter is OPTIONAL per signatures.md: replay protection is
  // handled at the business layer through idempotency keys, so no created
  // window is enforced -- mirroring the Python reference verifier.
  enforce();
  for (const skew of [-100_000, 100_000]) {
    const body = checkoutBody();
    const headers = signedHeaders("POST", "/checkout-sessions", body, {
      created: Math.floor(Date.now() / 1000) + skew,
    });
    const response = await postCheckout(headers, body);
    assert.equal(response.status, 201, await response.clone().text());
  }
});
