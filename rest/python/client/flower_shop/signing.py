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

"""Client-side RFC 9421 request signing for the happy-path demo.

Provides an ``httpx`` auth flow that signs every outgoing request with an
ephemeral ES256 key, and a tiny localhost profile server that publishes the
matching public key so the merchant can discover it via the ``UCP-Agent``
header. This is the counterpart to the server's ``ucp_signing`` verifier and
demonstrates the full sign-then-verify loop end to end.
"""

import base64
import hashlib
import http.server
import json
import threading
import time
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
import httpx

_ES256_COORD_BYTES = 32


def _normalize_authority(host: str) -> str:
  """Normalize an authority per RFC 9421 Section 2.2.3.

  Lowercases and strips the scheme's default port.
  """
  authority = host.lower()
  if authority.endswith(":443"):
    authority = authority[: -len(":443")]
  elif authority.endswith(":80"):
    authority = authority[: -len(":80")]
  return authority


def _b64u(data: bytes) -> str:
  """Encode bytes as base64url text without padding."""
  return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def content_digest(body: bytes) -> str:
  """Return the RFC 9530 sha-256 Content-Digest for the raw body bytes."""
  digest = hashlib.sha256(body).digest()
  return "sha-256=:" + base64.b64encode(digest).decode("ascii") + ":"


def public_jwk(public_key: ec.EllipticCurvePublicKey, kid: str) -> dict:
  """Export an ES256 public key as a UCP JWK."""
  numbers = public_key.public_numbers()
  return {
    "kid": kid,
    "kty": "EC",
    "crv": "P-256",
    "x": _b64u(numbers.x.to_bytes(_ES256_COORD_BYTES, "big")),
    "y": _b64u(numbers.y.to_bytes(_ES256_COORD_BYTES, "big")),
    "use": "sig",
    "alg": "ES256",
  }


class RequestSigner(httpx.Auth):
  """An httpx auth flow that RFC 9421-signs every request.

  The signed component set follows the UCP coverage table: the method,
  authority, and path (plus query when present), the content digest and type
  for bodied requests, and the idempotency-key and ucp-agent headers when they
  are present on the request.
  """

  requires_request_body = True

  def __init__(self, private_key: ec.EllipticCurvePrivateKey, kid: str) -> None:
    """Store the signing key and its identifier."""
    self._key = private_key
    self._kid = kid

  def auth_flow(self, request):
    """Add Content-Digest, Signature-Input, and Signature to the request."""
    body = request.content or b""
    lowered = {k.lower(): v for k, v in request.headers.items()}
    split = urlsplit(str(request.url))

    if body:
      digest = content_digest(body)
      request.headers["Content-Digest"] = digest
      lowered["content-digest"] = digest
      if "content-type" not in lowered:
        request.headers["Content-Type"] = "application/json"
        lowered["content-type"] = "application/json"

    components = ["@method", "@authority", "@path"]
    if split.query:
      components.append("@query")
    if body:
      components.extend(["content-digest", "content-type"])
    if "idempotency-key" in lowered:
      components.append("idempotency-key")
    if "ucp-agent" in lowered:
      components.append("ucp-agent")

    created = int(time.time())
    raw_params = (
      "(" + " ".join(f'"{c}"' for c in components) + ")"
      f';created={created};keyid="{self._kid}"'
    )

    def resolve(name: str) -> str:
      if name == "@method":
        return request.method.upper()
      if name == "@authority":
        return _normalize_authority(split.netloc)
      if name == "@path":
        return split.path or "/"
      if name == "@query":
        return "?" + split.query
      return lowered[name]

    lines = [f'"{c}": {resolve(c)}' for c in components]
    lines.append(f'"@signature-params": {raw_params}')
    base = "\n".join(lines).encode("utf-8")

    der = self._key.sign(base, ec.ECDSA(_ecdsa_hash()))
    r, s = decode_dss_signature(der)
    raw = r.to_bytes(_ES256_COORD_BYTES, "big") + s.to_bytes(
      _ES256_COORD_BYTES, "big"
    )
    request.headers["Signature-Input"] = f"sig1={raw_params}"
    request.headers["Signature"] = (
      "sig1=:" + base64.b64encode(raw).decode("ascii") + ":"
    )
    yield request


def _ecdsa_hash():
  """Return the SHA-256 primitive that ES256 signs with."""
  from cryptography.hazmat.primitives import hashes

  return hashes.SHA256()


class LocalProfileServer:
  """Serve a UCP profile publishing the demo signing key on localhost."""

  def __init__(self, jwk: dict, version: str = "2026-01-23") -> None:
    """Prepare the profile document and HTTP server (not yet started)."""
    document = json.dumps({"ucp": {"version": version, "keys": [jwk]}}).encode()

    class _Handler(http.server.BaseHTTPRequestHandler):
      def do_GET(self) -> None:  # noqa: N802 (http.server API)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(document)

      def log_message(self, *args) -> None:
        del args

    self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    self.port = self._server.server_address[1]
    self.profile_url = f"http://127.0.0.1:{self.port}/profile.json"
    self._thread = threading.Thread(target=self._server.serve_forever)
    self._thread.daemon = True

  def start(self) -> None:
    """Start serving in a background thread."""
    self._thread.start()

  def stop(self) -> None:
    """Stop the server and release its socket."""
    self._server.shutdown()
    self._server.server_close()


def build_signer() -> tuple[RequestSigner, LocalProfileServer]:
  """Create an ephemeral key, a signer, and its localhost profile server."""
  key = ec.generate_private_key(ec.SECP256R1())
  kid = "flower-shop-demo-client"
  server = LocalProfileServer(public_jwk(key.public_key(), kid))
  return RequestSigner(key, kid), server
