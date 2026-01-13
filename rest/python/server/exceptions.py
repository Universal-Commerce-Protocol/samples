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

"""Custom exceptions for the UCP Merchant Server."""


class UcpError(Exception):
  """Base class for all UCP exceptions."""

  def __init__(
    self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500
  ):
    """Initialize UcpError."""
    self.message = message
    self.code = code
    self.status_code = status_code
    super().__init__(self.message)


class ResourceNotFoundError(UcpError):
  """Raised when a requested resource is not found."""

  def __init__(self, message: str):
    """Initialize ResourceNotFoundError."""
    super().__init__(message, code="RESOURCE_NOT_FOUND", status_code=404)


class IdempotencyConflictError(UcpError):
  """Raised when an idempotency key is reused with different parameters."""

  def __init__(self, message: str):
    """Initialize IdempotencyConflictError."""
    super().__init__(message, code="IDEMPOTENCY_CONFLICT", status_code=409)


class CheckoutNotModifiableError(UcpError):
  """Raised when attempting to modify a checkout in a terminal state."""

  def __init__(self, message: str):
    """Initialize CheckoutNotModifiableError."""
    super().__init__(message, code="CHECKOUT_NOT_MODIFIABLE", status_code=409)


class OutOfStockError(UcpError):
  """Raised when there is insufficient inventory for an item."""

  def __init__(self, message: str, status_code: int = 400):
    """Initialize OutOfStockError."""
    super().__init__(message, code="OUT_OF_STOCK", status_code=status_code)


class PaymentFailedError(UcpError):
  """Raised when payment processing fails."""

  def __init__(
    self, message: str, code: str = "PAYMENT_FAILED", status_code: int = 402
  ):
    """Initialize PaymentFailedError."""
    super().__init__(message, code=code, status_code=status_code)


class InvalidRequestError(UcpError):
  """Raised when the request is invalid (e.g. missing fields)."""

  def __init__(self, message: str):
    """Initialize InvalidRequestError."""
    super().__init__(message, code="INVALID_REQUEST", status_code=400)
