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

"""Smoke tests for the sample server module."""

import importlib
from pathlib import Path
import sys


def test_server_module_imports(monkeypatch) -> None:
  """The sample server should import with the current Python SDK models."""
  monkeypatch.syspath_prepend(str(Path(__file__).parent))
  sys.modules.pop("server", None)

  server = importlib.import_module("server")

  assert server.app is not None
