# Copyright 2026 UCP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""UCP."""

from typing import Any
from a2a.types import Task, TaskState, TaskStatus
from ucp_sdk.models.schemas.shopping.types.payment_instrument import (
    PaymentInstrument,
)


class MockPaymentProcessor:
    """Mock Payment Processor simulating Merchant Agent to MPP Agent calls."""

    def process_payment(
        self, payment_data: PaymentInstrument, risk_data: Any | None = None
    ) -> Task:
        """Process the payment.

        Args:
            payment_data: The payment instrument to process.
            risk_data: Optional risk data for validation.

        Returns:
            Task: A task representing the completed payment process.

        """
        # this should invoke the Merchant Payment Processor
        # to validate the payment
        task = Task(
            context_id="a unique context id",
            id="a unique task id",
            status=TaskStatus(state=TaskState.completed),
        )
        # return a task that represents the payment processing has completed
        return task
