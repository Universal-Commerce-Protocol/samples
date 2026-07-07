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

"""Unit tests for the RFC 9421 signing module.

Correctness is anchored to three independent oracles: the RFC 9421 Appendix B
and RFC 9530 published vectors, an explicit DER-rejection check for the UCP
raw-`r||s` requirement, and a differential comparison against the independent
`http-message-signatures` library.

All key material is generated at runtime or reconstructed from the RFC's raw
JWK coordinates; no private-key files are committed.
"""

import base64

from absl.testing import absltest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
import httpx
import ucp_signing as signing


def _b64u(value: str) -> bytes:
  """Decode base64url without padding (for the RFC JWK coordinates)."""
  return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


# RFC 9421 Appendix B.1.4 test-key-ed25519 (JWK coordinates, verbatim).
RFC_ED25519_JWK = {
  "kty": "OKP",
  "crv": "Ed25519",
  "kid": "test-key-ed25519",
  "x": "JrQLj5P_89iXES9-vFgrIy29clF9CC_oPPsw3c5D0bs",
}
RFC_ED25519_D = "n4Ni-HpISpVObnQMW0wOhCKROaIKqKtW_2ZYb2p9KcU"

# RFC 9421 Appendix B.2.6 signature base and signature (byte-exact oracle).
RFC_B26_BASE = (
  b'"date": Tue, 20 Apr 2021 02:07:55 GMT\n'
  b'"@method": POST\n'
  b'"@path": /foo\n'
  b'"@authority": example.com\n'
  b'"content-type": application/json\n'
  b'"content-length": 18\n'
  b'"@signature-params": ("date" "@method" "@path" "@authority" '
  b'"content-type" "content-length");created=1618884473'
  b';keyid="test-key-ed25519"'
)
RFC_B26_SIGNATURE = base64.b64decode(
  "wqcAqbmYJ2ji2glfAMaRy4gruYYnx2nEFN2HN6jrnDnQCK1u02Gb04v9EDgwUPiu4"
  "A0w6vuQv5lIp5WPpBKRCw=="
)


class ContentDigestTest(absltest.TestCase):
  """RFC 9530 Content-Digest generation and matching."""

  def test_rfc9530_lf_body_vector(self) -> None:
    """The 19-byte LF body matches RFC 9530's canonical sha-256 value."""
    self.assertEqual(
      signing.content_digest(b'{"hello": "world"}\n'),
      "sha-256=:RK/0qy18MlBSVnWgjwz6lZEWjP/lF5HF9bvEF8FabDg=:",
    )

  def test_rfc9421_no_lf_body_vector(self) -> None:
    """The 18-byte body matches the value used in RFC 9421's examples."""
    self.assertEqual(
      signing.content_digest(b'{"hello": "world"}'),
      "sha-256=:X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=:",
    )

  def test_matches_accepts_and_rejects(self) -> None:
    """content_digest_matches accepts the right body and rejects others."""
    body = b'{"a": 1}'
    header = signing.content_digest(body)
    self.assertTrue(signing.content_digest_matches(header, body))
    self.assertFalse(signing.content_digest_matches(header, b'{"a": 2}'))


class SignatureBaseTest(absltest.TestCase):
  """RFC 9421 signature-base construction."""

  def test_matches_rfc_b26_base(self) -> None:
    """Reconstructing the B.2.6 components yields the RFC's exact base."""
    components = [
      "date",
      "@method",
      "@path",
      "@authority",
      "content-type",
      "content-length",
    ]
    raw = (
      '("date" "@method" "@path" "@authority" "content-type" '
      '"content-length");created=1618884473;keyid="test-key-ed25519"'
    )
    values = {
      "date": "Tue, 20 Apr 2021 02:07:55 GMT",
      "@method": "POST",
      "@path": "/foo",
      "@authority": "example.com",
      "content-type": "application/json",
      "content-length": "18",
    }
    base = signing.build_signature_base(components, raw, values.get)
    self.assertEqual(base, RFC_B26_BASE)

  def test_signature_params_echoed_verbatim(self) -> None:
    """The @signature-params line echoes the member value verbatim."""
    raw = '("@method");created=5;keyid="k"'
    base = signing.build_signature_base(["@method"], raw, lambda _: "GET")
    self.assertTrue(base.endswith(f'"@signature-params": {raw}'.encode()))

  def test_unresolvable_component_returns_none(self) -> None:
    """A component the resolver cannot supply aborts base construction."""
    self.assertIsNone(
      signing.build_signature_base(["x-missing"], "()", lambda _: None)
    )


class Rfc9421VectorsTest(absltest.TestCase):
  """Byte-exact Ed25519 and verify-direction ES256 against Appendix B."""

  def test_ed25519_b26_verifies(self) -> None:
    """The RFC's published Ed25519 signature verifies through the module."""
    signing.verify_raw_signature(
      RFC_ED25519_JWK, RFC_B26_BASE, RFC_B26_SIGNATURE
    )

  def test_ed25519_b26_byte_exact_sign(self) -> None:
    """Ed25519 is deterministic: our signature equals the RFC's bytes."""
    key = ed25519.Ed25519PrivateKey.from_private_bytes(_b64u(RFC_ED25519_D))
    self.assertEqual(signing._raw_sign(key, RFC_B26_BASE), RFC_B26_SIGNATURE)

  def test_ed25519_tampered_base_fails(self) -> None:
    """A modified base no longer verifies against the RFC signature."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_raw_signature(
        RFC_ED25519_JWK, RFC_B26_BASE + b" ", RFC_B26_SIGNATURE
      )
    self.assertEqual(ctx.exception.code, "signature_invalid")

  def test_es256_roundtrip(self) -> None:
    """An ES256 signature we produce verifies with the derived JWK."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k")
    sig = signing._raw_sign(key, RFC_B26_BASE)
    signing.verify_raw_signature(jwk, RFC_B26_BASE, sig)


class RawSignatureEncodingTest(absltest.TestCase):
  """The UCP raw-r||s ECDSA requirement (spec MUST; issue #569)."""

  def setUp(self) -> None:
    """Create a P-256 key and its JWK for the encoding tests."""
    super().setUp()
    self.key = ec.generate_private_key(ec.SECP256R1())
    self.jwk = signing.jwk_from_public_key(self.key.public_key(), "k")

  def test_der_signature_rejected(self) -> None:
    """A DER-encoded ECDSA signature must be rejected as non-conformant."""
    der = self.key.sign(RFC_B26_BASE, ec.ECDSA(hashes.SHA256()))
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_raw_signature(self.jwk, RFC_B26_BASE, der)
    self.assertEqual(ctx.exception.code, "signature_invalid")

  def test_raw_64_byte_accepted(self) -> None:
    """A well-formed 64-byte raw signature verifies."""
    sig = signing._raw_sign(self.key, RFC_B26_BASE)
    self.assertLen(sig, 64)
    signing.verify_raw_signature(self.jwk, RFC_B26_BASE, sig)

  def test_wrong_length_rejected(self) -> None:
    """Signatures that are not 64 bytes are rejected before verification."""
    sig = signing._raw_sign(self.key, RFC_B26_BASE)
    for bad in (sig[:-1], sig + b"\x00"):
      with self.assertRaises(signing.SignatureError) as ctx:
        signing.verify_raw_signature(self.jwk, RFC_B26_BASE, bad)
      self.assertEqual(ctx.exception.code, "signature_invalid")


class SfParserTest(absltest.TestCase):
  """RFC 8941 subset parsing of Signature-Input and Signature."""

  def test_parses_components_and_params(self) -> None:
    """A well-formed member yields components and parameters."""
    parsed = signing.parse_signature_input(
      'sig1=("@method" "content-digest");created=1;keyid="abc"'
    )
    self.assertEqual(
      parsed["sig1"]["components"], ["@method", "content-digest"]
    )
    self.assertEqual(parsed["sig1"]["params"]["keyid"], "abc")

  def test_multiple_labels(self) -> None:
    """Multiple comma-separated members are all parsed."""
    parsed = signing.parse_signature_input(
      'a=("@method");keyid="x", b=("@path");keyid="y"'
    )
    self.assertEqual(set(parsed), {"a", "b"})

  def test_signature_decodes_base64(self) -> None:
    """A Signature member decodes to raw bytes."""
    raw = base64.b64encode(b"hello").decode("ascii")
    parsed = signing.parse_signature(f"sig1=:{raw}:")
    self.assertEqual(parsed["sig1"], b"hello")

  def test_malformed_returns_none(self) -> None:
    """Malformed inputs parse to None rather than raising."""
    self.assertIsNone(signing.parse_signature_input("not a signature input"))
    self.assertIsNone(signing.parse_signature(""))


class CoverageGateTest(absltest.TestCase):
  """The UCP required-component coverage table."""

  def test_get_no_body(self) -> None:
    """A bodyless GET requires only the target components."""
    self.assertEqual(
      signing.required_components("GET", False, {}, False),
      ["@method", "@authority", "@path"],
    )

  def test_post_with_body_requires_digest_and_type(self) -> None:
    """A bodied request must cover content-digest and content-type."""
    required = signing.required_components("POST", False, {}, True)
    self.assertIn("content-digest", required)
    self.assertIn("content-type", required)

  def test_query_present(self) -> None:
    """A query string adds @query."""
    self.assertIn("@query", signing.required_components("GET", True, {}, False))

  def test_idempotency_key_header_on_get(self) -> None:
    """Coverage keys on header presence: a GET with the header covers it."""
    required = signing.required_components(
      "GET", False, {"idempotency-key": "x"}, False
    )
    self.assertIn("idempotency-key", required)

  def test_ucp_agent_and_signature_agent(self) -> None:
    """Present ucp-agent / signature-agent headers must be covered."""
    required = signing.required_components(
      "GET", False, {"ucp-agent": "a", "signature-agent": "b"}, False
    )
    self.assertIn("ucp-agent", required)
    self.assertIn("signature-agent", required)

  def test_alg_param_rejected_by_verify_request(self) -> None:
    """A signature carrying an alg parameter is rejected (spec MUST NOT)."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k")
    add = signing.sign_request(
      key,
      "k",
      "GET",
      "https://h/p",
      {"UCP-Agent": 'profile="https://a/p"'},
      b"",
    )
    add["Signature-Input"] = add["Signature-Input"].replace(
      ";created", ';alg="ecdsa-p256-sha256";created'
    )
    headers = {
      "ucp-agent": 'profile="https://a/p"',
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request("GET", "h", "/p", "", headers, b"", [jwk])
    self.assertEqual(ctx.exception.code, "signature_invalid")


class SsrfGuardTest(absltest.TestCase):
  """Profile-URL transport and SSRF guards."""

  def test_http_rejected_without_carveout(self) -> None:
    """Plain http is rejected unless the insecure carve-out is set."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing._assert_profile_url_allowed("http://example.com/p", False)
    self.assertEqual(ctx.exception.code, "invalid_profile_url")

  def test_metadata_address_rejected(self) -> None:
    """The cloud metadata address is rejected."""
    with self.assertRaises(signing.SignatureError):
      signing._assert_profile_url_allowed(
        "https://169.254.169.254/latest", False
      )

  def test_loopback_and_private_rejected(self) -> None:
    """Loopback and RFC 1918 hosts are rejected without the carve-out."""
    for url in ("https://127.0.0.1/p", "https://10.0.0.5/p"):
      with self.assertRaises(signing.SignatureError):
        signing._assert_profile_url_allowed(url, False)

  def test_credentials_rejected(self) -> None:
    """A URL carrying userinfo is rejected."""
    with self.assertRaises(signing.SignatureError):
      signing._assert_profile_url_allowed("https://u:p@example.com/p", False)

  def test_loopback_allowed_with_carveout(self) -> None:
    """The carve-out permits http loopback for localhost demos."""
    signing._assert_profile_url_allowed("http://127.0.0.1:8285/p", True)


class ProfileFetchTest(absltest.TestCase):
  """Key discovery from a signer profile, using a mocked transport."""

  def setUp(self) -> None:
    """Clear the key cache before each fetch test."""
    super().setUp()
    signing.clear_key_cache()

  def _fetch(self, handler) -> list:
    """Run fetch_signing_keys against a mocked httpx transport."""
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
      kwargs["transport"] = httpx.MockTransport(handler)
      kwargs.pop("follow_redirects", None)
      return real_client(*args, follow_redirects=False, **kwargs)

    signing.httpx.AsyncClient = factory
    try:
      import asyncio

      return asyncio.run(
        signing.fetch_signing_keys(
          "https://agent.example/p", allow_insecure=True
        )
      )
    finally:
      signing.httpx.AsyncClient = real_client

  def test_reads_signing_keys(self) -> None:
    """signing_keys is read from the ucp envelope."""
    keys = self._fetch(
      lambda req: httpx.Response(
        200, json={"ucp": {"signing_keys": [{"kid": "a"}]}}
      )
    )
    self.assertEqual(keys[0]["kid"], "a")

  def test_keys_fallback(self) -> None:
    """A top-level keys array is read when signing_keys is absent."""
    keys = self._fetch(
      lambda req: httpx.Response(200, json={"keys": [{"kid": "b"}]})
    )
    self.assertEqual(keys[0]["kid"], "b")

  def test_redirect_is_unreachable(self) -> None:
    """A 3xx response is treated as unreachable (no redirects allowed)."""
    with self.assertRaises(signing.SignatureError) as ctx:
      self._fetch(
        lambda req: httpx.Response(302, headers={"location": "https://x/y"})
      )
    self.assertEqual(ctx.exception.code, "profile_unreachable")

  def test_non_json_is_malformed(self) -> None:
    """A non-JSON body yields profile_malformed."""
    with self.assertRaises(signing.SignatureError) as ctx:
      self._fetch(lambda req: httpx.Response(200, text="not json"))
    self.assertEqual(ctx.exception.code, "profile_malformed")

  def test_keyless_is_malformed(self) -> None:
    """A profile with no keys yields profile_malformed."""
    with self.assertRaises(signing.SignatureError) as ctx:
      self._fetch(lambda req: httpx.Response(200, json={"ucp": {}}))
    self.assertEqual(ctx.exception.code, "profile_malformed")


class DifferentialLibraryTest(absltest.TestCase):
  """Cross-check against the independent http-message-signatures library."""

  def test_es256_both_directions(self) -> None:
    """Our ES256 signature and the library's verify each other."""
    from http_message_signatures.algorithms import ECDSA_P256_SHA256

    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k")
    alg = ECDSA_P256_SHA256(private_key=key, public_key=key.public_key())
    alg.verify(signing._raw_sign(key, RFC_B26_BASE), RFC_B26_BASE)
    signing.verify_raw_signature(jwk, RFC_B26_BASE, alg.sign(RFC_B26_BASE))

  def test_ed25519_both_directions(self) -> None:
    """Our Ed25519 signature and the library's verify each other."""
    from http_message_signatures.algorithms import ED25519

    key = ed25519.Ed25519PrivateKey.generate()
    jwk = signing.jwk_from_public_key(key.public_key(), "e")
    alg = ED25519(private_key=key, public_key=key.public_key())
    alg.verify(signing._raw_sign(key, RFC_B26_BASE), RFC_B26_BASE)
    signing.verify_raw_signature(jwk, RFC_B26_BASE, alg.sign(RFC_B26_BASE))


if __name__ == "__main__":
  absltest.main()
