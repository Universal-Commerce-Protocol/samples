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

"""UCP version string parsing (YYYY-MM-DD)."""

import datetime
import re

from exceptions import UcpVersionError

_UCP_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_ucp_version(version: str) -> datetime.date:
  """Parse a UCP version string in YYYY-MM-DD format.

  Args:
    version: The version string to parse.

  Returns:
    A datetime.date representing the version.

  Raises:
    TypeError: If version is not a string.
    UcpVersionError: If the string is not a valid YYYY-MM-DD calendar date.
    No provision for other formats supported like YYYY-MM-DDTHH:MM:SSZ

  """
  if not isinstance(version, str):
    raise TypeError(f"Version must be a string, got {type(version).__name__}.")

  version = version.strip()
  if not _UCP_VERSION_RE.fullmatch(version):
    raise UcpVersionError(
      f"Version '{version}' is invalid. Expected YYYY-MM-DD.",
      code="VERSION_INVALID_FORMAT",
    )

  try:
    return datetime.date.fromisoformat(version)
  except ValueError as exc:
    raise UcpVersionError(
      f"Version '{version}' is invalid. Expected YYYY-MM-DD.",
      code="VERSION_INVALID_FORMAT",
    ) from exc
