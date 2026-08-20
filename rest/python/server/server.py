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

"""UCP Merchant Server (Python/FastAPI)."""

import logging
import sys
from collections.abc import Sequence
from absl import app as absl_app
import config
from exceptions import UcpError
from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import generated_routes.ucp_routes
from routes.discovery import router as discovery_router
from routes.mcp import router as mcp_router
from routes.order import router as order_router
import routes.ucp_implementation
import uvicorn

# --- App Setup ---

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
  title="UCP Shopping Service",
  version=config.get_server_version(),
  description="Reference implementation of the UCP Shopping Service",
  lifespan=config.lifespan,
)


def _format_validation_loc(loc: tuple[int | str, ...]) -> str:
  parts = list(loc)
  if parts and parts[0] in ("body", "query", "path", "header"):
    parts = parts[1:]
  if not parts:
    return str(loc[0]) if loc else "request"
  path = ""
  for p in parts:
    if isinstance(p, int):
      path += f"[{p}]"
    else:
      path = f"{path}.{p}" if path else str(p)
  return path


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
  request: Request, exc: RequestValidationError
):
  """Handle validation errors and convert to the UCP error envelope."""
  del request  # Unused.
  error_lines = []
  for err in exc.errors():
    path = _format_validation_loc(err.get("loc", ()))
    msg = err.get("msg", "Validation error")
    error_lines.append(f"✖ {msg}\n  → at {path}")

  error_content = (
    "\n".join(error_lines) if error_lines else "Request validation failed."
  )
  logger.warning("Request payload failed validation:\n%s", error_content)

  return JSONResponse(
    status_code=422,
    content={
      "ucp": {
        "version": config.get_server_version(),
        "status": "error",
      },
      "messages": [
        {
          "type": "error",
          "code": "INVALID_REQUEST",
          "content": error_content,
          "severity": "unrecoverable",
        }
      ],
    },
  )


@app.exception_handler(UcpError)
async def ucp_exception_handler(request: Request, exc: UcpError):
  """Handle UCP-specific exceptions and converts them to JSON responses."""
  del request  # Unused.
  return JSONResponse(
    status_code=exc.status_code,
    content={
      "ucp": {
        "version": config.get_server_version(),
        "status": "error",
      },
      "messages": [
        {
          "type": "error",
          "code": exc.code,
          "content": exc.message,
          "severity": exc.severity,
        }
      ],
    },
  )


# Apply business logic implementation to generated routes
routes.ucp_implementation.apply_implementation(
  generated_routes.ucp_routes.router
)
app.include_router(generated_routes.ucp_routes.router)
app.include_router(order_router)
app.include_router(discovery_router)
app.include_router(mcp_router)


def main(argv: Sequence[str]) -> None:
  """Run the UCP Merchant Server."""
  del argv  # Unused.

  if (
    config.FLAGS.products_db_path is None
    or config.FLAGS.transactions_db_path is None
    or config.FLAGS.port is None
  ):
    logger.error(
      "Both --products_db_path, --transactions_db_path, and --port must be"
      " provided."
    )
    print("\nUsage:")  # noqa: T201
    print(config.FLAGS.main_module_help())  # noqa: T201
    sys.exit(1)

  uvicorn.run(app, host="0.0.0.0", port=config.FLAGS.port)


if __name__ == "__main__":
  absl_app.run(main)
