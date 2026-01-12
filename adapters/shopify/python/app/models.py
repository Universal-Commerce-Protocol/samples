from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# -------------------------
# Common API error shape
# -------------------------
class ApiError(BaseModel):
    detail: str
    code: str


# -------------------------
# Catalog (Mock Shopify)
# -------------------------
class Product(BaseModel):
    id: str
    title: str
    price: int  # cents
    currency: str = "USD"
    image_url: Optional[str] = None


# -------------------------
# Checkout models (UCP-ish)
# -------------------------
class Buyer(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None


class LineItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class LineItem(BaseModel):
    id: str
    item: Dict[str, Any]
    quantity: int
    totals: List[Dict[str, Any]]
    parent_id: Optional[str] = None


class ShippingDestination(BaseModel):
    id: Optional[str] = None
    street_address: Optional[str] = None
    extended_address: Optional[str] = None
    address_locality: Optional[str] = None
    address_region: Optional[str] = None
    address_country: Optional[str] = None
    postal_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class FulfillmentOption(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    carrier: Optional[str] = None
    earliest_fulfillment_time: Optional[str] = None
    latest_fulfillment_time: Optional[str] = None
    totals: List[Dict[str, Any]]


class FulfillmentGroup(BaseModel):
    id: Optional[str] = None
    line_item_ids: Optional[List[str]] = None
    options: Optional[List[FulfillmentOption]] = None
    selected_option_id: Optional[str] = None


class FulfillmentMethod(BaseModel):
    id: Optional[str] = None
    type: Literal["shipping", "pickup"]
    line_item_ids: Optional[List[str]] = None
    destinations: Optional[List[ShippingDestination]] = None
    selected_destination_id: Optional[str] = None
    groups: Optional[List[FulfillmentGroup]] = None


class Fulfillment(BaseModel):
    methods: Optional[List[FulfillmentMethod]] = None
    available_methods: Optional[Any] = None


class Discounts(BaseModel):
    codes: List[str] = []
    applied: List[Dict[str, Any]] = []


class Checkout(BaseModel):
    ucp: Dict[str, Any]
    id: str
    line_items: List[LineItem]
    buyer: Optional[Buyer] = None
    status: str
    currency: str
    totals: List[Dict[str, Any]]
    discounts: Optional[Discounts] = None
    fulfillment: Optional[Fulfillment] = None
    payment: Dict[str, Any] = Field(default_factory=lambda: {"handlers": [], "selected_instrument_id": None, "instruments": []})
    order: Optional[Dict[str, Any]] = None
    messages: Optional[Any] = None
    links: List[Any] = []
    expires_at: Optional[str] = None
    continue_url: Optional[str] = None
    ap2: Optional[Any] = None
    platform: Optional[Any] = None


class CreateCheckoutRequest(BaseModel):
    buyer: Optional[Buyer] = None
    currency: str = "USD"
    line_items: List[LineItemCreate]
    discount_codes: List[str] = []


class UpdateCheckoutRequest(BaseModel):
    id: str
    # allow partial updates; only fulfillment used in this sample
    fulfillment: Optional[Fulfillment] = None


# -------------------------
# Payment (minimal)
# -------------------------
class TokenCredential(BaseModel):
    type: Literal["token"]
    token: str


class PaymentInstrument(BaseModel):
    id: str
    handler_id: str
    type: Literal["card"]
    brand: str
    last_digits: str
    credential: Optional[TokenCredential] = None


class CompleteCheckoutRequest(BaseModel):
    payment_data: PaymentInstrument
    risk_signals: Dict[str, Any] = Field(default_factory=dict)


# -------------------------
# Order models (UCP-ish)
# -------------------------
class OrderLineItem(BaseModel):
    id: str
    item: Dict[str, Any]
    quantity: Dict[str, int]  # {"total": int, "fulfilled": int}
    totals: List[Dict[str, Any]]
    status: str
    parent_id: Optional[str] = None


class FulfillmentEvent(BaseModel):
    id: str
    type: str
    timestamp: str


class OrderFulfillment(BaseModel):
    expectations: List[Dict[str, Any]] = []
    events: List[FulfillmentEvent] = []


class Order(BaseModel):
    ucp: Dict[str, Any]
    id: str
    checkout_id: str
    permalink_url: str
    line_items: List[OrderLineItem]
    fulfillment: OrderFulfillment
    adjustments: Optional[Any] = None
    totals: List[Dict[str, Any]]