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
import time

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

  def test_ed25519_full_verify_request_roundtrip(self) -> None:
    """An Ed25519-signed request verifies through the full verify_request."""
    key = ed25519.Ed25519PrivateKey.generate()
    jwk = signing.jwk_from_public_key(key.public_key(), "ed-k")
    add = signing.sign_request(
      key, "ed-k", "GET", "https://m.example/p", {}, b""
    )
    headers = {
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    keyid = signing.verify_request(
      "GET", "m.example", "/p", "", headers, b"", [jwk]
    )
    self.assertEqual(keyid, "ed-k")


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

  def test_ucp_agent_covered_signature_agent_out_of_scope(self) -> None:
    """A present ucp-agent header must be covered; signature-agent is not.

    signature-agent is a WBA-shape component (component parameters /
    tag=web-bot-auth) that this default-UCP verifier does not parse, so it is
    deliberately outside the coverage gate: the module's promise matches what
    it can actually verify.
    """
    required = signing.required_components(
      "GET", False, {"ucp-agent": "a", "signature-agent": "b"}, False
    )
    self.assertIn("ucp-agent", required)
    self.assertNotIn("signature-agent", required)

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

  def test_reads_keys_from_ucp_envelope(self) -> None:
    """keys[] (canonical per ucp#566) is read from the ucp envelope."""
    keys = self._fetch(
      lambda req: httpx.Response(200, json={"ucp": {"keys": [{"kid": "a"}]}})
    )
    self.assertEqual(keys[0]["kid"], "a")

  def test_reads_top_level_keys(self) -> None:
    """A top-level keys[] array (no ucp wrapper) is read."""
    keys = self._fetch(
      lambda req: httpx.Response(200, json={"keys": [{"kid": "b"}]})
    )
    self.assertEqual(keys[0]["kid"], "b")

  def test_legacy_signing_keys_is_not_read(self) -> None:
    """A profile with only the removed signing_keys[] resolves to no keys.

    The reference verifier models the merged spec (keys[] only, ucp#566).
    """
    with self.assertRaises(signing.SignatureError) as ctx:
      self._fetch(
        lambda req: httpx.Response(
          200, json={"ucp": {"signing_keys": [{"kid": "old"}]}}
        )
      )
    self.assertEqual(ctx.exception.code, "profile_malformed")

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


class NormalizationTest(absltest.TestCase):
  """Verify-side normalization must match the signer's canonical base."""

  def _signed_get(self, url: str):
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    add = signing.sign_request(key, "k1", "GET", url, {}, b"")
    headers = {
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    return jwk, headers

  def test_authority_default_port_is_stripped(self) -> None:
    """The default port is removed per RFC 9421 Section 2.2.3.

    A signer that signs `host` still verifies when the server sees `host:443`.
    """
    jwk, headers = self._signed_get("https://merchant.example/p")
    keyid = signing.verify_request(
      "GET", "merchant.example:443", "/p", "", headers, b"", [jwk]
    )
    self.assertEqual(keyid, "k1")

  def test_empty_path_normalized_to_slash(self) -> None:
    """An empty path is the same as `/` on both sides (RFC 9421 2.2.6)."""
    jwk, headers = self._signed_get("https://merchant.example/")
    keyid = signing.verify_request(
      "GET", "merchant.example", "", "", headers, b"", [jwk]
    )
    self.assertEqual(keyid, "k1")

  def test_field_value_ows_is_trimmed(self) -> None:
    """Covered field values are OWS-trimmed per RFC 9421 Section 2.1.

    Leading or trailing whitespace on a header must not break verification.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    body = b'{"x":1}'
    add = signing.sign_request(
      key,
      "k1",
      "POST",
      "https://m.example/o",
      {"content-type": "application/json"},
      body,
    )
    headers = {
      "content-type": "  application/json  ",  # padded OWS
      "content-digest": add["Content-Digest"],
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    keyid = signing.verify_request(
      "POST", "m.example", "/o", "", headers, body, [jwk]
    )
    self.assertEqual(keyid, "k1")


class DigestMatchingTest(absltest.TestCase):
  """content_digest_matches rejects every malformed Content-Digest form."""

  def test_member_not_colon_wrapped(self) -> None:
    """A sha-256 member whose value is not :base64: is rejected."""
    self.assertFalse(signing.content_digest_matches("sha-256=abc", b"x"))

  def test_bad_base64_value(self) -> None:
    """A sha-256 member with undecodable base64 is rejected, not raised."""
    self.assertFalse(signing.content_digest_matches("sha-256=:@@@:", b"x"))

  def test_no_sha256_member(self) -> None:
    """A digest header without a sha-256 member does not match."""
    self.assertFalse(signing.content_digest_matches("md5=:AA==:", b"x"))


class SfEscapeTest(absltest.TestCase):
  """The structured-field splitter honours backslash escapes in strings."""

  def test_escaped_quote_inside_string(self) -> None:
    """A separator inside an escaped quoted string is not a split point."""
    parts = signing._sf_split(r'"a\"b,c" , "d"', ",")
    self.assertEqual(parts, [r'"a\"b,c"', '"d"'])


class ParserRejectionTest(absltest.TestCase):
  """Malformed Signature-Input / Signature headers return None."""

  def test_member_without_equals(self) -> None:
    """A member with no '=' is malformed."""
    self.assertIsNone(signing.parse_signature_input("sig1"))

  def test_component_not_quoted(self) -> None:
    """An unquoted component token is malformed."""
    self.assertIsNone(signing.parse_signature_input("sig1=(@method)"))

  def test_signature_member_without_equals(self) -> None:
    """A Signature member with no '=' is malformed."""
    self.assertIsNone(signing.parse_signature("sig1"))

  def test_signature_value_not_colon_wrapped(self) -> None:
    """A Signature value that is not :base64: is malformed."""
    self.assertIsNone(signing.parse_signature("sig1=abc"))

  def test_signature_bad_base64(self) -> None:
    """A Signature value with undecodable base64 is malformed."""
    self.assertIsNone(signing.parse_signature("sig1=:@@@:"))


class JwkErrorTest(absltest.TestCase):
  """public_key_from_jwk maps malformed / unsupported keys to spec codes."""

  def test_malformed_ec_jwk(self) -> None:
    """An EC JWK missing its y coordinate is signature_invalid."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.public_key_from_jwk({"kty": "EC", "crv": "P-256", "x": "AA"})
    self.assertEqual(ctx.exception.code, "signature_invalid")

  def test_unsupported_kty(self) -> None:
    """An RSA JWK is algorithm_unsupported."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.public_key_from_jwk({"kty": "RSA", "n": "AA", "e": "AQAB"})
    self.assertEqual(ctx.exception.code, "algorithm_unsupported")


class AuthorityHttpPortTest(absltest.TestCase):
  """_authority strips the http default port as well."""

  def test_strip_port_80(self) -> None:
    """host:80 normalises to host."""
    self.assertEqual(signing._authority("Host.Example:80"), "host.example")


class QueryAndUnresolvedTest(absltest.TestCase):
  """@query round-trips through verify; unresolvable coverage fails cleanly."""

  def test_query_signed_and_verified(self) -> None:
    """A signed request with a query string verifies (exercises @query)."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    add = signing.sign_request(
      key, "k1", "GET", "https://m.example/p?a=1", {}, b""
    )
    headers = {
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    keyid = signing.verify_request(
      "GET", "m.example", "/p", "a=1", headers, b"", [jwk]
    )
    self.assertEqual(keyid, "k1")

  def test_covered_component_absent_on_verify(self) -> None:
    """A signature covering a header absent at verify time is invalid."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    # Hand-craft a Signature-Input covering a header the verifier won't have.
    raw = '("@method" "@authority" "@path" "x-custom");created=1;keyid="k1"'

    def resolve(name: str):
      table = {
        "@method": "GET",
        "@authority": "m.example",
        "@path": "/p",
        "x-custom": "v",
      }
      return table.get(name)

    base = signing.build_signature_base(
      ["@method", "@authority", "@path", "x-custom"], raw, resolve
    )
    sig = signing._raw_sign(key, base)
    headers = {
      "signature-input": f"sig1={raw}",
      "signature": "sig1=:" + base64.b64encode(sig).decode() + ":",
    }
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk])
    self.assertEqual(ctx.exception.code, "signature_invalid")


class ExtractKeysTest(absltest.TestCase):
  """_extract_keys reads keys[] (canonical per ucp#566) and tolerates junk."""

  def test_non_dict_document(self) -> None:
    """A non-object profile yields no keys, not an error."""
    self.assertEqual(signing._extract_keys(["not", "a", "dict"]), [])

  def test_reads_canonical_keys(self) -> None:
    """keys[] under the ucp envelope is the canonical source."""
    doc = {"ucp": {"keys": [{"kid": "k"}]}}
    self.assertEqual(signing._extract_keys(doc), [{"kid": "k"}])

  def test_removed_signing_keys_is_ignored(self) -> None:
    """The removed signing_keys[] field is not read (ucp#566)."""
    doc = {"ucp": {"signing_keys": [{"kid": "old"}]}}
    self.assertEqual(signing._extract_keys(doc), [])


class SigCapableTest(absltest.TestCase):
  """Signature-capable key filtering (ucp#566).

  The verifier resolves keyid only among keys usable for verification, skipping
  use:enc / key_ops-without-verify per RFC 7517 Sections 4.2 and 4.3.
  """

  def _signed(self, jwk_extra: dict):
    """Sign a GET with a fresh key; return (published_jwk, headers)."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    jwk = {**jwk, **jwk_extra}
    add = signing.sign_request(key, "k1", "GET", "https://m.example/p", {}, b"")
    headers = {
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }
    return jwk, headers

  def test_use_sig_key_verifies(self) -> None:
    """A key marked use:"sig" is signature-capable and verifies."""
    jwk, headers = self._signed({"use": "sig"})
    self.assertEqual(
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk]),
      "k1",
    )

  def test_use_absent_key_verifies(self) -> None:
    """A key with no `use` member is signature-capable (use is OPTIONAL)."""
    jwk, headers = self._signed({})
    jwk.pop("use", None)
    self.assertEqual(
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk]),
      "k1",
    )

  def test_use_enc_key_is_skipped(self) -> None:
    """A use:"enc" key with the matching kid is not used; key_not_found."""
    jwk, headers = self._signed({"use": "enc"})
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk])
    self.assertEqual(ctx.exception.code, "key_not_found")

  def test_key_ops_without_verify_is_skipped(self) -> None:
    """A key whose key_ops is present but omits "verify" is skipped."""
    jwk, headers = self._signed({"key_ops": ["encrypt", "decrypt"]})
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk])
    self.assertEqual(ctx.exception.code, "key_not_found")

  def test_key_ops_with_verify_is_capable(self) -> None:
    """A key whose key_ops includes "verify" is signature-capable."""
    jwk, headers = self._signed({"key_ops": ["verify"]})
    self.assertEqual(
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk]),
      "k1",
    )


class KeyCacheTest(absltest.TestCase):
  """fetch_signing_keys serves a cached result on the second call."""

  def test_second_call_is_cached(self) -> None:
    """A fresh cache entry is returned without any network fetch."""
    import asyncio

    signing.clear_key_cache()
    jwk = {"kty": "EC", "crv": "P-256", "kid": "k", "x": "AA", "y": "AA"}
    url = "https://signer.example/.well-known/ucp"
    signing._KEY_CACHE[url] = (time.time() + 300, [jwk])
    keys = asyncio.run(signing.fetch_signing_keys(url, allow_insecure=False))
    self.assertEqual(keys, [jwk])
    signing.clear_key_cache()


class SsrfResolveTest(absltest.TestCase):
  """Profile-URL host vetting: resolve failures, hostless URLs, public pass."""

  def test_unresolvable_host(self) -> None:
    """A DNS failure on the profile host is profile_unreachable (424)."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing._assert_profile_url_allowed(
        "https://nonexistent.invalid.example./x", allow_insecure=False
      )
    self.assertEqual(ctx.exception.code, "profile_unreachable")

  def test_hostless_url_rejected(self) -> None:
    """A URL with no host is invalid_profile_url."""
    with self.assertRaises(signing.SignatureError) as ctx:
      signing._assert_profile_url_allowed("https:///x", allow_insecure=False)
    self.assertEqual(ctx.exception.code, "invalid_profile_url")

  def test_public_host_allowed(self) -> None:
    """A host resolving to a public address passes the SSRF guard."""
    import socket
    from unittest import mock

    infos = [(socket.AF_INET, None, None, "", ("93.184.216.34", 443))]
    with mock.patch.object(socket, "getaddrinfo", return_value=infos):
      signing._assert_profile_url_allowed(
        "https://public.example/.well-known/ucp", allow_insecure=False
      )


class BodyWithoutDigestTest(absltest.TestCase):
  """A bodied request whose Content-Digest header is absent is rejected."""

  def test_body_without_content_digest_rejected(self) -> None:
    """Signing covers content-digest; dropping the header fails verification."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    body = b'{"x":1}'
    add = signing.sign_request(
      key,
      "k1",
      "POST",
      "https://m.example/o",
      {"content-type": "application/json"},
      body,
    )
    headers = {
      "content-type": "application/json",
      "signature-input": add["Signature-Input"],
      "signature": add["Signature"],
    }  # Content-Digest deliberately omitted
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request(
        "POST", "m.example", "/o", "", headers, body, [jwk]
      )
    self.assertEqual(ctx.exception.code, "digest_mismatch")


class VerifyMissingSignatureTest(absltest.TestCase):
  """verify_request handles a present-but-unusable signature header set."""

  def test_malformed_input_is_signature_missing(self) -> None:
    """A malformed Signature-Input (parses to None) yields signature_missing."""
    headers = {"signature-input": "garbage", "signature": "sig1=:AA==:"}
    with self.assertRaises(signing.SignatureError) as ctx:
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [])
    self.assertEqual(ctx.exception.code, "signature_missing")

  def test_label_without_matching_signature_is_skipped(self) -> None:
    """A label with no matching Signature member is skipped; request fails."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    add = signing.sign_request(key, "k1", "GET", "https://m.example/p", {}, b"")
    # Relabel Signature-Input to sig2 while Signature stays sig1: no match.
    headers = {
      "signature-input": add["Signature-Input"].replace("sig1=", "sig2=", 1),
      "signature": add["Signature"],
    }
    with self.assertRaises(signing.SignatureError):
      signing.verify_request("GET", "m.example", "/p", "", headers, b"", [jwk])


class SfSplitEdgeTest(absltest.TestCase):
  """_sf_split trailing-separator and empty-tail handling."""

  def test_trailing_separator_has_no_empty_tail(self) -> None:
    """A trailing separator does not emit an empty final segment."""
    self.assertEqual(signing._sf_split("a,", ","), ["a"])

  def test_empty_input_returns_empty(self) -> None:
    """An empty string splits to no segments."""
    self.assertEqual(signing._sf_split("", ","), [])


class ParseEmptyTest(absltest.TestCase):
  """parse_signature_input guards empty and non-string input."""

  def test_empty_string(self) -> None:
    """An empty header parses to None."""
    self.assertIsNone(signing.parse_signature_input(""))


class ExtraComponentsTest(absltest.TestCase):
  """sign_request can cover caller-requested headers beyond the UCP minimum.

  RFC 9421 lets a signer cover any component; the UCP table is the required
  floor. Webhook deliveries use this to bind the Standard Webhooks headers
  (Webhook-Id, Webhook-Timestamp) into the signature.
  """

  def test_extra_components_are_covered_and_verify(self) -> None:
    """Requested present headers join the signed set; the result verifies."""
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = signing.jwk_from_public_key(key.public_key(), "k1")
    headers = {
      "UCP-Agent": 'profile="https://m.example/.well-known/ucp"',
      "Idempotency-Key": "evt-1",
      "Webhook-Id": "evt-1",
      "Webhook-Timestamp": "1700000000",
    }
    body = b'{"id":"ord_1"}'
    add = signing.sign_request(
      key,
      "k1",
      "POST",
      "https://platform.example/hook?token=t",
      headers,
      body,
      extra_components=("webhook-id", "webhook-timestamp"),
    )
    parsed = signing.parse_signature_input(add["Signature-Input"])
    components = parsed["sig1"]["components"]
    self.assertIn("webhook-id", components)
    self.assertIn("webhook-timestamp", components)
    # The UCP required floor is still fully covered.
    for required in (
      "@method",
      "@authority",
      "@path",
      "@query",
      "content-digest",
      "content-type",
      "idempotency-key",
      "ucp-agent",
    ):
      self.assertIn(required, components)
    merged = {k.lower(): v for k, v in {**headers, **add}.items()}
    keyid = signing.verify_request(
      "POST", "platform.example", "/hook", "token=t", merged, body, [jwk]
    )
    self.assertEqual(keyid, "k1")

  def test_absent_extra_component_is_skipped(self) -> None:
    """An extra component whose header is absent is not declared as signed."""
    key = ec.generate_private_key(ec.SECP256R1())
    add = signing.sign_request(
      key,
      "k1",
      "GET",
      "https://m.example/p",
      {},
      b"",
      extra_components=("webhook-id",),
    )
    parsed = signing.parse_signature_input(add["Signature-Input"])
    self.assertNotIn("webhook-id", parsed["sig1"]["components"])

  def test_extra_component_never_duplicates_required(self) -> None:
    """A requested component already in the required set appears once."""
    key = ec.generate_private_key(ec.SECP256R1())
    headers = {"UCP-Agent": 'profile="https://m.example/.well-known/ucp"'}
    add = signing.sign_request(
      key,
      "k1",
      "GET",
      "https://m.example/p",
      headers,
      b"",
      extra_components=("ucp-agent",),
    )
    parsed = signing.parse_signature_input(add["Signature-Input"])
    self.assertEqual(parsed["sig1"]["components"].count("ucp-agent"), 1)


class ParseParenDepthTest(absltest.TestCase):
  """The component-list paren scanner handles nested and unbalanced parens."""

  def test_nested_parens_are_balanced(self) -> None:
    """Balanced inner parens drive depth >1 then back without breaking early.

    RFC 9421 component identifiers never contain '(' (they are @-derived names
    or lowercase field names), so this only exercises the scanner's depth
    accounting on adversarial input: it must find the true closing paren.
    """
    parsed = signing.parse_signature_input('sig1=("@method" "@path");created=1')
    self.assertEqual(parsed["sig1"]["components"], ["@method", "@path"])
    # An embedded '(' (not valid per RFC 9421) confuses the naive scan; it must
    # degrade safely to no usable components, never crash or over-accept.
    embedded = signing.parse_signature_input('sig1=("a(b" "c");created=1')
    self.assertTrue(embedded is None or not embedded["sig1"]["components"])

  def test_unclosed_paren_yields_no_components(self) -> None:
    """An unbalanced '(' never returns depth 0; parsing does not crash."""
    parsed = signing.parse_signature_input('sig1=("a";created=1')
    self.assertTrue(parsed is None or not parsed["sig1"]["components"])


if __name__ == "__main__":
  absltest.main()
