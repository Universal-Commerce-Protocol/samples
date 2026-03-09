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

"""Tests for the Stripe payment handler.

These tests use mocks by default (no Stripe key needed). To run the
optional live test against the Stripe test API, set STRIPE_SECRET_KEY:

  STRIPE_SECRET_KEY=sk_test_... uv run pytest payment_handlers/test_stripe_handler.py -v

The live test creates a real PaymentIntent in Stripe's test environment.
"""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Ensure the server root is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from exceptions import PaymentFailedError
from payment_handlers.stripe_handler import StripePaymentHandler


# ---------------------------------------------------------------------------
# Helpers — fake Stripe error hierarchy for except clauses
# ---------------------------------------------------------------------------


class FakeStripeError(Exception):
  pass


class FakeCardError(FakeStripeError):
  def __init__(self, message="", param=None, code=None):
    super().__init__(message)
    self.user_message = message


class FakeInvalidRequestError(FakeStripeError):
  pass


class FakeRateLimitError(FakeStripeError):
  pass


class FakeAPIConnectionError(FakeStripeError):
  pass


def _make_mock_stripe():
  """Build a mock stripe module with real exception classes."""
  mock = MagicMock()
  mock.error.StripeError = FakeStripeError
  mock.error.CardError = FakeCardError
  mock.error.InvalidRequestError = FakeInvalidRequestError
  mock.error.RateLimitError = FakeRateLimitError
  mock.error.APIConnectionError = FakeAPIConnectionError
  return mock


# ---------------------------------------------------------------------------
# Unit tests (no Stripe key or package required)
# ---------------------------------------------------------------------------


class TestStripeHandlerConfiguration:
  """Test handler configuration and gating logic."""

  def test_not_configured_without_env_var(self, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    handler = StripePaymentHandler()
    assert handler.is_configured is False

  def test_configured_with_env_var(self, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    handler = StripePaymentHandler()
    assert handler.is_configured is True

  def test_process_token_raises_when_not_configured(self, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    handler = StripePaymentHandler()
    with pytest.raises(PaymentFailedError, match="not configured"):
      handler.process_token("tok_visa", 3500, "USD")


class TestStripeHandlerMocked:
  """Test payment processing with a mocked Stripe module."""

  @pytest.fixture(autouse=True)
  def _setup(self, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock")
    self.mock_stripe = _make_mock_stripe()
    self.handler = StripePaymentHandler()
    self.handler._stripe = self.mock_stripe

  def test_successful_payment(self):
    pi = MagicMock()
    pi.id = "pi_test_123"
    pi.status = "succeeded"
    self.mock_stripe.PaymentIntent.create.return_value = pi

    result = self.handler.process_token("tok_visa", 3500, "USD")

    assert result == "pi_test_123"
    self.mock_stripe.PaymentIntent.create.assert_called_once_with(
      amount=3500,
      currency="usd",
      payment_method_data={
        "type": "card",
        "card": {"token": "tok_visa"},
      },
      confirm=True,
      automatic_payment_methods={
        "enabled": True,
        "allow_redirects": "never",
      },
    )

  def test_requires_action_raises(self):
    pi = MagicMock()
    pi.status = "requires_action"
    self.mock_stripe.PaymentIntent.create.return_value = pi

    with pytest.raises(PaymentFailedError, match="3DS"):
      self.handler.process_token("tok_visa", 1000, "USD")

  def test_unexpected_status_raises(self):
    pi = MagicMock()
    pi.status = "requires_capture"
    self.mock_stripe.PaymentIntent.create.return_value = pi

    with pytest.raises(PaymentFailedError, match="requires_capture"):
      self.handler.process_token("tok_visa", 1000, "USD")

  def test_card_error_raises(self):
    self.mock_stripe.PaymentIntent.create.side_effect = FakeCardError(
      "Your card was declined."
    )

    with pytest.raises(PaymentFailedError, match="declined"):
      self.handler.process_token("tok_declined", 1000, "USD")

  def test_rate_limit_error_raises(self):
    self.mock_stripe.PaymentIntent.create.side_effect = (
      FakeRateLimitError("rate limit")
    )

    with pytest.raises(PaymentFailedError) as exc_info:
      self.handler.process_token("tok_visa", 1000, "USD")
    assert exc_info.value.status_code == 429

  def test_api_connection_error_raises(self):
    self.mock_stripe.PaymentIntent.create.side_effect = (
      FakeAPIConnectionError("connection failed")
    )

    with pytest.raises(PaymentFailedError) as exc_info:
      self.handler.process_token("tok_visa", 1000, "USD")
    assert exc_info.value.status_code == 503

  def test_invalid_request_error_raises(self):
    self.mock_stripe.PaymentIntent.create.side_effect = (
      FakeInvalidRequestError("bad param")
    )

    with pytest.raises(PaymentFailedError) as exc_info:
      self.handler.process_token("tok_visa", 1000, "USD")
    assert exc_info.value.status_code == 400

  def test_generic_stripe_error_raises(self):
    self.mock_stripe.PaymentIntent.create.side_effect = (
      FakeStripeError("unknown error")
    )

    with pytest.raises(PaymentFailedError) as exc_info:
      self.handler.process_token("tok_visa", 1000, "USD")
    assert exc_info.value.status_code == 500

  def test_currency_lowered(self):
    pi = MagicMock()
    pi.id = "pi_eur"
    pi.status = "succeeded"
    self.mock_stripe.PaymentIntent.create.return_value = pi

    self.handler.process_token("tok_visa", 2000, "EUR")

    call_kwargs = self.mock_stripe.PaymentIntent.create.call_args[1]
    assert call_kwargs["currency"] == "eur"


class TestStripeHandlerLazyImport:
  """Test that stripe is only imported when needed."""

  def test_import_error_gives_clear_message(self, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    handler = StripePaymentHandler()
    handler._stripe = None

    with patch.dict("sys.modules", {"stripe": None}):
      with pytest.raises(PaymentFailedError, match="stripe package"):
        _ = handler.stripe


# ---------------------------------------------------------------------------
# Live test (only runs when STRIPE_SECRET_KEY is set)
# ---------------------------------------------------------------------------

live = pytest.mark.skipif(
  not os.environ.get("STRIPE_SECRET_KEY"),
  reason="STRIPE_SECRET_KEY not set — skipping live Stripe test",
)


@live
class TestStripeHandlerLive:
  """Integration tests against the real Stripe test API.

  These create actual PaymentIntents visible in your Stripe dashboard.
  Only runs when STRIPE_SECRET_KEY=sk_test_... is set.
  """

  def test_live_payment_with_tok_visa(self):
    handler = StripePaymentHandler()
    result = handler.process_token("tok_visa", 100, "USD")
    assert result.startswith("pi_")

  def test_live_payment_declined(self):
    handler = StripePaymentHandler()
    with pytest.raises(PaymentFailedError):
      handler.process_token("tok_chargeDeclined", 100, "USD")
