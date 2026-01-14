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
except flags.DuplicateFlagError:
  pass


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
  """Shared lifespan manager for initializing databases."""
  del app  # Unused.
  # In tests or if flags aren't set, these might be None, handled by caller
  if FLAGS.products_db_path and FLAGS.transactions_db_path:
    await db.manager.init_dbs(
      FLAGS.products_db_path, FLAGS.transactions_db_path
    )
  yield
  await db.manager.close()
