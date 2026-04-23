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

"""UCP endpoint resolution utilities.

Implements the Endpoint Resolution logic from the UCP specification:
https://ucp.dev/2026-04-08/specification/overview#endpoint-resolution

  "The endpoint field provides the base URL for API calls. OpenAPI paths
   are appended to this endpoint to form the complete URL."
"""


def resolve_rest_endpoint(discovery_data: dict) -> str | None:
  """Extract the REST endpoint from a UCP discovery response.

  Looks up ``services["dev.ucp.shopping"]`` in the discovery payload,
  finds the entry with ``transport == "rest"``, and returns its
  ``endpoint`` value.  All subsequent API paths (e.g.
  ``/checkout-sessions``) should be appended to this base URL.

  Args:
    discovery_data: Parsed JSON body from ``GET /.well-known/ucp``.

  Returns:
    The resolved endpoint URL, or ``None`` if no REST service was found.

  """
  shopping_services = discovery_data.get("services", {}).get(
    "dev.ucp.shopping", []
  )
  rest_service = next(
    (s for s in shopping_services if s.get("transport") == "rest"), None
  )
  if rest_service and rest_service.get("endpoint"):
    return rest_service["endpoint"]
  return None
