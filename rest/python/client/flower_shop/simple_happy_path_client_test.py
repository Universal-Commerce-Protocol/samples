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

"""Tests for endpoint resolution in the happy path client.

Verifies that resolve_rest_endpoint correctly extracts the REST endpoint
from a UCP discovery response, per the spec's Endpoint Resolution section:
https://ucp.dev/2026-04-08/specification/overview#endpoint-resolution
"""

import unittest

from endpoint_resolution import resolve_rest_endpoint


class ResolveRestEndpointTest(unittest.TestCase):
  """Tests for resolve_rest_endpoint."""

  def test_returns_endpoint_with_path_prefix(self):
    """Merchant mounts API under a path prefix (the bug scenario)."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "rest",
            "endpoint": "https://merchant.example.com/buy/v1",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          }
        ]
      }
    }
    self.assertEqual(
      resolve_rest_endpoint(discovery),
      "https://merchant.example.com/buy/v1",
    )

  def test_returns_endpoint_at_root(self):
    """Merchant serves API at domain root (sample server scenario)."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "rest",
            "endpoint": "http://localhost:8182",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          }
        ]
      }
    }
    self.assertEqual(
      resolve_rest_endpoint(discovery),
      "http://localhost:8182",
    )

  def test_selects_rest_transport_among_multiple(self):
    """Discovery lists multiple transports; only REST is selected."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "mcp",
            "endpoint": "https://merchant.example.com/ucp/mcp",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json",
          },
          {
            "version": "2026-04-08",
            "transport": "rest",
            "endpoint": "https://merchant.example.com/api/v2",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          },
          {
            "version": "2026-04-08",
            "transport": "a2a",
            "endpoint": "https://merchant.example.com/.well-known/agent-card.json",
          },
        ]
      }
    }
    self.assertEqual(
      resolve_rest_endpoint(discovery),
      "https://merchant.example.com/api/v2",
    )

  def test_returns_none_when_no_services(self):
    """Discovery response has no services key at all."""
    discovery = {"payment_handlers": {}}
    self.assertIsNone(resolve_rest_endpoint(discovery))

  def test_returns_none_when_services_empty(self):
    """Discovery response has empty services."""
    discovery = {"services": {}}
    self.assertIsNone(resolve_rest_endpoint(discovery))

  def test_returns_none_when_no_rest_transport(self):
    """Shopping service exists but only non-REST transports are listed."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "mcp",
            "endpoint": "https://merchant.example.com/ucp/mcp",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json",
          }
        ]
      }
    }
    self.assertIsNone(resolve_rest_endpoint(discovery))

  def test_returns_none_when_rest_has_no_endpoint(self):
    """REST transport exists but endpoint field is missing."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "rest",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          }
        ]
      }
    }
    self.assertIsNone(resolve_rest_endpoint(discovery))

  def test_returns_none_when_endpoint_is_empty_string(self):
    """REST transport exists but endpoint is an empty string."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "rest",
            "endpoint": "",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          }
        ]
      }
    }
    self.assertIsNone(resolve_rest_endpoint(discovery))

  def test_handles_deeply_nested_path_prefix(self):
    """Endpoint has multiple path segments."""
    discovery = {
      "services": {
        "dev.ucp.shopping": [
          {
            "version": "2026-04-08",
            "transport": "rest",
            "endpoint": "https://api.merchant.com/ucp/shopping/v1",
            "schema": "https://ucp.dev/2026-04-08/services/shopping/rest.openapi.json",
          }
        ]
      }
    }
    self.assertEqual(
      resolve_rest_endpoint(discovery),
      "https://api.merchant.com/ucp/shopping/v1",
    )


if __name__ == "__main__":
  unittest.main()
