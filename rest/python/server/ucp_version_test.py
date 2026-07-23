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

"""Unit tests for UCP version parsing."""

import datetime
import unittest

from exceptions import UcpVersionError
from ucp_version import parse_ucp_version


class UcpVersionTest(unittest.TestCase):
  """Tests parse_ucp_version behavior."""

  def test_parse_valid_date(self) -> None:
    """Test parsing a valid YYYY-MM-DD date."""
    parsed = parse_ucp_version("2026-01-23")
    self.assertEqual(parsed, datetime.date(2026, 1, 23))

  def test_parse_strips_whitespace(self) -> None:
    """Test that leading/trailing whitespace is stripped before parsing."""
    parsed = parse_ucp_version(" 2026-01-23 ")
    self.assertEqual(parsed, datetime.date(2026, 1, 23))

  def test_parse_rejects_invalid_format(self) -> None:
    """Test that invalid formats raise UcpVersionError."""
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026/01/23")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")

  def test_parse_rejects_invalid_calendar_date(self) -> None:
    """Test that invalid calendar dates (e.g. Feb 30) raise UcpVersionError."""
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026-02-30")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")

  def test_parse_rejects_datetime_format(self) -> None:
    """Test that datetime formats (with time component) are rejected."""
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026-01-23T10:11:12Z")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")


if __name__ == "__main__":
  unittest.main()
