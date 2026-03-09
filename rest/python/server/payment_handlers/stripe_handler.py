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

"""Stripe payment handler for processing Google Pay tokens via UCP.

Demonstrates how to process the encrypted Google Pay credential token
through Stripe as the Payment Service Provider (PSP). This is the
"last mile" of UCP payment processing that the mock handler skips.

When Google Pay is configured with PAYMENT_GATEWAY tokenization for
Stripe, the credential.token contains a Stripe token (tok_...) that
can be used directly to create a PaymentIntent.

Usage:
  Set STRIPE_SECRET_KEY environment variable and pass
  --payment_handler=stripe when starting the server.

  In test mode (STRIPE_SECRET_KEY starts with sk_test_), you can use
  Stripe's test tokens like "tok_visa" or "tok_mastercard".
"""

import logging
import os

from exceptions import PaymentFailedError

logger = logging.getLogger(__name__)


class StripePaymentHandler:
  """Process Google Pay tokens through Stripe.

  In UCP, when a platform (Google) renders the Google Pay payment sheet,
  it generates an encrypted payment token using the merchant's Stripe
  tokenization configuration. This handler receives that token and
  creates a Stripe PaymentIntent to actually charge the customer.

  The token flow:
    1. Discovery profile declares Stripe as the tokenization gateway
    2. Google Pay encrypts card data into a Stripe token
    3. UCP sends the token in credential.token during complete_checkout
    4. This handler creates a PaymentIntent with the token
  """

  def __init__(self):
    """Initialize Stripe handler from environment."""
    self.api_key = os.environ.get("STRIPE_SECRET_KEY")
    self._stripe = None

  @property
  def stripe(self):
    """Lazy-load stripe module."""
    if self._stripe is None:
      try:
        import stripe

        stripe.api_key = self.api_key
        self._stripe = stripe
      except ImportError as err:
        raise PaymentFailedError(
          "stripe package is required for Stripe payment handler. "
          "Install with: uv add stripe",
          code="CONFIGURATION_ERROR",
          status_code=500,
        ) from err
    return self._stripe

  @property
  def is_configured(self) -> bool:
    """Check if Stripe is properly configured."""
    return bool(self.api_key)

  def process_token(
    self,
    token: str,
    amount: int,
    currency: str,
  ) -> str:
    """Process a Google Pay token through Stripe.

    Args:
      token: The credential.token from the UCP payment instrument.
        In production, this is an encrypted Google Pay token. In
        Stripe test mode, use test tokens like "tok_visa".
      amount: Total amount in the smallest currency unit (e.g. cents).
      currency: ISO 4217 currency code (e.g. "USD").

    Returns:
      The Stripe PaymentIntent ID on success.

    Raises:
      PaymentFailedError: If the payment is declined or fails.
    """
    if not self.is_configured:
      raise PaymentFailedError(
        "Stripe is not configured. Set STRIPE_SECRET_KEY.",
        code="CONFIGURATION_ERROR",
        status_code=500,
      )

    try:
      payment_intent = self.stripe.PaymentIntent.create(
        amount=amount,
        currency=currency.lower(),
        payment_method_data={
          "type": "card",
          "card": {"token": token},
        },
        confirm=True,
        automatic_payment_methods={
          "enabled": True,
          "allow_redirects": "never",
        },
      )

      if payment_intent.status == "succeeded":
        logger.info(
          "Stripe payment succeeded: %s (amount=%d %s)",
          payment_intent.id,
          amount,
          currency,
        )
        return payment_intent.id

      if payment_intent.status == "requires_action":
        raise PaymentFailedError(
          "Payment requires additional authentication (3DS). "
          "This is not supported in headless UCP checkout.",
          code="REQUIRES_ACTION",
        )

      raise PaymentFailedError(
        f"Payment failed with status: {payment_intent.status}",
        code="PAYMENT_FAILED",
      )

    except self.stripe.error.CardError as e:
      raise PaymentFailedError(
        str(e.user_message or e),
        code="CARD_DECLINED",
      ) from e
    except self.stripe.error.InvalidRequestError as e:
      raise PaymentFailedError(
        f"Invalid payment request: {e}",
        code="INVALID_REQUEST",
        status_code=400,
      ) from e
    except self.stripe.error.RateLimitError as e:
      raise PaymentFailedError(
        "Payment provider rate limit exceeded. Please retry.",
        code="RATE_LIMIT",
        status_code=429,
      ) from e
    except self.stripe.error.APIConnectionError as e:
      raise PaymentFailedError(
        "Could not connect to payment provider.",
        code="PSP_UNAVAILABLE",
        status_code=503,
      ) from e
    except self.stripe.error.StripeError as e:
      raise PaymentFailedError(
        f"Payment processing error: {e}",
        code="PSP_ERROR",
        status_code=500,
      ) from e
