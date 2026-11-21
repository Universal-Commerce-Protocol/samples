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

"""Tests that the discovery profile advertises every transport it serves."""

import json
import pathlib
import unittest

_PROFILE = pathlib.Path(__file__).parent / "routes" / "discovery_profile.json"


class DiscoveryProfileTest(unittest.TestCase):
  """Checks the shopping service entries of the discovery profile."""

  def setUp(self) -> None:
    """Load the raw profile template."""
    super().setUp()
    with _PROFILE.open(encoding="utf-8") as f:
      self.profile = json.load(f)

  def test_mcp_transport_is_advertised(self) -> None:
    """The server serves POST /mcp, so the profile must advertise it."""
    entries = self.profile["ucp"]["services"]["dev.ucp.shopping"]
    mcp = [e for e in entries if e["transport"] == "mcp"]
    self.assertEqual(len(mcp), 1)
    self.assertEqual(mcp[0]["endpoint"], "{{ENDPOINT}}/mcp")


if __name__ == "__main__":
  unittest.main()
