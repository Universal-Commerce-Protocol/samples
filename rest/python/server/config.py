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

"""Shared configuration and startup logic for UCP servers."""

import contextlib
import json
from pathlib import Path
import uuid
from absl import flags
import db
from fastapi import FastAPI

FLAGS = flags.FLAGS

_SERVER_VERSION_CACHE = None

# checkout.json annotates `currency` with `ucp_request: omit` and describes
# it as "reflecting the merchant's market determination ... buyers provide
# signals, merchants determine currency". A conformant platform therefore does
# not send it, and the generated CheckoutCreateRequest has no such field. This
# sample serves a single market, so the determination is a constant.
DEFAULT_CURRENCY = "USD"


def get_default_currency() -> str:
  """Return the currency this business trades in."""
  return DEFAULT_CURRENCY


def get_server_version() -> str:
  """Read and cache the server version from the discovery profile."""
  global _SERVER_VERSION_CACHE
  if _SERVER_VERSION_CACHE:
    return _SERVER_VERSION_CACHE

  current_dir = Path(__file__).resolve().parent
  profile_path = current_dir / "routes" / "discovery_profile.json"

  with profile_path.open() as f:
    data = json.load(f)
    _SERVER_VERSION_CACHE = data["ucp"]["version"]
    return _SERVER_VERSION_CACHE


# Define flags only if they haven't been defined yet (to avoid duplicates
# during tests or re-imports)
try:
  flags.DEFINE_string("products_db_path", None, "Path to products DB")
  flags.DEFINE_string("transactions_db_path", None, "Path to transactions DB")
  flags.DEFINE_string(
    "simulation_secret",
    str(uuid.uuid4()),
    "Secret key for simulation endpoints",
  )
  flags.DEFINE_integer("port", None, "Port to run the server on")
  flags.DEFINE_boolean(
    "require_signatures",
    False,
    "Reject requests whose RFC 9421 signature is missing or invalid. When "
    "false (the default), signatures are still verified when present, but "
    "unsigned or invalid requests are allowed and only logged.",
  )
  flags.DEFINE_boolean(
    "allow_insecure_profile_urls",
    False,
    "Permit http and loopback/private UCP-Agent profile URLs when resolving "
    "signer keys. For localhost demos and CI only; never enable in "
    "production, as it disables SSRF protections.",
  )
  flags.DEFINE_string(
    "webhook_signing_key",
    None,
    "Path to a PEM private key (EC P-256 or Ed25519) used to sign outbound "
    "order-event webhooks as this business (order.md, Webhook Signature "
    "Verification). When unset, an ephemeral demo key is generated at "
    "startup; either way the public JWK is published in the served "
    "profile's signing_keys[].",
  )
  flags.DEFINE_integer(
    "webhook_delivery_attempts",
    3,
    "Total delivery attempts per order-event webhook (the initial attempt "
    "plus retries). order.md requires failed deliveries to be retried; the "
    "bound keeps the retry finite.",
    lower_bound=1,
  )
  flags.DEFINE_float(
    "webhook_retry_backoff_seconds",
    0.5,
    "Delay before the first webhook retry, doubling on each subsequent "
    "retry (exponential backoff).",
    lower_bound=0.0,
  )
except flags.DuplicateFlagError:
  pass


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
  """Shared lifespan manager for initializing databases."""
  del app  # Unused.
  # Load (and thereby validate) the webhook-signing identity up front: a
  # misconfigured --webhook_signing_key must abort the boot loudly, not
  # surface as a swallowed per-delivery error that silently degrades every
  # webhook. Imported lazily; webhook_signer imports this module.
  import webhook_signer

  webhook_signer.signing_key()
  # In tests or if flags aren't set, these might be None, handled by caller
  if FLAGS.products_db_path and FLAGS.transactions_db_path:
    await db.manager.init_dbs(
      FLAGS.products_db_path, FLAGS.transactions_db_path
    )
  yield
  await db.manager.close()
