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

"""Utility script to dump checkout transaction data.

This script reads from the configured transactions SQLite database and prints
a summary of all stored checkout sessions, including their status and line
items. It is useful for debugging and verifying the state of the server.

Usage:
  uv run dump_transactions.py --transactions_db_path=...
"""

import asyncio
import json
import sys
from absl import app as absl_app
from absl import flags
from db import CheckoutSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

FLAGS = flags.FLAGS
flags.DEFINE_string("transactions_db_path", None, "Path to transactions DB")


async def dump_transactions():
  """Query the database and print all checkout transactions."""
  if not FLAGS.transactions_db_path:
    sys.stderr.write("Error: --transactions_db_path is required.\n")
    sys.exit(1)

  db_url = f"sqlite+aiosqlite:///{FLAGS.transactions_db_path}"
  engine = create_async_engine(db_url, echo=False)
  session_factory = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
  )

  async with session_factory() as session:
    result = await session.execute(select(CheckoutSession))
    checkouts = result.scalars().all()

    if not checkouts:
      print("No transactions found.")  # noqa: T201
      return

    for checkout in checkouts:
      print(f"Transaction: {checkout.id} [{checkout.status}]")  # noqa: T201
      try:
        if isinstance(checkout.data, str):
          data = json.loads(checkout.data)
        else:
          data = checkout.data
        line_items = data.get("line_items", [])
        if line_items:
          for line in line_items:
            item = line.get("item", {})
            title = item.get("title", "Unknown Item")
            item_id = item.get("id", "N/A")
            qty = line.get("quantity", 0)
            price = item.get("price", 0) / 100.0
            total = line.get("total", 0) / 100.0
            print(  # noqa: T201
              f"  - {title} (ID: {item_id}) x{qty} @ ${price:.2f} ="
              f" ${total:.2f}"
            )
        else:
          print("  (No items)")  # noqa: T201
      except json.JSONDecodeError:
        print("  (Error parsing transaction data)")  # noqa: T201
      print("-" * 60)  # noqa: T201


def main(argv):
  """Run the transaction dump script."""
  del argv
  asyncio.run(dump_transactions())


if __name__ == "__main__":
  absl_app.run(main)
