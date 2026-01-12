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

"""Utility script to dump inventory data.

This script reads the current inventory levels from the configured transactions
SQLite database and outputs them to standard output in CSV format.

Usage:
  uv run dump_inventory.py --transactions_db_path=...
"""

import asyncio
import csv
import sys
from absl import app as absl_app
from absl import flags
from db import Inventory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

FLAGS = flags.FLAGS
flags.DEFINE_string("transactions_db_path", None, "Path to transactions DB")


async def dump_inventory():
  """Query the database and print current inventory levels."""
  if not FLAGS.transactions_db_path:
    sys.stderr.write("Error: --transactions_db_path is required.\n")
    sys.exit(1)

  db_url = f"sqlite+aiosqlite:///{FLAGS.transactions_db_path}"
  engine = create_async_engine(db_url, echo=False)
  session_factory = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
  )

  async with session_factory() as session:
    result = await session.execute(select(Inventory))
    items = result.scalars().all()

    writer = csv.writer(sys.stdout)
    writer.writerow(["product_id", "quantity"])
    for item in items:
      writer.writerow([item.product_id, item.quantity])


def main(argv):
  """Run the inventory dump script."""
  del argv
  asyncio.run(dump_inventory())


if __name__ == "__main__":
  absl_app.run(main)
