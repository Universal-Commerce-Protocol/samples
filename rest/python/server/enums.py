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

"""Enumerations for the UCP sample server.

This module defines standard enums used throughout the server application
to represent the state of checkout sessions and orders.
"""

import enum


class CheckoutStatus(str, enum.Enum):
  """Possible states for a checkout session."""

  IN_PROGRESS = "incomplete"
  REQUIRES_ESCALATION = "requires_escalation"
  READY_FOR_COMPLETE = "ready_for_complete"
  COMPLETE_IN_PROGRESS = "complete_in_progress"
  COMPLETED = "completed"
  CANCELED = "canceled"


class OrderStatus(str, enum.Enum):
  """Possible states for an order."""

  PROCESSING = "processing"
