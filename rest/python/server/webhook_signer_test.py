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

"""Unit tests for the business webhook-signing identity.

The reference server signs outbound order-event webhooks as the business
(order.md, Webhook Signature Verification). These tests pin the key
lifecycle: an out-of-the-box ephemeral demo key, deterministic RFC 7638
thumbprint kids, and ``--webhook_signing_key`` loading an operator-provided
PEM (ES256 or Ed25519). No private-key files are committed; all key material
is generated at runtime.
"""

import pathlib
import tempfile

from absl import flags
from absl.testing import absltest
import config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
import ucp_signing
import webhook_signer


def _pem(private_key) -> bytes:
  """Serialize a private key as unencrypted PKCS#8 PEM."""
  return private_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
  )


class WebhookSignerTest(absltest.TestCase):
  """Key loading, kid derivation, and profile JWK export."""

  def setUp(self) -> None:
    """Parse flags and clear any cached signing identity."""
    super().setUp()
    flags.FLAGS(["test"])
    config.FLAGS.webhook_signing_key = None
    webhook_signer.reset()

  def tearDown(self) -> None:
    """Restore the default key configuration."""
    config.FLAGS.webhook_signing_key = None
    webhook_signer.reset()
    super().tearDown()

  def test_default_is_ephemeral_p256_singleton(self) -> None:
    """Without the flag, one ES256 demo key is generated and reused."""
    key1, kid1 = webhook_signer.signing_key()
    key2, kid2 = webhook_signer.signing_key()
    self.assertIsInstance(key1, ec.EllipticCurvePrivateKey)
    self.assertIs(key1, key2)
    self.assertEqual(kid1, kid2)
    self.assertNotEmpty(kid1)

  def test_public_jwk_matches_signing_key(self) -> None:
    """The published JWK is the signing key's public half, same kid."""
    key, kid = webhook_signer.signing_key()
    jwk = webhook_signer.public_jwk()
    self.assertEqual(jwk["kid"], kid)
    self.assertEqual(jwk["kty"], "EC")
    self.assertEqual(jwk["crv"], "P-256")
    expected = ucp_signing.jwk_from_public_key(key.public_key(), kid)
    self.assertEqual(jwk, expected)

  def test_flag_loads_p256_pem(self) -> None:
    """--webhook_signing_key loads an operator EC P-256 PEM key."""
    provided = ec.generate_private_key(ec.SECP256R1())
    path = pathlib.Path(tempfile.mkdtemp()) / "key.pem"
    path.write_bytes(_pem(provided))
    config.FLAGS.webhook_signing_key = str(path)
    webhook_signer.reset()
    key, _ = webhook_signer.signing_key()
    self.assertEqual(
      key.private_numbers().private_value,
      provided.private_numbers().private_value,
    )

  def test_flag_loads_ed25519_pem(self) -> None:
    """--webhook_signing_key loads an Ed25519 PEM key; JWK is OKP."""
    provided = ed25519.Ed25519PrivateKey.generate()
    path = pathlib.Path(tempfile.mkdtemp()) / "key.pem"
    path.write_bytes(_pem(provided))
    config.FLAGS.webhook_signing_key = str(path)
    webhook_signer.reset()
    key, _ = webhook_signer.signing_key()
    self.assertIsInstance(key, ed25519.Ed25519PrivateKey)
    self.assertEqual(webhook_signer.public_jwk()["kty"], "OKP")

  def test_kid_is_deterministic_for_a_given_key(self) -> None:
    """The kid is the RFC 7638 JWK thumbprint: stable across restarts.

    Reloading the same PEM must republish the same kid, so platforms that
    cache the profile keep resolving the key after a server restart.
    """
    provided = ec.generate_private_key(ec.SECP256R1())
    path = pathlib.Path(tempfile.mkdtemp()) / "key.pem"
    path.write_bytes(_pem(provided))
    config.FLAGS.webhook_signing_key = str(path)
    webhook_signer.reset()
    _, kid_first = webhook_signer.signing_key()
    webhook_signer.reset()
    _, kid_second = webhook_signer.signing_key()
    self.assertEqual(kid_first, kid_second)

  def test_unreadable_key_file_fails_loudly(self) -> None:
    """A bad key path is a configuration error, never a silent fallback.

    The operator asked for a specific signing identity; silently generating
    an ephemeral key instead would sign as a different identity than the one
    configured.
    """
    config.FLAGS.webhook_signing_key = "/nonexistent/key.pem"
    webhook_signer.reset()
    with self.assertRaises(OSError):
      webhook_signer.signing_key()


if __name__ == "__main__":
  absltest.main()
