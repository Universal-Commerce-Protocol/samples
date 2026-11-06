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

"""Shared discount rules for the cart and checkout totals recalculation.

The discount extension (discount.md) lets the business reject a submitted code
via messages[] with `discount_code_already_applied`, and totals[] carries the
signed effect of each discount. These helpers keep a repeated code from being
applied more than once and keep a fixed-amount discount from pushing the
running total below zero.
"""

from typing import Any

from ucp_sdk.models.schemas.shopping.types.message_warning import (
  MessageWarning,
)

ALREADY_APPLIED = "discount_code_already_applied"


def fixed_amount_discount(value: int, remaining_total: int) -> int:
  """Cap a fixed-amount discount at what is left of the running total."""
  return max(0, min(value, remaining_total))


def already_applied_warning(code: str, index: int) -> MessageWarning:
  """Build the warning returned for a repeated discount code."""
  return MessageWarning(
    type="warning",
    code=ALREADY_APPLIED,
    path=f"$.discounts.codes[{index}]",
    content=f"Code '{code}' is already applied",
  )


def _message_code(message: Any) -> str | None:
  if isinstance(message, dict):
    return message.get("code")
  return getattr(message, "code", None)


def replace_discount_warnings(
  messages: list[Any] | None, warnings: list[MessageWarning]
) -> list[Any] | None:
  """Swap out the warnings this module owns, leaving any other message alone.

  Totals are rebuilt on every create and update, so warnings from an earlier
  recalculation are dropped before the current ones are added.
  """
  kept = [m for m in (messages or []) if _message_code(m) != ALREADY_APPLIED]
  kept.extend(warnings)
  return kept or None
