import assert from "node:assert/strict";
import crypto from "node:crypto";
import http from "node:http";
import { after, before, test } from "node:test";

import {
  SignatureError,
  assertProfileUrlAllowed,
  buildSignatureBase,
  clearKeyCache,
  contentDigest,
  contentDigestMatches,
  extractKeys,
  fetchSigningKeys,
  jwkFromPublicKey,
  normalizeAuthority,
  parseSignature,
  parseSignatureInput,
  requiredComponents,
  sfSplit,
  signRequest,
  verifyRawSignature,
  verifyRequest,
} from "../src/utils/signature";

// RFC 9421 Appendix B.1.4 test-key-ed25519 (JWK coordinates, verbatim).
const RFC_ED25519_JWK = {
  kty: "OKP",
  crv: "Ed25519",
  kid: "test-key-ed25519",
  x: "JrQLj5P_89iXES9-vFgrIy29clF9CC_oPPsw3c5D0bs",
};
const RFC_ED25519_D = "n4Ni-HpISpVObnQMW0wOhCKROaIKqKtW_2ZYb2p9KcU";

// RFC 9421 Appendix B.2.6 signature base and signature (byte-exact oracle).
const RFC_B26_BASE = Buffer.from(
  [
    '"date": Tue, 20 Apr 2021 02:07:55 GMT',
    '"@method": POST',
    '"@path": /foo',
    '"@authority": example.com',
    '"content-type": application/json',
    '"content-length": 18',
    '"@signature-params": ("date" "@method" "@path" "@authority" ' +
      '"content-type" "content-length");created=1618884473' +
      ';keyid="test-key-ed25519"',
  ].join("\n")
);
const RFC_B26_SIGNATURE = Buffer.from(
  "wqcAqbmYJ2ji2glfAMaRy4gruYYnx2nEFN2HN6jrnDnQCK1u02Gb04v9EDgwUPiu4" +
    "A0w6vuQv5lIp5WPpBKRCw==",
  "base64"
);

function es256KeyPair() {
  return crypto.generateKeyPairSync("ec", { namedCurve: "P-256" });
}

function ed25519KeyPair() {
  return crypto.generateKeyPairSync("ed25519");
}

function assertSignatureError(fn: () => unknown, code: string) {
  try {
    fn();
  } catch (e) {
    assert.ok(e instanceof SignatureError, `expected SignatureError, got ${e}`);
    assert.equal(e.code, code);
    return e;
  }
  assert.fail(`expected SignatureError(${code}), nothing thrown`);
}

async function assertSignatureErrorAsync(
  fn: () => Promise<unknown>,
  code: string
) {
  try {
    await fn();
  } catch (e) {
    assert.ok(e instanceof SignatureError, `expected SignatureError, got ${e}`);
    assert.equal(e.code, code);
    return e;
  }
  assert.fail(`expected SignatureError(${code}), nothing thrown`);
}

/* RFC 9530 Content-Digest generation and matching. */

test("content digest matches the RFC 9530 LF body vector", () => {
  assert.equal(
    contentDigest(Buffer.from('{"hello": "world"}\n')),
    "sha-256=:RK/0qy18MlBSVnWgjwz6lZEWjP/lF5HF9bvEF8FabDg=:"
  );
});

test("content digest matches the RFC 9421 no-LF body vector", () => {
  assert.equal(
    contentDigest(Buffer.from('{"hello": "world"}')),
    "sha-256=:X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=:"
  );
});

test("content digest matching accepts the right body and rejects others", () => {
  const body = Buffer.from('{"a": 1}');
  const header = contentDigest(body);
  assert.equal(contentDigestMatches(header, body), true);
  assert.equal(contentDigestMatches(header, Buffer.from('{"a": 2}')), false);
});

test("content digest matching rejects malformed header forms", () => {
  const body = Buffer.from("x");
  assert.equal(contentDigestMatches("sha-256=abc", body), false);
  assert.equal(contentDigestMatches("sha-256=:@@@:", body), false);
  assert.equal(contentDigestMatches("md5=:AA==:", body), false);
});

test("unpadded base64 is malformed, matching the Python verifier", () => {
  // Python parses with base64.b64decode(validate=True), which raises on
  // incorrect padding; both references must agree on the same wire bytes.
  const body = Buffer.from("x");
  const digest = crypto.createHash("sha256").update(body).digest("base64");
  const unpadded = digest.replace(/=+$/, "");
  if (unpadded !== digest) {
    assert.equal(contentDigestMatches(`sha-256=:${unpadded}:`, body), false);
  }
  assert.equal(parseSignature("sig1=:QUJDRA:"), null);
  assert.equal(parseSignature("sig1=:A:"), null);
});

/* RFC 9421 signature-base construction. */

test("signature base reconstructs the RFC B.2.6 bytes exactly", () => {
  const components = [
    "date",
    "@method",
    "@path",
    "@authority",
    "content-type",
    "content-length",
  ];
  const raw =
    '("date" "@method" "@path" "@authority" "content-type" ' +
    '"content-length");created=1618884473;keyid="test-key-ed25519"';
  const values: Record<string, string> = {
    date: "Tue, 20 Apr 2021 02:07:55 GMT",
    "@method": "POST",
    "@path": "/foo",
    "@authority": "example.com",
    "content-type": "application/json",
    "content-length": "18",
  };
  const base = buildSignatureBase(components, raw, (name) => values[name]);
  assert.ok(base);
  assert.deepEqual(base, RFC_B26_BASE);
});

test("signature base echoes @signature-params verbatim", () => {
  const raw = '("@method");created=5;keyid="k"';
  const base = buildSignatureBase(["@method"], raw, () => "GET");
  assert.ok(base);
  assert.ok(base.toString().endsWith(`"@signature-params": ${raw}`));
});

test("signature base aborts on an unresolvable component", () => {
  assert.equal(
    buildSignatureBase(["x-missing"], "()", () => undefined),
    null
  );
});

/* Byte-exact Ed25519 and verify-direction ES256 against Appendix B. */

test("the RFC published Ed25519 signature verifies", () => {
  verifyRawSignature(RFC_ED25519_JWK, RFC_B26_BASE, RFC_B26_SIGNATURE);
});

test("Ed25519: signRequest accepts the key; the primitive matches the RFC vector", () => {
  const key = crypto.createPrivateKey({
    key: { ...RFC_ED25519_JWK, d: RFC_ED25519_D },
    format: "jwk",
  });
  const additions = signRequest(
    key,
    "test-key-ed25519",
    "GET",
    "https://example.com/",
    {},
    Buffer.alloc(0)
  );
  assert.ok(additions["Signature"]);
  // Determinism check via a direct signature over the RFC base: Ed25519 has no
  // nonce, so the signature must equal the RFC bytes.
  const sig = crypto.sign(null, RFC_B26_BASE, key);
  assert.deepEqual(sig, RFC_B26_SIGNATURE);
});

test("a tampered base no longer verifies against the RFC signature", () => {
  assertSignatureError(
    () =>
      verifyRawSignature(
        RFC_ED25519_JWK,
        Buffer.concat([RFC_B26_BASE, Buffer.from(" ")]),
        RFC_B26_SIGNATURE
      ),
    "signature_invalid"
  );
});

test("an ES256 signature we produce verifies with the derived JWK", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k");
  const additions = signRequest(
    privateKey,
    "k",
    "GET",
    "https://m.example/p",
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"],
    signature: additions["Signature"],
  };
  const keyid = verifyRequest(
    "GET",
    "m.example",
    "/p",
    "",
    headers,
    Buffer.alloc(0),
    [jwk]
  );
  assert.equal(keyid, "k");
});

test("an Ed25519-signed request verifies through the full verifyRequest", () => {
  const { publicKey, privateKey } = ed25519KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "ed-k");
  const additions = signRequest(
    privateKey,
    "ed-k",
    "GET",
    "https://m.example/p",
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"],
    signature: additions["Signature"],
  };
  const keyid = verifyRequest(
    "GET",
    "m.example",
    "/p",
    "",
    headers,
    Buffer.alloc(0),
    [jwk]
  );
  assert.equal(keyid, "ed-k");
});

/* The UCP raw-r||s ECDSA requirement (spec MUST). */

test("a DER-encoded ECDSA signature is rejected as non-conformant", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k");
  const der = crypto.sign("sha256", RFC_B26_BASE, privateKey);
  assertSignatureError(
    () => verifyRawSignature(jwk, RFC_B26_BASE, der),
    "signature_invalid"
  );
});

test("a well-formed 64-byte raw signature verifies", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k");
  const sig = crypto.sign("sha256", RFC_B26_BASE, {
    key: privateKey,
    dsaEncoding: "ieee-p1363",
  });
  assert.equal(sig.length, 64);
  verifyRawSignature(jwk, RFC_B26_BASE, sig);
});

test("signatures that are not 64 bytes are rejected before verification", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k");
  const sig = crypto.sign("sha256", RFC_B26_BASE, {
    key: privateKey,
    dsaEncoding: "ieee-p1363",
  });
  for (const bad of [
    sig.subarray(0, sig.length - 1),
    Buffer.concat([sig, Buffer.from([0])]),
  ]) {
    assertSignatureError(
      () => verifyRawSignature(jwk, RFC_B26_BASE, bad),
      "signature_invalid"
    );
  }
});

/* RFC 8941 subset parsing of Signature-Input and Signature. */

test("a well-formed member yields components and parameters", () => {
  const parsed = parseSignatureInput(
    'sig1=("@method" "content-digest");created=1;keyid="abc"'
  );
  assert.ok(parsed);
  assert.deepEqual(parsed["sig1"]?.components, ["@method", "content-digest"]);
  assert.equal(parsed["sig1"]?.params["keyid"], "abc");
});

test("multiple comma-separated members are all parsed", () => {
  const parsed = parseSignatureInput(
    'a=("@method");keyid="x", b=("@path");keyid="y"'
  );
  assert.ok(parsed);
  assert.deepEqual(Object.keys(parsed).sort(), ["a", "b"]);
});

test("a Signature member decodes to raw bytes", () => {
  const raw = Buffer.from("hello").toString("base64");
  const parsed = parseSignature(`sig1=:${raw}:`);
  assert.ok(parsed);
  assert.deepEqual(parsed["sig1"], Buffer.from("hello"));
});

test("malformed inputs parse to null rather than throwing", () => {
  assert.equal(parseSignatureInput("not a signature input"), null);
  assert.equal(parseSignature(""), null);
  assert.equal(parseSignatureInput("sig1"), null);
  assert.equal(parseSignatureInput("sig1=(@method)"), null);
  assert.equal(parseSignature("sig1"), null);
  assert.equal(parseSignature("sig1=abc"), null);
  assert.equal(parseSignature("sig1=:@@@:"), null);
  assert.equal(parseSignatureInput(""), null);
});

test("the splitter honours backslash escapes inside quoted strings", () => {
  const parts = sfSplit(String.raw`"a\"b,c" , "d"`, ",");
  assert.deepEqual(parts, [String.raw`"a\"b,c"`, '"d"']);
});

test("a trailing separator does not emit an empty final segment", () => {
  assert.deepEqual(sfSplit("a,", ","), ["a"]);
  assert.deepEqual(sfSplit("", ","), []);
});

test("nested and unbalanced parens degrade safely", () => {
  const parsed = parseSignatureInput('sig1=("@method" "@path");created=1');
  assert.ok(parsed);
  assert.deepEqual(parsed["sig1"]?.components, ["@method", "@path"]);
  const embedded = parseSignatureInput('sig1=("a(b" "c");created=1');
  assert.ok(embedded === null || embedded["sig1"]?.components.length === 0);
  const unclosed = parseSignatureInput('sig1=("a";created=1');
  assert.ok(unclosed === null || unclosed["sig1"]?.components.length === 0);
});

/* The UCP required-component coverage table. */

test("a bodyless GET requires only the target components", () => {
  assert.deepEqual(requiredComponents("GET", false, {}, false), [
    "@method",
    "@authority",
    "@path",
  ]);
});

test("a bodied request must cover content-digest and content-type", () => {
  const required = requiredComponents("POST", false, {}, true);
  assert.ok(required.includes("content-digest"));
  assert.ok(required.includes("content-type"));
});

test("a query string adds @query", () => {
  assert.ok(requiredComponents("GET", true, {}, false).includes("@query"));
});

test("coverage keys on header presence, not on the method", () => {
  const required = requiredComponents(
    "GET",
    false,
    { "idempotency-key": "x" },
    false
  );
  assert.ok(required.includes("idempotency-key"));
});

test("ucp-agent must be covered; signature-agent is out of scope", () => {
  const required = requiredComponents(
    "GET",
    false,
    { "ucp-agent": "a", "signature-agent": "b" },
    false
  );
  assert.ok(required.includes("ucp-agent"));
  assert.ok(!required.includes("signature-agent"));
});

test("a signature carrying an alg parameter is rejected (spec MUST NOT)", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k");
  const additions = signRequest(
    privateKey,
    "k",
    "GET",
    "https://h/p",
    { "ucp-agent": 'profile="https://a/p"' },
    Buffer.alloc(0)
  );
  const headers = {
    "ucp-agent": 'profile="https://a/p"',
    "signature-input": additions["Signature-Input"]!.replace(
      ";created",
      ';alg="ecdsa-p256-sha256";created'
    ),
    signature: additions["Signature"]!,
  };
  assertSignatureError(
    () => verifyRequest("GET", "h", "/p", "", headers, Buffer.alloc(0), [jwk]),
    "signature_invalid"
  );
});

/* Verify-side normalization must match the signer's canonical base. */

function signedGet(url: string) {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const additions = signRequest(
    privateKey,
    "k1",
    "GET",
    url,
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"]!,
    signature: additions["Signature"]!,
  };
  return { jwk, headers };
}

test("the default port is stripped per RFC 9421 Section 2.2.3", () => {
  const { jwk, headers } = signedGet("https://merchant.example/p");
  const keyid = verifyRequest(
    "GET",
    "merchant.example:443",
    "/p",
    "",
    headers,
    Buffer.alloc(0),
    [jwk]
  );
  assert.equal(keyid, "k1");
});

test("an empty path is normalized to / on both sides", () => {
  const { jwk, headers } = signedGet("https://merchant.example/");
  const keyid = verifyRequest(
    "GET",
    "merchant.example",
    "",
    "",
    headers,
    Buffer.alloc(0),
    [jwk]
  );
  assert.equal(keyid, "k1");
});

test("host:80 normalises to host", () => {
  assert.equal(normalizeAuthority("Host.Example:80"), "host.example");
});

test("covered field values are OWS-trimmed per RFC 9421 Section 2.1", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const body = Buffer.from('{"x":1}');
  const additions = signRequest(
    privateKey,
    "k1",
    "POST",
    "https://m.example/o",
    { "content-type": "application/json" },
    body
  );
  const headers = {
    "content-type": "  application/json  ",
    "content-digest": additions["Content-Digest"]!,
    "signature-input": additions["Signature-Input"]!,
    signature: additions["Signature"]!,
  };
  const keyid = verifyRequest("POST", "m.example", "/o", "", headers, body, [
    jwk,
  ]);
  assert.equal(keyid, "k1");
});

test("a signed request with a query string verifies", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const additions = signRequest(
    privateKey,
    "k1",
    "GET",
    "https://m.example/p?a=1",
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"]!,
    signature: additions["Signature"]!,
  };
  const keyid = verifyRequest(
    "GET",
    "m.example",
    "/p",
    "a=1",
    headers,
    Buffer.alloc(0),
    [jwk]
  );
  assert.equal(keyid, "k1");
});

test("a signature covering a header absent at verify time is invalid", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const raw =
    '("@method" "@authority" "@path" "x-custom");created=1;keyid="k1"';
  const table: Record<string, string> = {
    "@method": "GET",
    "@authority": "m.example",
    "@path": "/p",
    "x-custom": "v",
  };
  const base = buildSignatureBase(
    ["@method", "@authority", "@path", "x-custom"],
    raw,
    (name) => table[name]
  );
  assert.ok(base);
  const sig = crypto.sign("sha256", base, {
    key: privateKey,
    dsaEncoding: "ieee-p1363",
  });
  const headers = {
    "signature-input": `sig1=${raw}`,
    signature: `sig1=:${sig.toString("base64")}:`,
  };
  assertSignatureError(
    () =>
      verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
        jwk,
      ]),
    "signature_invalid"
  );
});

/* verify_request handles a present-but-unusable signature header set. */

test("a malformed Signature-Input yields signature_missing", () => {
  const headers = { "signature-input": "garbage", signature: "sig1=:AA==:" };
  assertSignatureError(
    () =>
      verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), []),
    "signature_missing"
  );
});

test("a label with no matching Signature member is skipped and fails", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const additions = signRequest(
    privateKey,
    "k1",
    "GET",
    "https://m.example/p",
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"]!.replace("sig1=", "sig2="),
    signature: additions["Signature"]!,
  };
  assert.throws(() =>
    verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [jwk])
  );
});

test("a bodied request without Content-Digest is digest_mismatch", () => {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = jwkFromPublicKey(publicKey, "k1");
  const body = Buffer.from('{"x":1}');
  const additions = signRequest(
    privateKey,
    "k1",
    "POST",
    "https://m.example/o",
    { "content-type": "application/json" },
    body
  );
  const headers = {
    "content-type": "application/json",
    "signature-input": additions["Signature-Input"]!,
    signature: additions["Signature"]!,
  };
  assertSignatureError(
    () => verifyRequest("POST", "m.example", "/o", "", headers, body, [jwk]),
    "digest_mismatch"
  );
});

/* Signature-capable key filtering: use / key_ops (RFC 7517 4.2, 4.3). */

function signedWithJwkExtra(extra: Record<string, unknown>) {
  const { publicKey, privateKey } = es256KeyPair();
  const jwk = { ...jwkFromPublicKey(publicKey, "k1"), ...extra };
  const additions = signRequest(
    privateKey,
    "k1",
    "GET",
    "https://m.example/p",
    {},
    Buffer.alloc(0)
  );
  const headers = {
    "signature-input": additions["Signature-Input"]!,
    signature: additions["Signature"]!,
  };
  return { jwk, headers };
}

test('a key marked use:"sig" verifies', () => {
  const { jwk, headers } = signedWithJwkExtra({ use: "sig" });
  assert.equal(
    verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
      jwk,
    ]),
    "k1"
  );
});

test("a key with no use member verifies (use is OPTIONAL)", () => {
  const { jwk, headers } = signedWithJwkExtra({});
  delete (jwk as Record<string, unknown>)["use"];
  assert.equal(
    verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
      jwk,
    ]),
    "k1"
  );
});

test('a use:"enc" key with the matching kid is key_not_found', () => {
  const { jwk, headers } = signedWithJwkExtra({ use: "enc" });
  assertSignatureError(
    () =>
      verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
        jwk,
      ]),
    "key_not_found"
  );
});

test('a key whose key_ops omits "verify" is skipped', () => {
  const { jwk, headers } = signedWithJwkExtra({
    key_ops: ["encrypt", "decrypt"],
  });
  assertSignatureError(
    () =>
      verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
        jwk,
      ]),
    "key_not_found"
  );
});

test('a key whose key_ops includes "verify" is capable', () => {
  const { jwk, headers } = signedWithJwkExtra({ key_ops: ["verify"] });
  assert.equal(
    verifyRequest("GET", "m.example", "/p", "", headers, Buffer.alloc(0), [
      jwk,
    ]),
    "k1"
  );
});

/* public key construction maps malformed / unsupported keys to spec codes. */

test("an EC JWK missing its y coordinate is signature_invalid", () => {
  assertSignatureError(
    () =>
      verifyRawSignature(
        { kty: "EC", crv: "P-256", x: "AA" },
        RFC_B26_BASE,
        Buffer.alloc(64)
      ),
    "signature_invalid"
  );
});

test("an RSA JWK is algorithm_unsupported", () => {
  assertSignatureError(
    () =>
      verifyRawSignature(
        { kty: "RSA", n: "AA", e: "AQAB" },
        RFC_B26_BASE,
        Buffer.alloc(64)
      ),
    "algorithm_unsupported"
  );
});

/* Profile-URL transport and SSRF guards. */

test("plain http is rejected unless the insecure carve-out is set", async () => {
  await assertSignatureErrorAsync(
    () => assertProfileUrlAllowed("http://example.com/p", false),
    "invalid_profile_url"
  );
});

test("the cloud metadata address is rejected", async () => {
  await assertSignatureErrorAsync(
    () => assertProfileUrlAllowed("https://169.254.169.254/latest", false),
    "invalid_profile_url"
  );
});

test("loopback and RFC 1918 hosts are rejected without the carve-out", async () => {
  for (const url of ["https://127.0.0.1/p", "https://10.0.0.5/p"]) {
    await assertSignatureErrorAsync(
      () => assertProfileUrlAllowed(url, false),
      "invalid_profile_url"
    );
  }
});

test("a URL carrying userinfo is rejected", async () => {
  await assertSignatureErrorAsync(
    () => assertProfileUrlAllowed("https://u:p@example.com/p", false),
    "invalid_profile_url"
  );
});

test("the carve-out permits http loopback for localhost demos", async () => {
  await assertProfileUrlAllowed("http://127.0.0.1:8285/p", true);
});

test("a DNS failure on the profile host is profile_unreachable", async () => {
  await assertSignatureErrorAsync(
    () =>
      assertProfileUrlAllowed("https://nonexistent.invalid.example./x", false),
    "profile_unreachable"
  );
});

test("a host resolving to a public address passes the SSRF guard", async () => {
  // A literal public IP exercises the address vetting without a DNS mock.
  await assertProfileUrlAllowed("https://93.184.216.34/.well-known/ucp", false);
});

/* Key discovery from a signer profile, against a local profile server. */

let profileServer: http.Server;
let profilePort: number;
let profileResponses: Record<
  string,
  { status: number; body: string; location?: string }
>;
let profileHits: string[];

before(async () => {
  profileResponses = {};
  profileHits = [];
  profileServer = http.createServer((req, res) => {
    profileHits.push(req.url ?? "");
    const entry = profileResponses[req.url ?? ""];
    if (!entry) {
      res.writeHead(404).end();
      return;
    }
    const headers: Record<string, string> = {
      "content-type": "application/json",
    };
    if (entry.location) headers["location"] = entry.location;
    res.writeHead(entry.status, headers);
    res.end(entry.body);
  });
  await new Promise<void>((resolve) =>
    profileServer.listen(0, "127.0.0.1", resolve)
  );
  const address = profileServer.address();
  profilePort = typeof address === "object" && address ? address.port : 0;
});

after(() => {
  profileServer.close();
});

function profileUrl(path: string): string {
  return `http://127.0.0.1:${profilePort}${path}`;
}

test("keys[] is read from the ucp envelope", async () => {
  clearKeyCache();
  profileResponses["/envelope.json"] = {
    status: 200,
    body: JSON.stringify({ ucp: { keys: [{ kid: "a" }] } }),
  };
  const keys = await fetchSigningKeys(profileUrl("/envelope.json"), {
    allowInsecure: true,
  });
  assert.equal(keys[0]?.kid, "a");
});

test("a top-level keys[] array (no ucp wrapper) is read", async () => {
  clearKeyCache();
  profileResponses["/top.json"] = {
    status: 200,
    body: JSON.stringify({ keys: [{ kid: "b" }] }),
  };
  const keys = await fetchSigningKeys(profileUrl("/top.json"), {
    allowInsecure: true,
  });
  assert.equal(keys[0]?.kid, "b");
});

test("a profile with only the removed signing_keys[] is profile_malformed", async () => {
  clearKeyCache();
  profileResponses["/legacy.json"] = {
    status: 200,
    body: JSON.stringify({ ucp: { signing_keys: [{ kid: "old" }] } }),
  };
  await assertSignatureErrorAsync(
    () => fetchSigningKeys(profileUrl("/legacy.json"), { allowInsecure: true }),
    "profile_malformed"
  );
});

test("a 3xx response is treated as unreachable (no redirects allowed)", async () => {
  clearKeyCache();
  profileResponses["/redirect.json"] = {
    status: 302,
    body: "",
    location: "https://x/y",
  };
  await assertSignatureErrorAsync(
    () =>
      fetchSigningKeys(profileUrl("/redirect.json"), { allowInsecure: true }),
    "profile_unreachable"
  );
});

test("a non-JSON body yields profile_malformed", async () => {
  clearKeyCache();
  profileResponses["/notjson.json"] = { status: 200, body: "not json" };
  await assertSignatureErrorAsync(
    () =>
      fetchSigningKeys(profileUrl("/notjson.json"), { allowInsecure: true }),
    "profile_malformed"
  );
});

test("a profile with no keys yields profile_malformed", async () => {
  clearKeyCache();
  profileResponses["/keyless.json"] = {
    status: 200,
    body: JSON.stringify({ ucp: {} }),
  };
  await assertSignatureErrorAsync(
    () =>
      fetchSigningKeys(profileUrl("/keyless.json"), { allowInsecure: true }),
    "profile_malformed"
  );
});

test("a second fetch within the TTL is served from the cache", async () => {
  clearKeyCache();
  profileResponses["/cached.json"] = {
    status: 200,
    body: JSON.stringify({ ucp: { keys: [{ kid: "c" }] } }),
  };
  await fetchSigningKeys(profileUrl("/cached.json"), { allowInsecure: true });
  const hitsAfterFirst = profileHits.filter((p) => p === "/cached.json").length;
  await fetchSigningKeys(profileUrl("/cached.json"), { allowInsecure: true });
  const hitsAfterSecond = profileHits.filter(
    (p) => p === "/cached.json"
  ).length;
  assert.equal(hitsAfterFirst, 1);
  assert.equal(hitsAfterSecond, 1);
});

/* extractKeys reads keys[] (canonical per ucp#566) and tolerates junk. */

test("a non-object profile yields no keys, not an error", () => {
  assert.deepEqual(extractKeys(["not", "a", "dict"]), []);
});

test("keys[] under the ucp envelope is the canonical source", () => {
  assert.deepEqual(extractKeys({ ucp: { keys: [{ kid: "k" }] } }), [
    { kid: "k" },
  ]);
});

test("the removed signing_keys[] field is not read (ucp#566)", () => {
  assert.deepEqual(
    extractKeys({ ucp: { signing_keys: [{ kid: "old" }] } }),
    []
  );
});
