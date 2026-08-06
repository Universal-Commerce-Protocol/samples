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

"""The business's webhook-signing identity.

Order-event webhooks MUST be signed by the business (order.md, Webhook
Signature Verification) with a key the business publishes in its profile's
``signing_keys[]`` so platforms can verify the deliveries. This module owns
that identity:

* ``--webhook_signing_key`` loads an operator-provided PEM private key
  (EC P-256 for ES256, or Ed25519). When unset, an ephemeral demo key is
  generated at startup -- the server signs correctly out of the box and no
  private-key file ever lives in the repository.
* The ``kid`` is the RFC 7638 JWK thumbprint of the public key, so the same
  key always republishes under the same identifier across restarts.
"""

import base64
import hashlib
import json
import pathlib

import config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric import ed25519
import ucp_signing

# The lazily-created (private key, kid) signing identity for this process.
_SIGNER: tuple | None = None


def signing_key() -> tuple:
  """Return the ``(private_key, kid)`` this business signs webhooks with.

  Loaded once per process: from the ``--webhook_signing_key`` PEM when
  configured, otherwise a fresh ephemeral ES256 demo key. A configured path
  that cannot be read or holds an unsupported key type fails loudly --
  silently signing with a different identity than the operator configured
  would be wrong.

  Returns:
    A tuple of the private key object and its RFC 7638 thumbprint kid.

  Raises:
    OSError: When the configured key file cannot be read.
    ValueError: When the file is not a supported private key (EC P-256 or
      Ed25519).

  """
  global _SIGNER
  if _SIGNER is None:
    path = config.FLAGS.webhook_signing_key
    if path:
      pem = pathlib.Path(path).read_bytes()
      key = serialization.load_pem_private_key(pem, password=None)
      if isinstance(key, ec.EllipticCurvePrivateKey):
        if not isinstance(key.curve, ec.SECP256R1):
          raise ValueError(
            "--webhook_signing_key must be EC P-256 (ES256) or Ed25519; "
            f"got EC curve {key.curve.name}"
          )
      elif not isinstance(key, ed25519.Ed25519PrivateKey):
        raise ValueError(
          "--webhook_signing_key must be EC P-256 (ES256) or Ed25519; "
          f"got {type(key).__name__}"
        )
    else:
      key = ec.generate_private_key(ec.SECP256R1())
    _SIGNER = (key, _thumbprint_kid(key.public_key()))
  return _SIGNER


def public_jwk() -> dict:
  """Return the public JWK to publish in the profile's ``signing_keys[]``."""
  key, kid = signing_key()
  return ucp_signing.jwk_from_public_key(key.public_key(), kid)


def reset() -> None:
  """Discard the cached signing identity (used by tests)."""
  global _SIGNER
  _SIGNER = None


def _thumbprint_kid(public_key) -> str:
  """Derive the RFC 7638 JWK thumbprint (base64url SHA-256) as the kid.

  The thumbprint hashes only the REQUIRED public members in lexicographic
  order with no whitespace, so it is deterministic for a given key.
  """
  jwk = ucp_signing.jwk_from_public_key(public_key, kid="")
  if jwk["kty"] == "OKP":
    members = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]}
  else:
    members = {
      "crv": jwk["crv"],
      "kty": jwk["kty"],
      "x": jwk["x"],
      "y": jwk["y"],
    }
  canonical = json.dumps(members, separators=(",", ":"), sort_keys=True)
  digest = hashlib.sha256(canonical.encode("utf-8")).digest()
  return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
