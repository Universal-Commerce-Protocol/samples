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

"""Discovery routes for the UCP server."""

import json
import pathlib
import uuid
from fastapi import APIRouter
from fastapi import Request
from fastapi import Response
import webhook_signer

router = APIRouter()

PROFILE_TEMPLATE_PATH = pathlib.Path(__file__).parent / "discovery_profile.json"

# Profiles are stable, non-sensitive documents; the spec requires a cacheable
# response (overview.md, Discovery: profile caching): `public` with `max-age`
# of at least 60 seconds, and never `private`/`no-store`/`no-cache`.
PROFILE_CACHE_CONTROL = "public, max-age=3600"

# Generate a unique shop ID for this server instance
SHOP_ID = str(uuid.uuid4())


@router.get(
  "/.well-known/ucp",
  response_model=dict,
  summary="Get Merchant Profile",
)
async def get_merchant_profile(request: Request, response: Response):
  """Return the merchant profile and capabilities."""
  response.headers["Cache-Control"] = PROFILE_CACHE_CONTROL
  # Read template and perform simple substitution
  with PROFILE_TEMPLATE_PATH.open(encoding="utf-8") as f:
    template = f.read()

  # Replace placeholders
  profile_json = template.replace(
    "{{ENDPOINT}}", str(request.base_url).rstrip("/")
  ).replace("{{SHOP_ID}}", SHOP_ID)

  profile_data = json.loads(profile_json)

  # Preserve the spec-required top-level `ucp` wrapper. The UCP discovery
  # profile schema (discovery/profile.json) defines `$defs.base.required =
  # ["ucp"]`, so the served body MUST be `{"ucp": {...}}`. Default
  # payment_handlers INSIDE the ucp object rather than at the document root.
  ucp = profile_data.setdefault("ucp", {})
  ucp.setdefault("payment_handlers", [])

  # Publish the webhook-signing public key so platforms can verify our
  # order-event deliveries (order.md, Webhook Signature Verification /
  # signatures.md, Key Discovery). source/discovery/profile_schema.json
  # $defs/base at the 2026-04-08 pin this server declares
  # (config.get_server_version()) requires `ucp` and separately declares
  # `signing_keys` as a top-level sibling of `ucp` -- that schema defines no
  # `keys` field anywhere, nested or otherwise, so publish signing_keys[]
  # only. ucp#566 renames this field to a top-level keys[] for 2026-08-25
  # and later; when this server's declared version moves to that pin, this
  # field name must move with it in the same change, together with
  # ucp_signing.py's _extract_keys().
  jwk = webhook_signer.public_jwk()
  profile_data.setdefault("signing_keys", []).append(jwk)

  return profile_data
