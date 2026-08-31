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

import crypto, { type KeyObject } from "node:crypto";
import dns from "node:dns/promises";
import net from "node:net";
import { type Context, type MiddlewareHandler } from "hono";
import { type ContentfulStatusCode } from "hono/utils/http-status";

import { signatureConfig } from "./config";

// RFC 9421 HTTP Message Signatures for UCP, using the default UCP profile.
// This is the Node twin of the Python server's ucp_signing.py: RFC 9421
// signature-base construction with the UCP covered-component set, RFC 9530
// Content-Digest over the raw body bytes (sha-256), ES256 (ECDSA P-256 with
// fixed-width raw r||s signatures, never ASN.1/DER) plus Ed25519, and signer
// key discovery from the UCP-Agent profile's keys[]. Only node:crypto is used;
// the RFC 8941 structured-field subset is hand-rolled, no new dependencies.

// Public keys resolved from a signer profile are cached for this long.
const KEY_CACHE_TTL_MS = 300_000;
const keyCache = new Map<string, { expires: number; keys: Jwk[] }>();

// P-256 coordinate width. ES384 is intentionally omitted: the spec lists it as
// OPTIONAL and the baseline every verifier MUST support is ES256.
const ES256_COORD_BYTES = 32;

// A signature or profile-resolution failure with UCP wire semantics: the UCP
// error code and the HTTP status the spec maps it to.
export class SignatureError extends Error {
  constructor(
    readonly code: string,
    readonly statusCode: number,
    message: string
  ) {
    super(message);
  }
}

export type Jwk = {
  kid?: string;
  kty?: string;
  crv?: string;
  x?: string;
  y?: string;
  use?: string;
  key_ops?: string[];
  alg?: string;
  [member: string]: unknown;
};

export type SignatureInputMember = {
  raw: string;
  components: string[];
  params: Record<string, string>;
};

// Returns the RFC 9530 Content-Digest value (sha-256 over the raw body bytes).
export function contentDigest(body: Uint8Array): string {
  const digest = crypto.createHash("sha256").update(body).digest("base64");
  return `sha-256=:${digest}:`;
}

// Whether a Content-Digest header covers the given body. Only the sha-256
// member is inspected, matching the spec's requirement to use sha-256.
export function contentDigestMatches(
  headerValue: string,
  body: Uint8Array
): boolean {
  const want = crypto.createHash("sha256").update(body).digest();
  for (const member of sfSplit(headerValue, ",")) {
    const eq = member.indexOf("=");
    const key = (eq === -1 ? member : member.slice(0, eq)).trim();
    if (key !== "sha-256") continue;
    const value = (eq === -1 ? "" : member.slice(eq + 1)).trim();
    if (!value.startsWith(":") || !value.endsWith(":")) return false;
    const encoded = value.slice(1, -1);
    if (
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
        encoded
      )
    )
      return false;
    return want.equals(Buffer.from(encoded, "base64"));
  }
  return false;
}

// Splits a structured-field string on top-level separators. Quoted strings and
// inner lists are opaque -- enough of RFC 8941 to parse the signature headers.
export function sfSplit(value: string, seps: string): string[] {
  const out: string[] = [];
  let cur = "";
  let depth = 0;
  let quote = false;
  for (let i = 0; i < value.length; i++) {
    const c = value[i]!;
    if (quote) {
      cur += c;
      if (c === "\\" && i + 1 < value.length) {
        cur += value[i + 1];
        i += 1;
      } else if (c === '"') {
        quote = false;
      }
    } else if (c === '"') {
      quote = true;
      cur += c;
    } else if (c === "(") {
      depth += 1;
      cur += c;
    } else if (c === ")") {
      depth -= 1;
      cur += c;
    } else if (seps.includes(c) && depth === 0) {
      out.push(cur.trim());
      cur = "";
    } else {
      cur += c;
    }
  }
  const tail = cur.trim();
  if (tail) out.push(tail);
  return out;
}

// Parses a Signature-Input header into per-label descriptors: the member value
// verbatim (what @signature-params must echo), the unquoted component
// identifiers, and the parameters. Null on malformed input.
export function parseSignatureInput(
  value: string
): Record<string, SignatureInputMember> | null {
  if (typeof value !== "string" || !value.trim()) return null;
  const out: Record<string, SignatureInputMember> = {};
  for (const member of sfSplit(value, ",")) {
    const eq = member.indexOf("=");
    const label = (eq === -1 ? member : member.slice(0, eq)).trim();
    const val = (eq === -1 ? "" : member.slice(eq + 1)).trim();
    if (eq === -1 || !label || !val.startsWith("(")) return null;
    let depth = 0;
    let end = 0;
    for (let index = 0; index < val.length; index++) {
      const char = val[index];
      if (char === "(") {
        depth += 1;
      } else if (char === ")") {
        depth -= 1;
        if (depth === 0) {
          end = index;
          break;
        }
      }
    }
    const inner = val.slice(1, end);
    const rest = val.slice(end + 1);
    const components: string[] = [];
    for (const tok of sfSplit(inner, " ")) {
      if (!tok.startsWith('"') || !tok.endsWith('"') || tok.includes(";")) {
        return null;
      }
      components.push(tok.slice(1, -1));
    }
    const params: Record<string, string> = {};
    for (const part of sfSplit(rest, ";")) {
      if (!part) continue;
      const pEq = part.indexOf("=");
      const k = (pEq === -1 ? part : part.slice(0, pEq)).trim();
      let v = pEq === -1 ? "" : part.slice(pEq + 1);
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      params[k] = v;
    }
    out[label] = { raw: val, components, params };
  }
  return Object.keys(out).length ? out : null;
}

// Parses a Signature header into {label: raw signature bytes}, or null on
// malformed input.
export function parseSignature(value: string): Record<string, Buffer> | null {
  if (typeof value !== "string" || !value.trim()) return null;
  const out: Record<string, Buffer> = {};
  for (const member of sfSplit(value, ",")) {
    const eq = member.indexOf("=");
    const label = (eq === -1 ? member : member.slice(0, eq)).trim();
    const val = (eq === -1 ? "" : member.slice(eq + 1)).trim();
    if (eq === -1 || !val.startsWith(":") || !val.endsWith(":")) return null;
    const encoded = val.slice(1, -1);
    if (
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
        encoded
      )
    )
      return null;
    out[label] = Buffer.from(encoded, "base64");
  }
  return Object.keys(out).length ? out : null;
}

// Constructs the RFC 9421 signature base. The raw Signature-Input member value
// is echoed verbatim on the @signature-params line. Null if any covered
// component cannot be resolved for this message.
export function buildSignatureBase(
  components: string[],
  rawParams: string,
  resolve: (name: string) => string | undefined | null
): Buffer | null {
  const lines: string[] = [];
  for (const name of components) {
    const value = resolve(name);
    if (value === undefined || value === null) return null;
    lines.push(`"${name}": ${value}`);
  }
  lines.push(`"@signature-params": ${rawParams}`);
  return Buffer.from(lines.join("\n"), "utf-8");
}

// The components a UCP request signature MUST cover (the verification-side
// coverage gate from signatures.md). Coverage keys on header presence, not on
// the method. signature-agent is a WBA-shape component this default-UCP
// verifier does not parse, so it is deliberately outside the gate.
export function requiredComponents(
  _method: string,
  hasQuery: boolean,
  headers: Record<string, string>,
  hasBody: boolean
): string[] {
  const required = ["@method", "@authority", "@path"];
  if (hasQuery) required.push("@query");
  if (hasBody) required.push("content-digest", "content-type");
  if ("idempotency-key" in headers) required.push("idempotency-key");
  if ("ucp-agent" in headers) required.push("ucp-agent");
  return required;
}

// Normalises an authority per RFC 9421 Section 2.2.3: lowercase, scheme
// default port stripped, so host:443 added by an intermediary reconstructs to
// the value the signer used.
export function normalizeAuthority(host: string): string {
  let authority = host.toLowerCase();
  if (authority.endsWith(":443")) {
    authority = authority.slice(0, -":443".length);
  } else if (authority.endsWith(":80")) {
    authority = authority.slice(0, -":80".length);
  }
  return authority;
}

// Exports a node:crypto public key as a UCP JWK (used by tests and demos).
export function jwkFromPublicKey(publicKey: KeyObject, kid: string): Jwk {
  const jwk = publicKey.export({ format: "jwk" }) as Jwk;
  const alg = jwk.kty === "OKP" ? "EdDSA" : "ES256";
  return { kid, ...jwk, use: "sig", alg };
}

// Builds a node:crypto public key from a UCP JWK. The supported set is what
// UCP verifiers must support (EC P-256) plus Ed25519; anything else is
// algorithm_unsupported.
function publicKeyFromJwk(jwk: Jwk): KeyObject {
  const { kty, crv } = jwk;
  if (
    (kty === "EC" && crv === "P-256") ||
    (kty === "OKP" && crv === "Ed25519")
  ) {
    try {
      return crypto.createPublicKey({
        key: jwk as crypto.JsonWebKey,
        format: "jwk",
      });
    } catch (e) {
      throw new SignatureError("signature_invalid", 401, `Malformed JWK: ${e}`);
    }
  }
  throw new SignatureError(
    "algorithm_unsupported",
    400,
    `Unsupported key type/curve: kty=${JSON.stringify(kty)} crv=${JSON.stringify(crv)}`
  );
}

// Verifies a signature base against a JWK public key. The algorithm is derived
// from the key's kty/crv -- never from a Signature-Input alg parameter, which
// UCP forbids. ECDSA signatures MUST be fixed-width raw r||s (64 bytes for
// P-256); ASN.1/DER is rejected before any verification is attempted.
export function verifyRawSignature(
  jwk: Jwk,
  base: Buffer,
  signature: Buffer
): void {
  const publicKey = publicKeyFromJwk(jwk);
  if (publicKey.asymmetricKeyType === "ed25519") {
    if (!crypto.verify(null, base, publicKey, signature)) {
      throw new SignatureError(
        "signature_invalid",
        401,
        "Ed25519 signature verification failed"
      );
    }
    return;
  }
  if (signature.length !== 2 * ES256_COORD_BYTES) {
    throw new SignatureError(
      "signature_invalid",
      401,
      `ECDSA signature must be ${2 * ES256_COORD_BYTES}-byte raw r||s, got ` +
        `${signature.length} bytes (ASN.1/DER is not permitted)`
    );
  }
  let ok = false;
  try {
    ok = crypto.verify(
      "sha256",
      base,
      { key: publicKey, dsaEncoding: "ieee-p1363" },
      signature
    );
  } catch {
    ok = false;
  }
  if (!ok) {
    throw new SignatureError(
      "signature_invalid",
      401,
      "ES256 signature verification failed"
    );
  }
}

// Whether a JWK is usable for signature verification. A profile's keys[] JWK
// Set may carry non-signature keys (RFC 7517 Sections 4.2, 4.3): a key marked
// use:"enc", or whose key_ops is present but omits "verify", is skipped.
function sigCapable(jwk: Jwk): boolean {
  if (jwk.use === "enc") return false;
  const keyOps = jwk.key_ops;
  return keyOps === undefined || keyOps.includes("verify");
}

// Verifies the signatures on an inbound UCP request. A request is accepted
// when at least one carried signature fully verifies; it is rejected only when
// every candidate signature is skipped or fails. Returns the keyid that
// verified.
export function verifyRequest(
  method: string,
  authority: string,
  path: string,
  query: string,
  headers: Record<string, string>,
  body: Uint8Array,
  keys: Jwk[]
): string {
  const sigInput = parseSignatureInput(headers["signature-input"] ?? "");
  const sigs = parseSignature(headers["signature"] ?? "");
  if (!sigInput || !sigs) {
    throw new SignatureError(
      "signature_missing",
      401,
      "Missing Signature-Input or Signature header"
    );
  }

  const hasBody = body.length > 0;
  if (hasBody) {
    const digestHeader = headers["content-digest"];
    if (!digestHeader || !contentDigestMatches(digestHeader, body)) {
      throw new SignatureError(
        "digest_mismatch",
        400,
        "Content-Digest does not match the body"
      );
    }
  }

  const required = requiredComponents(method, query !== "", headers, hasBody);
  const keysByKid = new Map<string | undefined, Jwk>();
  for (const key of keys) {
    if (sigCapable(key)) keysByKid.set(key.kid, key);
  }

  const resolve = (name: string): string | undefined => {
    if (name === "@method") return method.toUpperCase();
    if (name === "@authority") return normalizeAuthority(authority);
    if (name === "@path") return path || "/"; // RFC 9421 2.2.6: empty is "/"
    if (name === "@query") return "?" + query;
    const value = headers[name];
    // RFC 9421 Section 2.1: a covered field value is OWS-trimmed.
    return typeof value === "string" ? value.trim() : value;
  };

  let lastError = new SignatureError(
    "signature_invalid",
    401,
    "No valid signature found"
  );
  for (const [label, desc] of Object.entries(sigInput)) {
    const signature = sigs[label];
    if (signature === undefined) continue;
    if ("alg" in desc.params) {
      lastError = new SignatureError(
        "signature_invalid",
        401,
        "Signature-Input MUST NOT carry an 'alg' parameter"
      );
      continue;
    }
    const missing = required.filter((c) => !desc.components.includes(c));
    if (missing.length) {
      lastError = new SignatureError(
        "signature_invalid",
        401,
        `Signature does not cover required components: ${missing.sort().join(", ")}`
      );
      continue;
    }
    const keyid = desc.params["keyid"];
    const jwk = keysByKid.get(keyid);
    if (jwk === undefined) {
      lastError = new SignatureError(
        "key_not_found",
        401,
        `No published key with kid=${JSON.stringify(keyid)}`
      );
      continue;
    }
    const base = buildSignatureBase(desc.components, desc.raw, resolve);
    if (base === null) {
      lastError = new SignatureError(
        "signature_invalid",
        401,
        "Unresolvable signed component"
      );
      continue;
    }
    try {
      verifyRawSignature(jwk, base, signature);
    } catch (e) {
      if (!(e instanceof SignatureError)) throw e;
      lastError = e;
      continue;
    }
    return keyid ?? "";
  }
  throw lastError;
}

// Signs a raw signature base, emitting fixed-width raw r||s for ECDSA.
function rawSign(privateKey: KeyObject, base: Buffer): Buffer {
  if (privateKey.asymmetricKeyType === "ed25519") {
    return crypto.sign(null, base, privateKey);
  }
  return crypto.sign("sha256", base, {
    key: privateKey,
    dsaEncoding: "ieee-p1363",
  });
}

// Signs a UCP request and returns the headers to add: Content-Digest (when a
// body is present), Signature-Input, and Signature covering the UCP
// required-component set. Used by the tests as the client side of the loop,
// and by the webhook sender as this business's signer.
//
// extraComponents lists additional header components to cover beyond the UCP
// required floor (RFC 9421 permits covering any component). Each is covered
// when the header is present on the request, mirroring how the required
// table conditions on header presence. Webhook deliveries use this to bind
// Webhook-Id and Webhook-Timestamp.
export function signRequest(
  privateKey: KeyObject,
  kid: string,
  method: string,
  url: string,
  headers: Record<string, string>,
  body: Uint8Array,
  created?: number,
  extraComponents: string[] = []
): Record<string, string> {
  const target = new URL(url);
  const additions: Record<string, string> = {};
  const merged: Record<string, string> = {};
  for (const [k, v] of Object.entries(headers)) merged[k.toLowerCase()] = v;
  const hasBody = body.length > 0;
  if (hasBody) {
    const digest = contentDigest(body);
    additions["Content-Digest"] = digest;
    merged["content-digest"] = digest;
    // The signer must fix and cover Content-Type: a value the transport adds
    // after signing would not be part of the signature base.
    if (!("content-type" in merged)) {
      merged["content-type"] = "application/json";
      additions["Content-Type"] = "application/json";
    }
  }

  const query = target.search.slice(1);
  const components = requiredComponents(method, query !== "", merged, hasBody);
  for (const name of extraComponents) {
    if (!components.includes(name) && name in merged) components.push(name);
  }
  const createdAt = created ?? Math.floor(Date.now() / 1000);
  const rawParams =
    "(" +
    components.map((c) => `"${c}"`).join(" ") +
    `);created=${createdAt};keyid="${kid}"`;

  const resolve = (name: string): string | undefined => {
    if (name === "@method") return method.toUpperCase();
    if (name === "@authority") return normalizeAuthority(target.host);
    if (name === "@path") return target.pathname || "/";
    if (name === "@query") return "?" + query;
    return merged[name];
  };

  const base = buildSignatureBase(components, rawParams, resolve);
  if (base === null) {
    const missing = components.filter((c) => resolve(c) === undefined);
    throw new SignatureError(
      "signature_invalid",
      401,
      `Cannot sign; missing components: ${missing.join(", ")}`
    );
  }
  const signature = rawSign(privateKey, base);
  additions["Signature-Input"] = `sig1=${rawParams}`;
  additions["Signature"] = `sig1=:${signature.toString("base64")}:`;
  return additions;
}

// Empties the resolved-key cache (used by tests).
export function clearKeyCache(): void {
  keyCache.clear();
}

function isDisallowedV4(address: string): boolean {
  const octets = address.split(".").map(Number);
  const [a = 0, b = 0, c = 0] = octets;
  return (
    a === 0 || // "this network"
    a === 10 || // RFC 1918
    a === 127 || // loopback
    (a === 100 && b >= 64 && b < 128) || // shared address space
    (a === 169 && b === 254) || // link-local (incl. cloud metadata)
    (a === 172 && b >= 16 && b < 32) || // RFC 1918
    (a === 192 && b === 0 && c === 0) || // IETF protocol assignments
    (a === 192 && b === 0 && c === 2) || // documentation
    (a === 192 && b === 168) || // RFC 1918
    (a === 198 && (b === 18 || b === 19)) || // benchmarking
    (a === 198 && b === 51 && c === 100) || // documentation
    (a === 203 && b === 0 && c === 113) || // documentation
    a >= 224 // multicast and reserved
  );
}

// Whether an address is special-use (loopback, private, link-local, reserved,
// multicast, unspecified). IPv6 is vetted by allowing only current global
// unicast (2000::/3, minus documentation space); v4-mapped addresses are
// classified by their embedded IPv4 address.
function isDisallowedAddress(address: string): boolean {
  if (net.isIP(address) === 4) return isDisallowedV4(address);
  const lower = address.toLowerCase();
  const mapped = /^::ffff:(\d+\.\d+\.\d+\.\d+)$/.exec(lower);
  if (mapped) return isDisallowedV4(mapped[1]!);
  if (lower.startsWith("2001:db8:") || lower === "2001:db8") return true;
  const firstGroup = parseInt(lower.split(":")[0] || "0", 16);
  return firstGroup < 0x2000 || firstGroup >= 0x4000;
}

// Rejects profile URLs that violate the spec's transport and SSRF rules.
// NOTE: like the Python reference, this check is vulnerable to DNS rebinding
// (TOCTOU): the IP is validated here but resolved again by fetch. A production
// implementation should resolve once, validate, and pin the connection.
export async function assertProfileUrlAllowed(
  url: string,
  allowInsecure: boolean
): Promise<void> {
  let target: URL;
  try {
    target = new URL(url);
  } catch {
    throw new SignatureError(
      "invalid_profile_url",
      400,
      `Profile URL is malformed: ${JSON.stringify(url)}`
    );
  }
  if (
    target.protocol !== "https:" &&
    !(allowInsecure && target.protocol === "http:")
  ) {
    throw new SignatureError(
      "invalid_profile_url",
      400,
      `Profile URL must be HTTPS: ${JSON.stringify(url)}`
    );
  }
  if (target.username || target.password) {
    throw new SignatureError(
      "invalid_profile_url",
      400,
      "Profile URL must not carry credentials"
    );
  }
  const host = target.hostname.replace(/^\[|\]$/g, "");
  if (!host) {
    throw new SignatureError(
      "invalid_profile_url",
      400,
      `Profile URL has no host: ${JSON.stringify(url)}`
    );
  }
  if (allowInsecure) return;
  let addresses: string[];
  if (net.isIP(host)) {
    addresses = [host];
  } else {
    try {
      const results = await dns.lookup(host, { all: true });
      addresses = results.map((r) => r.address);
    } catch {
      throw new SignatureError(
        "profile_unreachable",
        424,
        `Cannot resolve profile host: ${host}`
      );
    }
  }
  for (const address of addresses) {
    if (isDisallowedAddress(address)) {
      throw new SignatureError(
        "invalid_profile_url",
        400,
        `Profile URL resolves to a disallowed address: ${address}`
      );
    }
  }
}

// Pulls the signing keys out of a profile document. At the UCP version this
// server declares (2026-04-08, config.ts UCP_VERSION),
// source/discovery/profile_schema.json $defs/base requires `ucp` and
// separately declares `signing_keys` as a top-level sibling of `ucp` -- not
// a field nested inside it. `ucp` is required on every real profile
// document, so a reader that looks inside `ucp` whenever it is present can
// never see a top-level sibling field on any real document; this reads the
// top level directly instead.
//
// ucp#566 (merged upstream) renames this field to a top-level keys[] for
// 2026-08-25 and later. When this server's UCP_VERSION moves to that pin,
// this field name must move with it, in the same change, together with
// discovery.ts's publication side.
export function extractKeys(document: unknown): Jwk[] {
  if (typeof document !== "object" || document === null) return [];
  const doc = document as Record<string, unknown>;
  const value = doc["signing_keys"];
  return Array.isArray(value) && value.length ? (value as Jwk[]) : [];
}

// Fetches and caches a signer's published signing keys from its UCP profile
// (the top-level signing_keys[] of the document behind the UCP-Agent
// profile URL).
export async function fetchSigningKeys(
  profileUrl: string,
  options: { allowInsecure?: boolean } = {}
): Promise<Jwk[]> {
  const cached = keyCache.get(profileUrl);
  if (cached && cached.expires > Date.now()) return cached.keys;

  await assertProfileUrlAllowed(profileUrl, options.allowInsecure ?? false);
  let response: globalThis.Response;
  try {
    response = await fetch(profileUrl, {
      redirect: "manual",
      signal: AbortSignal.timeout(5000),
    });
  } catch (e) {
    throw new SignatureError(
      "profile_unreachable",
      424,
      `Profile fetch failed: ${e}`
    );
  }
  if (response.status >= 300) {
    throw new SignatureError(
      "profile_unreachable",
      424,
      `Profile fetch returned HTTP ${response.status}`
    );
  }
  let document: unknown;
  try {
    document = await response.json();
  } catch {
    throw new SignatureError(
      "profile_malformed",
      422,
      "Profile is not valid JSON"
    );
  }
  const keys = extractKeys(document);
  if (!keys.length) {
    throw new SignatureError(
      "profile_malformed",
      422,
      "Profile publishes no signing keys"
    );
  }
  keyCache.set(profileUrl, { expires: Date.now() + KEY_CACHE_TTL_MS, keys });
  return keys;
}

function signatureErrorResponse(c: Context, exc: SignatureError): Response {
  // The same wire shape as the Python server's error envelope, inside the
  // { detail } wrapper this server already uses for its 4xx responses.
  return c.json(
    {
      detail: {
        status: "error",
        errors: [
          { code: exc.code, message: exc.message, severity: "critical" },
        ],
      },
    },
    exc.statusCode as ContentfulStatusCode
  );
}

// Hono middleware verifying an inbound request's RFC 9421 signature per the
// UCP spec. The signer's keys are discovered from the UCP-Agent header's
// profile URL (its keys[]). Behaviour depends on signatureConfig:
//
// * requireSignatures: a missing or invalid signature is rejected with the
//   spec's error code (401 signature_missing / signature_invalid /
//   key_not_found, 400 digest_mismatch / algorithm_unsupported, etc.).
// * Otherwise (the default), signatures are still verified when present and
//   the outcome is logged, but unsigned or invalid requests are allowed. This
//   keeps the sample interoperable with clients that do not yet sign.
//
// No profile fetch occurs unless a Signature-Input header is present, so
// unsigned traffic incurs no extra work.
export const verifySignature: MiddlewareHandler = async (c, next) => {
  const enforcing = signatureConfig.requireSignatures;
  const headers: Record<string, string> = {};
  c.req.raw.headers.forEach((value, key) => {
    headers[key] = value;
  });

  if (!("signature-input" in headers) || !("signature" in headers)) {
    if (enforcing) {
      return signatureErrorResponse(
        c,
        new SignatureError(
          "signature_missing",
          401,
          "Request signature is required"
        )
      );
    }
    c.var.logger.debug("No request signature present; skipping verification");
    return next();
  }

  const match = /profile="([^"]+)"/.exec(headers["ucp-agent"] ?? "");
  if (!match) {
    const exc = new SignatureError(
      "signature_invalid",
      401,
      "UCP-Agent profile URL is required to resolve the signing key"
    );
    if (enforcing) return signatureErrorResponse(c, exc);
    c.var.logger.warn(`Cannot verify signature: ${exc.message}`);
    return next();
  }

  const body = Buffer.from(await c.req.arrayBuffer());
  const url = new URL(c.req.url);
  try {
    const keys = await fetchSigningKeys(match[1]!, {
      allowInsecure: signatureConfig.allowInsecureProfileUrls,
    });
    const keyid = verifyRequest(
      c.req.method,
      url.host,
      url.pathname,
      url.search.slice(1),
      headers,
      body,
      keys
    );
    c.var.logger.info(
      `RFC 9421 signature verified (keyid=${keyid}, profile=${match[1]})`
    );
  } catch (e) {
    if (!(e instanceof SignatureError)) throw e;
    if (enforcing) return signatureErrorResponse(c, e);
    c.var.logger.warn(
      `Request signature verification failed (${e.code}: ${e.message}); ` +
        "allowing because REQUIRE_SIGNATURES is not set"
    );
  }
  return next();
};
