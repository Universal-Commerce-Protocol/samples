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

"""End-to-end tests for RFC 9421 request-signature verification.

`PermissiveModeTest` proves the default (unset ``--require_signatures``) leaves
existing clients untouched -- including the exact header shape the official
conformance suite sends -- while still verifying and logging real signatures.
`EnforcedModeTest` proves that with enforcement on, the server returns the
spec's error codes for every failure mode.

Signer keys are served from an in-process localhost profile server, mirroring
the topology of the official conformance harness. All key material is generated
at runtime.
"""

import http.server
import json
import threading
import uuid

from absl.testing import absltest
from cryptography.hazmat.primitives.asymmetric import ec
import config
from cryptography.hazmat.primitives import hashes
import dependencies
from integration_test import IntegrationTest
import ucp_signing


class _ProfileHandler(http.server.BaseHTTPRequestHandler):
  """Serve signer profiles from an in-memory routing table."""

  routes: dict = {}

  def do_GET(self) -> None:  # noqa: N802 (http.server API)
    """Return the configured status and body for the requested path."""
    entry = self.routes.get(self.path)
    if entry is None:
      self.send_response(404)
      self.end_headers()
      return
    status, body = entry
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.end_headers()
    self.wfile.write(body)

  def log_message(self, *args) -> None:
    """Silence the default request logging."""
    del args


class _SigTestBase(IntegrationTest):
  """Shared scaffolding: DB seed (from the base) plus a profile server.

  The lifecycle tests defined on ``IntegrationTest`` are suppressed here so the
  signature scenarios run in isolation; they are exercised in that file, and
  under enforcement the legacy unsigned flows intentionally do not apply.
  """

  # Suppress every test inherited from IntegrationTest — not a hand-kept name
  # list, which would silently re-enable any test added to the base file later.
  for _inherited in [_n for _n in dir(IntegrationTest) if _n.startswith("test_")]:
    locals()[_inherited] = None
  del _inherited

  require_signatures = False

  def setUp(self) -> None:
    """Start a localhost profile server and configure signature flags."""
    super().setUp()
    ucp_signing.clear_key_cache()
    config.FLAGS.require_signatures = self.require_signatures
    config.FLAGS.allow_insecure_profile_urls = True

    self.agent_key = ec.generate_private_key(ec.SECP256R1())
    self.agent_kid = "test-agent-key"
    agent_jwk = ucp_signing.jwk_from_public_key(
      self.agent_key.public_key(), self.agent_kid
    )
    # A deliberately unsupported (RSA) JWK to exercise algorithm_unsupported.
    rsa_jwk = {"kid": "rsa-key", "kty": "RSA", "n": "abc", "e": "AQAB"}

    version = config.get_server_version()
    good = json.dumps(
      {"ucp": {"version": version, "keys": [agent_jwk, rsa_jwk]}}
    ).encode()
    _ProfileHandler.routes = {
      "/profile.json": (200, good),
      "/keyless.json": (200, json.dumps({"ucp": {}}).encode()),
    }
    self.server = http.server.ThreadingHTTPServer(
      ("127.0.0.1", 0), _ProfileHandler
    )
    self.port = self.server.server_address[1]
    self.profile_url = f"http://127.0.0.1:{self.port}/profile.json"
    self.thread = threading.Thread(target=self.server.serve_forever)
    self.thread.daemon = True
    self.thread.start()

  def tearDown(self) -> None:
    """Stop the profile server and reset signature flags."""
    self.server.shutdown()
    self.server.server_close()
    config.FLAGS.require_signatures = False
    config.FLAGS.allow_insecure_profile_urls = False
    super().tearDown()

  def _checkout_body(self, checkout_id: str) -> bytes:
    """Return the raw bytes of a single-item checkout create request."""
    payload = self._create_checkout_payload(
      checkout_id, [("rose", "Red Rose", 1000, 1)]
    )
    return json.dumps(
      payload.model_dump(mode="json", exclude_none=True)
    ).encode()

  def _signed_headers(
    self,
    method: str,
    path: str,
    body: bytes,
    *,
    key=None,
    kid: str | None = None,
    profile: str | None = None,
    extra_sign_headers: dict | None = None,
  ) -> dict:
    """Build headers for a signed request against the in-process server."""
    key = key or self.agent_key
    kid = kid or self.agent_kid
    profile = profile or self.profile_url
    headers = {
      "UCP-Agent": f'profile="{profile}"',
      "Idempotency-Key": str(uuid.uuid4()),
      "Request-Id": str(uuid.uuid4()),
    }
    sign_headers = dict(headers)
    if extra_sign_headers is not None:
      sign_headers = extra_sign_headers
    additions = ucp_signing.sign_request(
      key, kid, method, f"http://testserver{path}", sign_headers, body
    )
    headers.update(additions)
    return headers


class PermissiveModeTest(_SigTestBase):
  """Default mode: existing clients keep working; signatures are logged."""

  require_signatures = False

  def test_official_conformance_replay_no_fetch(self) -> None:
    """Legacy headers with no Signature-Input succeed without a key fetch."""
    calls = []
    original = ucp_signing.fetch_signing_keys

    async def spy(*args, **kwargs):
      calls.append(args)
      return await original(*args, **kwargs)

    ucp_signing.fetch_signing_keys = spy
    try:
      with self.client:
        body = self._checkout_body("replay_1")
        response = self.client.post(
          "/checkout-sessions",
          headers={
            "UCP-Agent": 'profile="https://agent.example/profile"',
            "request-signature": "test",
            "idempotency-key": "1",
            "request-id": "1",
            "content-type": "application/json",
          },
          content=body,
        )
      self.assertEqual(response.status_code, 201, response.text)
      self.assertEmpty(calls, "No profile fetch should occur for unsigned reqs")
    finally:
      ucp_signing.fetch_signing_keys = original

  def test_unsigned_without_legacy_header(self) -> None:
    """A request omitting Request-Signature entirely still succeeds."""
    with self.client:
      body = self._checkout_body("unsigned_1")
      response = self.client.post(
        "/checkout-sessions",
        headers={
          "UCP-Agent": 'profile="https://agent.example/profile"',
          "idempotency-key": "1",
          "request-id": "1",
          "content-type": "application/json",
        },
        content=body,
      )
    self.assertEqual(response.status_code, 201, response.text)

  def test_signed_no_profile_allowed_when_permissive(self) -> None:
    """Permissive mode allows a signed request that can't resolve a key."""
    with self.client:
      body = self._checkout_body("perm_no_profile_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      headers["UCP-Agent"] = "version=2026-01-23"  # no profile=
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self.assertEqual(response.status_code, 201, response.text)

  def test_valid_signature_is_verified_and_logged(self) -> None:
    """A correctly signed request is verified and logs confirmation."""
    with self.client:
      body = self._checkout_body("signed_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      with self.assertLogs(dependencies.logger, level="INFO") as logs:
        response = self.client.post(
          "/checkout-sessions", headers=headers, content=body
        )
    self.assertEqual(response.status_code, 201, response.text)
    self.assertTrue(
      any("RFC 9421 signature verified" in line for line in logs.output)
    )

  def test_bad_signature_allowed_with_warning(self) -> None:
    """An invalid signature is allowed in permissive mode but warned about."""
    with self.client:
      body = self._checkout_body("badsig_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      tampered = body + b" "
      with self.assertLogs(dependencies.logger, level="WARNING") as logs:
        response = self.client.post(
          "/checkout-sessions", headers=headers, content=tampered
        )
    self.assertEqual(response.status_code, 201, response.text)
    self.assertTrue(any("verification failed" in x for x in logs.output))


class EnforcedModeTest(_SigTestBase):
  """Enforcement on: every failure mode returns its spec error code."""

  require_signatures = True

  def _post_signed(self, checkout_id: str, **kwargs):
    """Sign and POST a checkout create; return the response."""
    body = self._checkout_body(checkout_id)
    headers = self._signed_headers("POST", "/checkout-sessions", body, **kwargs)
    return (
      self.client.post("/checkout-sessions", headers=headers, content=body),
      body,
      headers,
    )

  def _assert_error(self, response, status: int, code: str) -> None:
    """Assert an HTTP status and UCP error code on a response."""
    self.assertEqual(response.status_code, status, response.text)
    self.assertEqual(response.json()["detail"]["errors"][0]["code"], code)

  def test_valid_signature_accepted(self) -> None:
    """A correctly signed request is accepted."""
    with self.client:
      response, _, _ = self._post_signed("ok_1")
    self.assertEqual(response.status_code, 201, response.text)

  def test_signed_but_no_profile_url_rejected(self) -> None:
    """A signature present with no UCP-Agent profile= cannot resolve a key.

    The key source is the UCP-Agent profile URL, so a signed request whose
    UCP-Agent carries no profile= is signature_invalid (401) under enforcement.
    """
    with self.client:
      body = self._checkout_body("no_profile_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      headers["UCP-Agent"] = "version=2026-01-23"  # no profile=
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self._assert_error(response, 401, "signature_invalid")

  def test_unsigned_rejected(self) -> None:
    """A request with no signature is rejected with signature_missing."""
    with self.client:
      body = self._checkout_body("miss_1")
      response = self.client.post(
        "/checkout-sessions",
        headers={
          "UCP-Agent": f'profile="{self.profile_url}"',
          "idempotency-key": "1",
          "request-id": "1",
        },
        content=body,
      )
    self._assert_error(response, 401, "signature_missing")

  def test_tampered_body_rejected(self) -> None:
    """A body that does not match Content-Digest yields digest_mismatch."""
    with self.client:
      body = self._checkout_body("tamper_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body + b" "
      )
    self._assert_error(response, 400, "digest_mismatch")

  def test_wrong_key_rejected(self) -> None:
    """A signature from an unpublished key yields signature_invalid."""
    other = ec.generate_private_key(ec.SECP256R1())
    with self.client:
      response, _, _ = self._post_signed("wrong_1", key=other)
    self._assert_error(response, 401, "signature_invalid")

  def test_unknown_kid_rejected(self) -> None:
    """A keyid not in the published set yields key_not_found."""
    with self.client:
      response, _, _ = self._post_signed("kid_1", kid="nonexistent")
    self._assert_error(response, 401, "key_not_found")

  def test_der_signature_rejected(self) -> None:
    """A DER-encoded signature on the wire yields signature_invalid."""
    with self.client:
      body = self._checkout_body("der_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      # Re-sign the base as DER to violate the raw-r||s requirement.
      parsed = ucp_signing.parse_signature_input(headers["Signature-Input"])
      raw = parsed["sig1"]["raw"]
      base = ucp_signing.build_signature_base(
        parsed["sig1"]["components"],
        raw,
        _resolver(body, headers, self.port),
      )
      der = self.agent_key.sign(base, ec.ECDSA(hashes.SHA256()))
      import base64

      headers["Signature"] = (
        "sig1=:" + base64.b64encode(der).decode("ascii") + ":"
      )
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self._assert_error(response, 401, "signature_invalid")

  def test_uncovered_component_rejected(self) -> None:
    """A signature that omits a required component yields signature_invalid."""
    with self.client:
      body = self._checkout_body("cov_1")
      # Sign WITHOUT ucp-agent in the covered set, then add the header.
      headers = self._signed_headers(
        "POST",
        "/checkout-sessions",
        body,
        extra_sign_headers={
          "Idempotency-Key": str(uuid.uuid4()),
          "Request-Id": str(uuid.uuid4()),
        },
      )
      headers["UCP-Agent"] = f'profile="{self.profile_url}"'
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self._assert_error(response, 401, "signature_invalid")

  def test_alg_param_rejected(self) -> None:
    """A signature carrying an alg parameter yields signature_invalid."""
    with self.client:
      body = self._checkout_body("alg_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      headers["Signature-Input"] = headers["Signature-Input"].replace(
        ";created", ';alg="ecdsa-p256-sha256";created'
      )
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self._assert_error(response, 401, "signature_invalid")

  def test_unsupported_key_algorithm(self) -> None:
    """A keyid selecting an RSA key yields algorithm_unsupported."""
    with self.client:
      body = self._checkout_body("rsa_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      headers["Signature-Input"] = headers["Signature-Input"].replace(
        f'keyid="{self.agent_kid}"', 'keyid="rsa-key"'
      )
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self._assert_error(response, 400, "algorithm_unsupported")

  def test_dead_profile_port_unreachable(self) -> None:
    """An unresolvable profile port yields profile_unreachable."""
    dead = "http://127.0.0.1:1/profile.json"
    with self.client:
      response, _, _ = self._post_signed("dead_1", profile=dead)
    self._assert_error(response, 424, "profile_unreachable")

  def test_keyless_profile_malformed(self) -> None:
    """A profile with no keys yields profile_malformed."""
    keyless = f"http://127.0.0.1:{self.port}/keyless.json"
    with self.client:
      response, _, _ = self._post_signed("keyless_1", profile=keyless)
    self._assert_error(response, 422, "profile_malformed")

  def test_http_profile_without_carveout(self) -> None:
    """With the carve-out off, an http profile URL is rejected."""
    config.FLAGS.allow_insecure_profile_urls = False
    with self.client:
      response, _, _ = self._post_signed("insecure_1")
    self._assert_error(response, 400, "invalid_profile_url")

  def test_multi_signature_one_valid(self) -> None:
    """A request with one bad and one valid signature is accepted."""
    with self.client:
      body = self._checkout_body("multi_1")
      headers = self._signed_headers("POST", "/checkout-sessions", body)
      # Add a second, bogus signature label; the good sig1 must still pass.
      headers["Signature-Input"] += (
        ', sig2=("@method");created=1;keyid="' + self.agent_kid + '"'
      )
      headers["Signature"] += ", sig2=:AAAA:"
      response = self.client.post(
        "/checkout-sessions", headers=headers, content=body
      )
    self.assertEqual(response.status_code, 201, response.text)

  def test_webhook_unsigned_rejected(self) -> None:
    """The webhook route also enforces signatures when required."""
    with self.client:
      response = self.client.post(
        "/webhooks/partners/p1/events/order",
        headers={"UCP-Agent": f'profile="{self.profile_url}"'},
        json={"id": "order_1"},
      )
    self._assert_error(response, 401, "signature_missing")


def _resolver(body: bytes, headers: dict, port: int):
  """Build a signature-base component resolver for the DER-tamper test."""
  digest = ucp_signing.content_digest(body)
  values = {
    "@method": "POST",
    "@authority": "testserver",
    "@path": "/checkout-sessions",
    "@query": "?",
    "content-digest": digest,
    "content-type": "application/json",
    "idempotency-key": headers["Idempotency-Key"],
    "ucp-agent": headers["UCP-Agent"],
  }
  return values.get


if __name__ == "__main__":
  absltest.main()
