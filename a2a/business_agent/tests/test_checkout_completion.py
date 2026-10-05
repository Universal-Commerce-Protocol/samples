# Copyright 2026 UCP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Regression tests for the A2A checkout completion contract."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from a2a.server.agent_execution import RequestContext
from a2a.types import DataPart, Message, MessageSendParams, Part, Role, TextPart
from ucp_sdk.models.schemas.shopping.types.buyer import Buyer
from ucp_sdk.models.schemas.shopping.types.payment_instrument import PaymentInstrument
from ucp_sdk.models.schemas.ucp import ResponseCheckout

from business_agent import agent
from business_agent.agent_executor import ADKAgentExecutor
from business_agent.constants import (
    ADK_PAYMENT_STATE,
    ADK_USER_CHECKOUT_ID,
    UCP_PAYMENT_DATA_KEY,
    UCP_RISK_SIGNALS_KEY,
)
from business_agent.payment_processor import MockPaymentProcessor
from business_agent.store import RetailStore


PAYMENT_WIRE = {
    "id": "instr_1",
    "handler_id": "example_payment_provider",
    "type": "card",
    "display": {
        "brand": "visa",
        "last_digits": "8888",
        "expiry_month": 12,
        "expiry_year": 2026,
    },
    "credential": {"type": "token", "token": "mock_token"},
}


class PaymentInputTest(unittest.TestCase):
    """Test the DataPart boundary used by the chat client."""

    def _prepare_input(self, data: dict) -> tuple[str, dict | None]:
        message = Message(
            messageId="message-1",
            role=Role.user,
            parts=[
                Part(root=TextPart(text="Confirm purchase")),
                Part(root=DataPart(data=data)),
            ],
        )
        context = RequestContext(
            request=MessageSendParams(message=message), context_id="context-1"
        )
        executor = ADKAgentExecutor.__new__(ADKAgentExecutor)
        return executor._prepare_input(context)

    def test_extracts_spec_payment_key_and_adapts_nested_display(self):
        query, payment_data = self._prepare_input(
            {"a2a.ucp.checkout.payment": PAYMENT_WIRE.copy()}
        )

        self.assertEqual(query, "Confirm purchase")
        self.assertIsNotNone(payment_data)
        payment = payment_data[UCP_PAYMENT_DATA_KEY]
        self.assertIsInstance(payment, PaymentInstrument)
        self.assertEqual(payment.root.brand, "visa")
        self.assertEqual(payment.root.last_digits, "8888")
        self.assertEqual(
            payment.model_dump(mode="json")["display"], PAYMENT_WIRE["display"]
        )

    def test_ignores_legacy_private_payment_key(self):
        query, payment_data = self._prepare_input(
            {"a2a.ucp.checkout.payment_data": PAYMENT_WIRE.copy()}
        )

        self.assertIsNone(payment_data)
        self.assertIn("a2a.ucp.checkout.payment_data", query)


class CheckoutCompletionTest(unittest.IsolatedAsyncioTestCase):
    """Test checkout state and optional-signal handling before payment."""

    def setUp(self):
        self.original_store = agent.store
        self.original_mpp = agent.mpp
        agent.store = RetailStore()
        agent.mpp = Mock(wraps=MockPaymentProcessor())

    def tearDown(self):
        agent.store = self.original_store
        agent.mpp = self.original_mpp

    def _create_checkout(self):
        metadata = ResponseCheckout(version="2026-01-23", capabilities=[])
        return agent.store.add_to_checkout(metadata, "BISC-001", 1)

    def _context(self, checkout_id: str, payment_data: dict):
        return SimpleNamespace(
            state={
                ADK_USER_CHECKOUT_ID: checkout_id,
                ADK_PAYMENT_STATE: payment_data,
            },
            actions=SimpleNamespace(skip_summarization=False),
        )

    def _payment(self) -> PaymentInstrument:
        return PaymentInstrument.model_validate(
            {**PAYMENT_WIRE, **PAYMENT_WIRE["display"]}
        )

    async def test_rejects_completion_until_checkout_is_ready(self):
        checkout = self._create_checkout()
        context = self._context(
            checkout.id,
            {
                UCP_PAYMENT_DATA_KEY: self._payment(),
                UCP_RISK_SIGNALS_KEY: {"data": "mock risk data"},
            },
        )

        response = await agent.complete_checkout(context)

        self.assertEqual(response["status"], "requires_more_info")
        self.assertIs(agent.store.get_checkout(checkout.id), checkout)
        self.assertEqual(agent.store._orders, {})
        self.assertEqual(context.state[ADK_USER_CHECKOUT_ID], checkout.id)
        agent.mpp.process_payment.assert_not_called()

    async def test_completes_ready_checkout_without_risk_signals(self):
        checkout = self._create_checkout()
        checkout.buyer = Buyer(email="buyer@example.com")
        agent.store.start_payment(checkout.id)
        payment = self._payment()
        context = self._context(checkout.id, {UCP_PAYMENT_DATA_KEY: payment})

        response = await agent.complete_checkout(context)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["a2a.ucp.checkout"]["status"], "completed")
        self.assertIsNone(agent.store.get_checkout(checkout.id))
        self.assertIn(f"ORD-{checkout.id}", agent.store._orders)
        self.assertIsNone(context.state[ADK_USER_CHECKOUT_ID])
        agent.mpp.process_payment.assert_called_once_with(payment, None)

    async def test_passes_optional_risk_signals_to_payment_processor(self):
        checkout = self._create_checkout()
        checkout.buyer = Buyer(email="buyer@example.com")
        agent.store.start_payment(checkout.id)
        payment = self._payment()
        risk_signals = {"data": "mock risk data"}
        context = self._context(
            checkout.id,
            {
                UCP_PAYMENT_DATA_KEY: payment,
                UCP_RISK_SIGNALS_KEY: risk_signals,
            },
        )

        response = await agent.complete_checkout(context)

        self.assertEqual(response["status"], "success")
        agent.mpp.process_payment.assert_called_once_with(payment, risk_signals)


if __name__ == "__main__":
    unittest.main()
