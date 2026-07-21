"""Unit tests for UCP version parsing."""

import datetime
import unittest

from exceptions import UcpVersionError
from ucp_version import parse_ucp_version


class UcpVersionTest(unittest.TestCase):
  """Tests parse_ucp_version behavior."""

  def test_parse_valid_date(self) -> None:
    parsed = parse_ucp_version("2026-01-23")
    self.assertEqual(parsed, datetime.date(2026, 1, 23))

  def test_parse_strips_whitespace(self) -> None:
    parsed = parse_ucp_version(" 2026-01-23 ")
    self.assertEqual(parsed, datetime.date(2026, 1, 23))

  def test_parse_rejects_non_string(self) -> None:
    with self.assertRaises(TypeError):
      parse_ucp_version(123)  # type: ignore[arg-type]

  def test_parse_rejects_invalid_format(self) -> None:
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026/01/23")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")

  def test_parse_rejects_invalid_calendar_date(self) -> None:
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026-02-30")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")

  def test_parse_rejects_datetime_format(self) -> None:
    with self.assertRaises(UcpVersionError) as exc:
      parse_ucp_version("2026-01-23T10:11:12Z")
    self.assertEqual(exc.exception.code, "VERSION_INVALID_FORMAT")


if __name__ == "__main__":
  unittest.main()
