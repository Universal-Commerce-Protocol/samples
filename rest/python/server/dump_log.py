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

"""Utility script to dump request logs from the database.

This script reads and displays HTTP request logs stored in the transactions DB.
It provides details such as timestamp, method, URL, and payload for each
request.
It can optionally look up and display the status of the associated checkout
session.

Usage:
  uv run dump_log.py --transactions_db_path=... [--show_transaction]
"""

import asyncio
import json
import sys
from absl import app as absl_app
from absl import flags
from db import CheckoutSession
from db import RequestLog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

FLAGS = flags.FLAGS
flags.DEFINE_string("transactions_db_path", None, "Path to transactions DB")
flags.DEFINE_bool(
  "show_transaction", False, "Show correlated transaction details"
)


async def dump_logs():
  """Query the database and print request logs."""
  if not FLAGS.transactions_db_path:
    sys.stderr.write("Error: --transactions_db_path is required.\n")
    sys.exit(1)

  db_url = f"sqlite+aiosqlite:///{FLAGS.transactions_db_path}"
  engine = create_async_engine(db_url, echo=False)
  session_factory = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
  )

  async with session_factory() as session:
    print("=== REQUEST LOGS ===")  # noqa: T201
    result = await session.execute(select(RequestLog).order_by(RequestLog.id))
    logs = result.scalars().all()

    if not logs:
      print("No request logs found.")  # noqa: T201
      return

    for log in logs:
      print(f"[{log.timestamp}] {log.method} {log.url}")  # noqa: T201
      if log.checkout_id:
        print(f"  Checkout ID: {log.checkout_id}")  # noqa: T201

        if FLAGS.show_transaction:
          transaction_result = await session.get(
            CheckoutSession, log.checkout_id
          )
          if transaction_result:
            print(f"  Transaction Status: {transaction_result.status}")  # noqa: T201

      if log.payload:
        try:
          # Pretty print JSON if possible
          payload_obj = json.loads(log.payload)
          print(f"  Payload: {json.dumps(payload_obj, indent=2)}")  # noqa: T201
        except (json.JSONDecodeError, TypeError):
          print(f"  Payload: {log.payload}")  # noqa: T201
      print("-" * 40)  # noqa: T201


def main(argv):
  """Run the log dump script."""
  del argv
  asyncio.run(dump_logs())


if __name__ == "__main__":
  absl_app.run(main)
