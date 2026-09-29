#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""RFC 9421 HTTP Message Signatures for UCP, using the default UCP profile.

This module implements what the UCP `signatures.md` specification actually
requires for platform-to-business request signing and verification:

* RFC 9421 signature base construction and the UCP covered-component set.
* RFC 9530 `Content-Digest` over the raw body bytes (`sha-256`).
* ECDSA P-256 (`ES256`) verification with fixed-width raw `r||s` signatures
  (RFC 9421 Section 3.3.1) -- never ASN.1/DER -- and Ed25519 (RFC 8032).
* Signer public-key discovery from the `UCP-Agent` profile's `signing_keys[]`.

Only the encoding and canonicalization are implemented here; every
cryptographic primitive comes from the `cryptography` package. The module is
deliberately small and readable so it can double as a reference for
implementers building their own UCP signature layer.
"""

import base64
import hashlib
import ipaddress
import logging
import socket
import time
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
import httpx

logger = logging.getLogger(__name__)

# Public keys resolved from a signer profile are cached for this many seconds.
_KEY_CACHE_TTL_SECONDS = 300
_KEY_CACHE: dict[str, tuple[float, list[dict]]] = {}

# Curve -> (JWA algorithm name, coordinate byte length). ES384 is intentionally
# omitted: the spec lists it as OPTIONAL and the baseline every verifier MUST
# support is ES256.
_EC_CURVES = {
  "P-256": ("ES256", 32),
}


class SignatureError(Exception):
  """A signature or profile-resolution failure with UCP wire semantics.

  Attributes:
    code: The UCP error code (e.g. ``signature_invalid``).
    status_code: The HTTP status the spec maps that code to.
    message: A human-readable explanation for logs and error bodies.

  """

  def __init__(self, code: str, status_code: int, message: str) -> None:
    """Store the UCP error code, HTTP status, and message."""
    super().__init__(message)
    self.code = code
    self.status_code = status_code
    self.message = message


def _b64u_decode(value: str) -> bytes:
  """Decode base64url text without requiring padding."""
  return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _b64u_encode(data: bytes) -> str:
  """Encode bytes as base64url text without padding."""
  return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def content_digest(body: bytes) -> str:
  """Return the RFC 9530 ``Content-Digest`` value for the raw body bytes.

  Args:
    body: The exact bytes of the message body as they appear on the wire.

  Returns:
    A structured-field dictionary value of the form ``sha-256=:<base64>:``.

  """
  digest = hashlib.sha256(body).digest()
  return "sha-256=:" + base64.b64encode(digest).decode("ascii") + ":"


def content_digest_matches(header_value: str, body: bytes) -> bool:
  """Check whether a ``Content-Digest`` header covers the given body.

  Only the ``sha-256`` member is inspected; other digest algorithms in the
  dictionary are ignored, matching the spec's requirement to use ``sha-256``.

  Args:
    header_value: The received ``Content-Digest`` header value.
    body: The raw body bytes to compare against.

  Returns:
    True when the header carries a ``sha-256`` member equal to the digest of
    ``body``.

  """
  want = hashlib.sha256(body).digest()
  for member in _sf_split(header_value, ","):
    key, _, val = member.partition("=")
    if key.strip() != "sha-256":
      continue
    val = val.strip()
    if not (val.startswith(":") and val.endswith(":")):
      return False
    try:
      return base64.b64decode(val[1:-1], validate=True) == want
    except (ValueError, TypeError):
      return False
  return False


def _sf_split(value: str, seps: str) -> list[str]:
  """Split a structured-field string on top-level separators.

  Quoted strings and inner lists are treated as opaque, which is enough of
  RFC 8941 to parse ``Signature`` and ``Signature-Input`` headers.

  Args:
    value: The structured-field string.
    seps: Separator characters to split on at the top level.

  Returns:
    The list of trimmed, non-empty segments.

  """
  out: list[str] = []
  cur: list[str] = []
  depth = 0
  quote = False
  i = 0
  while i < len(value):
    c = value[i]
    if quote:
      cur.append(c)
      if c == "\\" and i + 1 < len(value):
        cur.append(value[i + 1])
        i += 1
      elif c == '"':
        quote = False
    elif c == '"':
      quote = True
      cur.append(c)
    elif c == "(":
      depth += 1
      cur.append(c)
    elif c == ")":
      depth -= 1
      cur.append(c)
    elif c in seps and depth == 0:
      out.append("".join(cur).strip())
      cur = []
    else:
      cur.append(c)
    i += 1
  tail = "".join(cur).strip()
  if tail:
    out.append(tail)
  return out


def parse_signature_input(value: str) -> dict | None:
  """Parse a ``Signature-Input`` header into per-label descriptors.

  Args:
    value: The ``Signature-Input`` header value.

  Returns:
    A mapping ``{label: {"raw", "components", "params"}}`` where ``raw`` is the
    member value verbatim (what ``@signature-params`` must echo), ``components``
    are the unquoted component identifiers, and ``params`` maps parameter names
    to their unquoted values. None on malformed input.

  """
  if not isinstance(value, str) or not value.strip():
    return None
  out: dict = {}
  for member in _sf_split(value, ","):
    label, eq, val = member.partition("=")
    label = label.strip()
    val = val.strip()
    if not eq or not label or not val.startswith("("):
      return None
    depth = 0
    end = 0
    for index, char in enumerate(val):
      if char == "(":
        depth += 1
      elif char == ")":
        depth -= 1
        if depth == 0:
          end = index
          break
    inner = val[1:end]
    rest = val[end + 1 :]
    components: list[str] = []
    for tok in _sf_split(inner, " "):
      if not (tok.startswith('"') and tok.endswith('"')) or ";" in tok:
        return None
      components.append(tok[1:-1])
    params: dict[str, str] = {}
    for part in _sf_split(rest, ";"):
      if not part:
        continue
      k, _, v = part.partition("=")
      if v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
      params[k.strip()] = v
    out[label] = {"raw": val, "components": components, "params": params}
  return out or None


def parse_signature(value: str) -> dict | None:
  """Parse a ``Signature`` header into ``{label: raw signature bytes}``.

  Args:
    value: The ``Signature`` header value.

  Returns:
    A mapping of label to decoded signature bytes, or None on malformed input.

  """
  if not isinstance(value, str) or not value.strip():
    return None
  out: dict[str, bytes] = {}
  for member in _sf_split(value, ","):
    label, eq, val = member.partition("=")
    label = label.strip()
    val = val.strip()
    if not eq or not val.startswith(":") or not val.endswith(":"):
      return None
    try:
      out[label] = base64.b64decode(val[1:-1], validate=True)
    except (ValueError, TypeError):
      return None
  return out or None


def build_signature_base(
  components: list[str],
  raw_params: str,
  resolve: "callable",
) -> bytes | None:
  """Construct the RFC 9421 signature base.

  Args:
    components: The ordered component identifiers to cover.
    raw_params: The ``Signature-Input`` member value verbatim, echoed on the
      ``@signature-params`` line.
    resolve: A callable mapping a component identifier to its string value, or
      None when the component cannot be resolved for this message.

  Returns:
    The signature base as bytes, or None if any component is unresolvable.

  """
  lines: list[str] = []
  for name in components:
    value = resolve(name)
    if value is None:
      return None
    lines.append(f'"{name}": {value}')
  lines.append(f'"@signature-params": {raw_params}')
  return "\n".join(lines).encode("utf-8")


def required_components(
  method: str,
  has_query: bool,
  headers: dict,
  has_body: bool,
) -> list[str]:
  """Return the components a UCP request signature MUST cover.

  This is the verification-side coverage gate from ``signatures.md``: a
  signature that omits any of these while the corresponding element is present
  is treated as not covering the message.

  Args:
    method: The HTTP request method (unused today; retained for clarity that
      coverage keys on header presence, not method).
    has_query: Whether the request target carries a query string.
    headers: A case-insensitive mapping of request headers.
    has_body: Whether the request carries a body.

  Returns:
    The ordered list of required component identifiers.

  """
  del method  # Coverage keys on header presence, not on the method.
  required = ["@method", "@authority", "@path"]
  if has_query:
    required.append("@query")
  if has_body:
    required.extend(["content-digest", "content-type"])
  if "idempotency-key" in headers:
    required.append("idempotency-key")
  if "ucp-agent" in headers:
    required.append("ucp-agent")
  # signature-agent is a WBA-shape component (carried with RFC 8941 component
  # parameters, e.g. "signature-agent";key="sig1", under tag=web-bot-auth). This
  # verifier covers the default-UCP regime only and does not parse WBA-shape
  # component parameters, so it does not gate on signature-agent — the coverage
  # promise matches what the module can actually verify. WBA-shape support
  # (member selection, keyid thumbprint binding) is a documented follow-up.
  return required


def public_key_from_jwk(jwk: dict):
  """Build a ``cryptography`` public key from a UCP JWK.

  Args:
    jwk: A JWK describing an EC P-256 or OKP Ed25519 public key.

  Returns:
    An ``EllipticCurvePublicKey`` or ``Ed25519PublicKey``.

  Raises:
    SignatureError: With ``algorithm_unsupported`` when the key type or curve
      is not one UCP verifiers are required to support.

  """
  kty = jwk.get("kty")
  crv = jwk.get("crv")
  try:
    if kty == "EC" and crv in _EC_CURVES:
      x = int.from_bytes(_b64u_decode(jwk["x"]), "big")
      y = int.from_bytes(_b64u_decode(jwk["y"]), "big")
      return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
    if kty == "OKP" and crv == "Ed25519":
      return ed25519.Ed25519PublicKey.from_public_bytes(_b64u_decode(jwk["x"]))
  except (KeyError, ValueError) as exc:
    raise SignatureError(
      "signature_invalid", 401, f"Malformed JWK: {exc}"
    ) from exc
  raise SignatureError(
    "algorithm_unsupported",
    400,
    f"Unsupported key type/curve: kty={kty!r} crv={crv!r}",
  )


def jwk_from_public_key(public_key, kid: str) -> dict:
  """Export a ``cryptography`` public key as a UCP JWK.

  Args:
    public_key: An ``EllipticCurvePublicKey`` (P-256) or ``Ed25519PublicKey``.
    kid: The key identifier to embed.

  Returns:
    A JWK dictionary with ``use`` and ``alg`` populated.

  """
  if isinstance(public_key, ed25519.Ed25519PublicKey):
    from cryptography.hazmat.primitives import serialization

    raw = public_key.public_bytes(
      serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return {
      "kid": kid,
      "kty": "OKP",
      "crv": "Ed25519",
      "x": _b64u_encode(raw),
      "use": "sig",
      "alg": "EdDSA",
    }
  numbers = public_key.public_numbers()
  size = _EC_CURVES["P-256"][1]
  return {
    "kid": kid,
    "kty": "EC",
    "crv": "P-256",
    "x": _b64u_encode(numbers.x.to_bytes(size, "big")),
    "y": _b64u_encode(numbers.y.to_bytes(size, "big")),
    "use": "sig",
    "alg": "ES256",
  }


def verify_raw_signature(jwk: dict, base: bytes, signature: bytes) -> None:
  """Verify a signature base against a JWK public key.

  The algorithm is derived from the key's ``kty``/``crv`` -- never from a
  ``Signature-Input`` ``alg`` parameter, which UCP forbids. ECDSA signatures
  MUST be fixed-width raw ``r||s`` (64 bytes for P-256); ASN.1/DER is rejected
  before it can be decoded.

  Args:
    jwk: The signer's public JWK.
    base: The RFC 9421 signature base bytes.
    signature: The decoded signature value.

  Raises:
    SignatureError: ``algorithm_unsupported`` for keys UCP need not support, or
      ``signature_invalid`` when verification fails or the encoding is wrong.

  """
  public_key = public_key_from_jwk(jwk)
  if isinstance(public_key, ed25519.Ed25519PublicKey):
    try:
      public_key.verify(signature, base)
    except InvalidSignature as exc:
      raise SignatureError(
        "signature_invalid", 401, "Ed25519 signature verification failed"
      ) from exc
    return
  # ECDSA P-256: enforce fixed-width raw r||s (never DER) before converting to
  # the DER form cryptography's verifier expects.
  size = _EC_CURVES["P-256"][1]
  if len(signature) != 2 * size:
    raise SignatureError(
      "signature_invalid",
      401,
      f"ECDSA signature must be {2 * size}-byte raw r||s, got "
      f"{len(signature)} bytes (ASN.1/DER is not permitted)",
    )
  r = int.from_bytes(signature[:size], "big")
  s = int.from_bytes(signature[size:], "big")
  try:
    public_key.verify(encode_dss_signature(r, s), base, ec.ECDSA(_es256_hash()))
  except InvalidSignature as exc:
    raise SignatureError(
      "signature_invalid", 401, "ES256 signature verification failed"
    ) from exc


def _es256_hash():
  """Return the SHA-256 hash primitive used by ES256."""
  from cryptography.hazmat.primitives import hashes

  return hashes.SHA256()


def _authority(host: str) -> str:
  """Normalise an authority per RFC 9421 Section 2.2.3.

  Lowercases and strips the scheme's default port. UCP signatures are HTTPS, so
  a ``host:443`` (added by an intermediary) is equivalent to ``host`` and must
  reconstruct to the same value the signer used.
  """
  authority = host.lower()
  if authority.endswith(":443"):
    authority = authority[: -len(":443")]
  elif authority.endswith(":80"):
    authority = authority[: -len(":80")]
  return authority


def _sig_capable(jwk: dict) -> bool:
  """Whether a JWK is usable for signature verification.

  Per ucp#566 (and RFC 7517 Sections 4.2, 4.3), a profile's ``keys[]`` JWK Set
  may carry non-signature keys. A key is skipped for verification when it is
  marked ``use:"enc"``, or its ``key_ops`` is present but does not include
  ``"verify"``. A key with no ``use``/``key_ops`` is eligible.
  """
  if jwk.get("use") == "enc":
    return False
  key_ops = jwk.get("key_ops")
  return key_ops is None or "verify" in key_ops


def verify_request(
  method: str,
  authority: str,
  path: str,
  query: str,
  headers: dict,
  body: bytes,
  keys: list[dict],
) -> str:
  """Verify the signatures on an inbound UCP request.

  A request is accepted when at least one carried signature fully verifies;
  it is rejected only when every candidate signature is skipped or fails.

  Args:
    method: HTTP method.
    authority: Target authority (host, optionally with port).
    path: Request path without query.
    query: Raw query string (without a leading ``?``); empty when absent.
    headers: Case-insensitive request headers.
    body: Raw request body bytes.
    keys: The signer's published JWKs.

  Returns:
    The ``keyid`` of the signature that verified.

  Raises:
    SignatureError: With the appropriate UCP code when no signature verifies.

  """
  sig_input = parse_signature_input(headers.get("signature-input", ""))
  sigs = parse_signature(headers.get("signature", ""))
  if not sig_input or not sigs:
    raise SignatureError(
      "signature_missing", 401, "Missing Signature-Input or Signature header"
    )

  has_body = bool(body)
  if has_body:
    digest_header = headers.get("content-digest")
    if not digest_header or not content_digest_matches(digest_header, body):
      raise SignatureError(
        "digest_mismatch", 400, "Content-Digest does not match the body"
      )

  required = required_components(method, bool(query), headers, has_body)
  # Resolve keyid only among signature-capable keys (ucp#566): a profile's
  # keys[] is a general JWK Set that may carry non-signature keys, so skip
  # use:"enc" and any key_ops that omits "verify" before matching on kid.
  keys_by_kid = {k.get("kid"): k for k in keys if _sig_capable(k)}

  def resolve(name: str) -> str | None:
    if name == "@method":
      return method.upper()
    if name == "@authority":
      return _authority(authority)
    if name == "@path":
      return path or "/"  # RFC 9421 Section 2.2.6: empty path is "/"
    if name == "@query":
      return "?" + query
    value = headers.get(name)
    # RFC 9421 Section 2.1: a covered field value is OWS-trimmed.
    return value.strip() if isinstance(value, str) else value

  last_error = SignatureError(
    "signature_invalid", 401, "No valid signature found"
  )
  for label, desc in sig_input.items():
    signature = sigs.get(label)
    if signature is None:
      continue
    if "alg" in desc["params"]:
      last_error = SignatureError(
        "signature_invalid",
        401,
        "Signature-Input MUST NOT carry an 'alg' parameter",
      )
      continue
    if not set(required).issubset(desc["components"]):
      missing = sorted(set(required) - set(desc["components"]))
      last_error = SignatureError(
        "signature_invalid",
        401,
        f"Signature does not cover required components: {missing}",
      )
      continue
    keyid = desc["params"].get("keyid")
    jwk = keys_by_kid.get(keyid)
    if jwk is None:
      last_error = SignatureError(
        "key_not_found", 401, f"No published key with kid={keyid!r}"
      )
      continue
    base = build_signature_base(desc["components"], desc["raw"], resolve)
    if base is None:
      last_error = SignatureError(
        "signature_invalid", 401, "Unresolvable signed component"
      )
      continue
    try:
      verify_raw_signature(jwk, base, signature)
    except SignatureError as exc:
      last_error = exc
      continue
    return keyid
  raise last_error


def sign_request(
  private_key,
  kid: str,
  method: str,
  url: str,
  headers: dict,
  body: bytes,
  created: int | None = None,
  extra_components: tuple[str, ...] = (),
) -> dict:
  """Sign a UCP request and return the headers to add.

  Adds ``Content-Digest`` (when a body is present), ``Signature-Input``, and
  ``Signature`` covering exactly the UCP required-component set. Used by the
  demo client and the tests; it is also the reference for a future SDK signer.

  Args:
    private_key: An EC P-256 or Ed25519 private key.
    kid: The key identifier to advertise via ``keyid``.
    method: HTTP method.
    url: The absolute request URL.
    headers: The request headers already set by the caller; extended in place
      is avoided -- a new dict of additions is returned.
    body: Raw request body bytes.
    created: Optional ``created`` timestamp; defaults to the current time.
    extra_components: Additional header components to cover beyond the UCP
      required floor (RFC 9421 permits covering any component). Each is
      covered when the header is present on the request, mirroring how the
      required table conditions on header presence. Webhook deliveries use
      this to bind ``Webhook-Id`` and ``Webhook-Timestamp``.

  Returns:
    A dict of header names to values that the caller must add to the request.

  """
  split = urlsplit(url)
  additions: dict[str, str] = {}
  merged = {k.lower(): v for k, v in headers.items()}
  has_body = bool(body)
  if has_body:
    digest = content_digest(body)
    additions["Content-Digest"] = digest
    merged["content-digest"] = digest
    # The signer must fix and cover Content-Type: a value the transport adds
    # after signing would not be part of the signature base.
    if "content-type" not in merged:
      merged["content-type"] = "application/json"
      additions["Content-Type"] = "application/json"

  components = required_components(method, bool(split.query), merged, has_body)
  for name in extra_components:
    if name not in components and name in merged:
      components.append(name)
  created = int(time.time()) if created is None else created
  raw_params = (
    "(" + " ".join(f'"{c}"' for c in components) + ")"
    f';created={created};keyid="{kid}"'
  )

  def resolve(name: str) -> str | None:
    if name == "@method":
      return method.upper()
    if name == "@authority":
      return _authority(split.netloc)
    if name == "@path":
      return split.path or "/"
    if name == "@query":
      return "?" + split.query
    return merged.get(name)

  base = build_signature_base(components, raw_params, resolve)
  if (
    base is None
  ):  # pragma: no cover - defensive; sign covers only self-derived components
    missing = [c for c in components if resolve(c) is None]
    raise SignatureError(
      "signature_invalid", 401, f"Cannot sign; missing components: {missing}"
    )
  signature = _raw_sign(private_key, base)
  additions["Signature-Input"] = f"sig1={raw_params}"
  additions["Signature"] = (
    "sig1=:" + base64.b64encode(signature).decode("ascii") + ":"
  )
  return additions


def _raw_sign(private_key, base: bytes) -> bytes:
  """Sign a signature base, emitting raw ``r||s`` for ECDSA."""
  if isinstance(private_key, ed25519.Ed25519PrivateKey):
    return private_key.sign(base)
  from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
  )

  der = private_key.sign(base, ec.ECDSA(_es256_hash()))
  r, s = decode_dss_signature(der)
  size = _EC_CURVES["P-256"][1]
  return r.to_bytes(size, "big") + s.to_bytes(size, "big")


def clear_key_cache() -> None:
  """Empty the resolved-key cache (used by tests)."""
  _KEY_CACHE.clear()


def _assert_profile_url_allowed(url: str, allow_insecure: bool) -> None:
  """Reject profile URLs that violate the spec's transport and SSRF rules.

  NOTE: This check is vulnerable to DNS rebinding (TOCTOU) because the IP
  is validated here but resolved again by the HTTP client when fetching.
  A production implementation should resolve the host once, validate the IP,
  and pin the connection to that IP.

  Args:
    url: The candidate profile URL from the ``UCP-Agent`` header.
    allow_insecure: When True, permit ``http`` and loopback/private hosts. This
      exists only for localhost demos and CI, mirroring the official
      conformance harness, and must never be enabled against real agents.

  Raises:
    SignatureError: ``invalid_profile_url`` when the URL is malformed, not
      HTTPS, or resolves to a special-use address.

  """
  split = urlsplit(url)
  if split.scheme != "https" and not (
    allow_insecure and split.scheme == "http"
  ):
    raise SignatureError(
      "invalid_profile_url", 400, f"Profile URL must be HTTPS: {url!r}"
    )
  if split.username or split.password:
    raise SignatureError(
      "invalid_profile_url", 400, "Profile URL must not carry credentials"
    )
  host = split.hostname
  if not host:
    raise SignatureError(
      "invalid_profile_url", 400, f"Profile URL has no host: {url!r}"
    )
  if allow_insecure:
    return
  try:
    infos = socket.getaddrinfo(
      host, split.port or 443, proto=socket.IPPROTO_TCP
    )
  except socket.gaierror as exc:
    raise SignatureError(
      "profile_unreachable", 424, f"Cannot resolve profile host: {host}"
    ) from exc
  for info in infos:
    addr = ipaddress.ip_address(info[4][0])
    if (
      addr.is_private
      or addr.is_loopback
      or addr.is_link_local
      or addr.is_reserved
      or addr.is_multicast
      or addr.is_unspecified
    ):
      raise SignatureError(
        "invalid_profile_url",
        400,
        f"Profile URL resolves to a disallowed address: {addr}",
      )


async def fetch_signing_keys(
  profile_url: str, *, allow_insecure: bool = False
) -> list[dict]:
  """Fetch and cache a signer's published signing keys from its UCP profile.

  Reads the top-level ``signing_keys[]`` of the document behind the
  ``UCP-Agent`` profile URL.

  Args:
    profile_url: The signer's profile URL from the ``UCP-Agent`` header.
    allow_insecure: Permit ``http`` and loopback hosts for demos/CI.

  Returns:
    The list of JWKs published by the signer.

  Raises:
    SignatureError: ``invalid_profile_url`` / ``profile_unreachable`` /
      ``profile_malformed`` per the failure.

  """
  cached = _KEY_CACHE.get(profile_url)
  if cached and cached[0] > time.time():
    return cached[1]

  _assert_profile_url_allowed(profile_url, allow_insecure)
  try:
    async with httpx.AsyncClient(follow_redirects=False) as client:
      response = await client.get(profile_url, timeout=5.0)
  except httpx.HTTPError as exc:
    raise SignatureError(
      "profile_unreachable", 424, f"Profile fetch failed: {exc}"
    ) from exc
  if response.status_code >= 300:
    raise SignatureError(
      "profile_unreachable",
      424,
      f"Profile fetch returned HTTP {response.status_code}",
    )
  try:
    document = response.json()
  except ValueError as exc:
    raise SignatureError(
      "profile_malformed", 422, "Profile is not valid JSON"
    ) from exc

  keys = _extract_keys(document)
  if not keys:
    raise SignatureError(
      "profile_malformed", 422, "Profile publishes no signing keys"
    )
  _KEY_CACHE[profile_url] = (time.time() + _KEY_CACHE_TTL_SECONDS, keys)
  return keys


def _extract_keys(document: dict) -> list[dict]:
  """Pull the signing keys out of a profile document.

  At the UCP version this server declares (2026-04-08,
  ``config.get_server_version()``), ``source/discovery/profile_schema.json``
  ``$defs/base`` requires ``ucp`` and separately declares ``signing_keys`` as
  a top-level sibling of ``ucp`` -- not a field nested inside it. ``ucp`` is
  required on every real profile document, so a reader that looks inside
  ``ucp`` whenever it is present can never see a top-level sibling field on
  any real document; this reads the top level directly instead.

  ucp#566 (merged upstream) renames this field to a top-level ``keys[]`` for
  2026-08-25 and later. When this server's declared version moves to that
  pin, this field name must move with it, in the same change, together with
  ``routes/discovery.py``'s publication side.
  """
  if not isinstance(document, dict):
    return []
  value = document.get("signing_keys")
  return value if isinstance(value, list) and value else []
