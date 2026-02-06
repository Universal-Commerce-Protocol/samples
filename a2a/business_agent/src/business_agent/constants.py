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

ADK_USER_CHECKOUT_ID = "user:checkout_id"
ADK_PAYMENT_STATE = "__payment_data__"
ADK_UCP_METADATA_STATE = "__ucp_metadata__"
ADK_EXTENSIONS_STATE_KEY = "__session_extensions__"
ADK_LATEST_TOOL_RESULT = "temp:LATEST_TOOL_RESULT"

A2A_UCP_EXTENSION_URL = "https://ucp.dev/specification/reference?v=2026-01-11"

UCP_AGENT_HEADER = "UCP-Agent"
UCP_FULFILLMENT_EXTENSION = "dev.ucp.shopping.fulfillment"
UCP_BUYER_CONSENT_EXTENSION = "dev.ucp.shopping.buyer_consent"
UCP_DISCOUNT_EXTENSION = "dev.ucp.shopping.discount"

UCP_APPOINTMENT_EXTENSION = "com.levro.appointment"

UCP_CHECKOUT_KEY = "a2a.ucp.checkout"
UCP_PAYMENT_DATA_KEY = "a2a.ucp.checkout.payment_data"
UCP_RISK_SIGNALS_KEY = "a2a.ucp.checkout.risk_signals"
