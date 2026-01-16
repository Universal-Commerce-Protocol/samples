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

from pydantic import create_model
from ucp_sdk.models.schemas.shopping.buyer_consent_resp import (
    Checkout as BuyerConsentCheckout,
)
from ucp_sdk.models.schemas.shopping.checkout_resp import (
    CheckoutResponse as Checkout,
)
from ucp_sdk.models.schemas.shopping.discount_resp import (
    Checkout as DiscountCheckout,
)
from ucp_sdk.models.schemas.shopping.fulfillment_resp import (
    Checkout as FulfillmentCheckout,
)
from ucp_sdk.models.schemas.shopping.payment_resp import PaymentResponse
from ucp_sdk.models.schemas.ucp import ResponseCheckout as UcpMetadata
from ..constants import (
    UCP_BUYER_CONSENT_EXTENSION,
    UCP_DISCOUNT_EXTENSION,
    UCP_FULFILLMENT_EXTENSION,
)


def get_checkout_type(ucp_metadata: UcpMetadata) -> type[Checkout]:
    """Generate a dynamic Checkout type based on UCP metadata capabilities.

    Args:
        ucp_metadata: The UCP metadata containing active capabilities.

    Returns:
        type[Checkout]: The generated dynamic checkout class.

    """
    selected_base_models = []

    active_capability_names = {c.name for c in ucp_metadata.capabilities}

    if UCP_FULFILLMENT_EXTENSION in active_capability_names:
        selected_base_models.append(FulfillmentCheckout)
    if UCP_BUYER_CONSENT_EXTENSION in active_capability_names:
        selected_base_models.append(BuyerConsentCheckout)
    if UCP_DISCOUNT_EXTENSION in active_capability_names:
        selected_base_models.append(DiscountCheckout)

    if not selected_base_models:
        return Checkout

    return create_model(
        "DynamicCheckout",
        __base__=tuple(selected_base_models),
        payment=(PaymentResponse, ...),
    )
