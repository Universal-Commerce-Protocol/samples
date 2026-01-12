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

"""Unified models for the UCP sample REST server.

These models extend the base UCP SDK models by combining multiple extensions
(e.g., Fulfillment, Discount, Buyer Consent) into unified checkout and order
objects used by the sample server implementation.
"""

from ucp_sdk.models.schemas.shopping.ap2_mandate import (
  CheckoutResponseWithAp2 as Ap2Checkout,
)
from ucp_sdk.models.schemas.shopping.buyer_consent_create_req import (
  Checkout as BuyerConsentCheckoutCreate,
)
from ucp_sdk.models.schemas.shopping.buyer_consent_resp import (
  Checkout as BuyerConsentCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.buyer_consent_update_req import (
  Checkout as BuyerConsentCheckoutUpdate,
)
from ucp_sdk.models.schemas.shopping.discount_create_req import (
  Checkout as DiscountCheckoutCreate,
)
from ucp_sdk.models.schemas.shopping.discount_resp import (
  Checkout as DiscountCheckoutResp,
)
from ucp_sdk.models.schemas.shopping.discount_update_req import (
  Checkout as DiscountCheckoutUpdate,
)
from ucp_sdk.models.schemas.shopping.fulfillment_create_req import (
  Checkout as FulfillmentCreateRequest,
)
from ucp_sdk.models.schemas.shopping.fulfillment_resp import (
  Checkout as FulfillmentCheckout,
)
from ucp_sdk.models.schemas.shopping.fulfillment_update_req import (
  Checkout as FulfillmentUpdateRequest,
)
from ucp_sdk.models.schemas.shopping.order import Order
from ucp_sdk.models.schemas.shopping.order import PlatformConfig


class UnifiedOrder(Order):
  """Order model supporting extensions."""


class UnifiedCheckout(
  BuyerConsentCheckoutResp,
  FulfillmentCheckout,
  DiscountCheckoutResp,
  Ap2Checkout,
):
  """Checkout model supporting various extensions."""

  platform: PlatformConfig | None = None


class UnifiedCheckoutCreateRequest(
  FulfillmentCreateRequest, DiscountCheckoutCreate, BuyerConsentCheckoutCreate
):
  """Create request model combining base fields and extensions."""


class UnifiedCheckoutUpdateRequest(
  FulfillmentUpdateRequest, DiscountCheckoutUpdate, BuyerConsentCheckoutUpdate
):
  """Update request model combining base fields and extensions."""


UnifiedCheckout.model_rebuild()
UnifiedCheckoutCreateRequest.model_rebuild()
UnifiedCheckoutUpdateRequest.model_rebuild()
UnifiedOrder.model_rebuild()
