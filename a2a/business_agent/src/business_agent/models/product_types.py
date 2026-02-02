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

from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ProductDiscoveryModel(BaseModel):
    """Base class for all product discovery types."""

    model_config = ConfigDict(
        populate_by_name=True, serialize_by_alias=True, extra="allow"
    )


class PropertyValue(BaseModel):
    """Corresponds to schema.org/PropertyValue."""

    schema_type: Literal["PropertyValue"] = Field(
        default="PropertyValue", alias="@type"
    )
    name: str
    value: str


class ImageObject(ProductDiscoveryModel):
    """Corresponds to schema.org/ImageObject."""

    url: str
    caption: str | None = None
    schema_type: Literal["ImageObject"] = Field(
        default="ImageObject", alias="@type"
    )


class Organization(ProductDiscoveryModel):
    """Corresponds to schema.org/Organization."""

    name: str
    schema_type: Literal["Organization"] = Field(
        default="Organization", alias="@type"
    )


class Brand(ProductDiscoveryModel):
    """Corresponds to schema.org/Brand."""

    name: str
    schema_type: Literal["Brand"] = Field(default="Brand", alias="@type")


class PriceType(str, Enum):
    """Corresponds to https://schema.org/PriceTypeEnumeration."""

    STRIKE_THROUGH_PRICE = "https://schema.org/StrikeThroughPrice"


class MemberProgramTier(ProductDiscoveryModel):
    """Corresponds to schema.org/MemberProgramTier."""

    id: str = Field(alias="@id")
    schema_type: Literal["MemberProgramTier"] = Field(
        default="MemberProgramTier", alias="@type"
    )


class QuantitativeValue(ProductDiscoveryModel):
    """Corresponds to schema.org/QuantitativeValue."""

    value: str | None = None
    unit_code: str = Field(alias="unitCode")
    schema_type: Literal["QuantitativeValue"] = Field(
        default="QuantitativeValue", alias="@type"
    )


class QuantitativeValueWithReference(QuantitativeValue):
    """Corresponds to schema.org/QuantitativeValue."""

    value_reference: QuantitativeValue | None = Field(
        default=None, alias="valueReference"
    )


class PriceSpecificationType(str, Enum):
    """Specifies the type of the price specification."""

    SUB_TOTAL_AMOUNT = "SubTotalAmount"
    DISCOUNT_AMOUNT = "DiscountAmount"
    TAX_AMOUNT = "TaxAmount"
    SHIPPING_AMOUNT = "ShippingAmount"
    SHIPPING_DISCOUNT_AMOUNT = "ShippingDiscountAmount"
    TOTAL_AMOUNT = "TotalAmount"
    OTHER_AMOUNT = "OtherAmount"


class BasePriceSpecification(ProductDiscoveryModel):
    """Base class for all price specifications."""

    name: str | None = None
    price: str
    price_currency: str = Field(alias="priceCurrency")
    valid_for_member_tier: (
        MemberProgramTier | list[MemberProgramTier] | None
    ) = Field(default=None, alias="validForMemberTier")
    membership_points_earned: str | None = Field(
        default=None, alias="membershipPointsEarned"
    )
    valid_from: str | None = Field(default=None, alias="validFrom")
    valid_through: str | None = Field(default=None, alias="validThrough")
    value_added_tax_included: bool | None = Field(
        alias="valueAddedTaxIncluded", default=None
    )


class PriceSpecification(BasePriceSpecification):
    """Corresponds to schema.org/PriceSpecification."""

    additional_type: PriceSpecificationType | None = Field(
        alias="additionalType", default=None
    )
    schema_type: Literal["PriceSpecification"] = Field(
        default="PriceSpecification", alias="@type"
    )


class UnitPriceSpecification(BasePriceSpecification):
    """Corresponds to schema.org/UnitPriceSpecification."""

    price_type: PriceType | None = Field(alias="priceType", default=None)
    reference_quantity: QuantitativeValueWithReference | None = Field(
        default=None, alias="referenceQuantity"
    )

    schema_type: Literal["UnitPriceSpecification"] = Field(
        default="UnitPriceSpecification", alias="@type"
    )


class ItemAvailability(str, Enum):
    """Corresponds to schema.org/ItemAvailability."""

    IN_STOCK = "https://schema.org/InStock"
    OUT_OF_STOCK = "https://schema.org/OutOfStock"
    PREORDER = "https://schema.org/PreOrder"
    BACKORDER = "https://schema.org/BackOrder"
    DISCONTINUED = "https://schema.org/Discontinued"
    IN_STORE_ONLY = "https://schema.org/InStoreOnly"
    LIMITED_AVAILABILITY = "https://schema.org/LimitedAvailability"
    ONLINE_ONLY = "https://schema.org/OnlineOnly"
    PRE_SALE = "https://schema.org/PreSale"
    SOLD_OUT = "https://schema.org/SoldOut"


class ItemCondition(str, Enum):
    """Corresponds to schema.org/OfferItemCondition."""

    NEW_CONDITION = "https://schema.org/NewCondition"
    REFURBISHED_CONDITION = "https://schema.org/RefurbishedCondition"
    USED_CONDITION = "https://schema.org/UsedCondition"


class AggregateRating(ProductDiscoveryModel):
    """Corresponds to schema.org/AggregateRating."""

    rating_value: float = Field(alias="ratingValue")
    rating_count: int | None = Field(alias="ratingCount", default=None)
    review_count: int | None = Field(alias="reviewCount", default=None)
    best_rating: float | None = Field(default=None, alias="bestRating")
    worst_rating: float | None = Field(default=None, alias="worstRating")
    schema_type: Literal["AggregateRating"] = Field(
        default="AggregateRating", alias="@type"
    )


class SizeSpecification(ProductDiscoveryModel):
    """Corresponds to schema.org/SizeSpecification."""

    name: str
    size_group: str | None = Field(alias="sizeGroup", default=None)
    size_system: str | None = Field(alias="sizeSystem", default=None)
    schema_type: Literal["SizeSpecification"] = Field(
        default="SizeSpecification", alias="@type"
    )


class MonetaryAmount(ProductDiscoveryModel):
    """Corresponds to schema.org/MonetaryAmount."""

    schema_type: Literal["MonetaryAmount"] = Field(
        default="MonetaryAmount", alias="@type"
    )
    value: str | None = None
    max_value: str | None = Field(default=None, alias="maxValue")
    min_value: str | None = Field(default=None, alias="minValue")
    currency: str


class DefinedRegion(ProductDiscoveryModel):
    """Corresponds to schema.org/DefinedRegion."""

    schema_type: Literal["DefinedRegion"] = Field(
        default="DefinedRegion", alias="@type"
    )
    address_country: str | None = Field(default=None, alias="addressCountry")
    address_region: list[str] | None = Field(
        default=None, alias="addressRegion"
    )


class ShippingQuantitativeValue(ProductDiscoveryModel):
    """Corresponds to schema.org/QuantitativeValue."""

    max_value: int
    min_value: int
    unit_code: str = Field(alias="unitCode", default="DAY")
    schema_type: Literal["QuantitativeValue"] = Field(
        default="QuantitativeValue", alias="@type"
    )


class ShippingDeliveryTime(ProductDiscoveryModel):
    """Corresponds to schema.org/ShippingDeliveryTime."""

    schema_type: Literal["ShippingDeliveryTime"] = Field(
        default="ShippingDeliveryTime", alias="@type"
    )
    handling_time: ShippingQuantitativeValue | None = Field(
        alias="handlingTime"
    )
    transit_time: ShippingQuantitativeValue | None = Field(alias="transitTime")


class OfferShippingDetails(ProductDiscoveryModel):
    """Corresponds to schema.org/OfferShippingDetails."""

    schema_type: Literal["OfferShippingDetails"] = Field(
        default="OfferShippingDetails", alias="@type"
    )
    name: str | None = None
    shipping_rate: MonetaryAmount = Field(alias="shippingRate")
    shipping_destination: DefinedRegion = Field(alias="shippingDestination")
    delivery_time: ShippingDeliveryTime = Field(alias="deliveryTime")


class MerchantReturnEnumeration(str, Enum):
    """Corresponds to schema.org/MerchantReturnEnumeration."""

    FINITE_RETURN_WINDOW = "https://schema.org/MerchantReturnFiniteReturnWindow"
    RETURN_NOT_PERMITTED = "https://schema.org/MerchantReturnNotPermitted"
    UNLIMITED_RETURN_WINDOW = "https://schema.org/MerchantReturnUnlimitedWindow"


class ReturnFeesEnumeration(str, Enum):
    """Corresponds to schema.org/ReturnFeesEnumeration."""

    FREE_RETURN = "https://schema.org/FreeReturn"
    RETURN_FEES_CUSTOMER_RESPONSIBILITY = (
        "https://schema.org/ReturnFeesCustomerResponsibility"
    )
    RETURN_SHIPPING_FEES = "https://schema.org/ReturnShippingFees"


class ReturnMethodEnumeration(str, Enum):
    """Corresponds to schema.org/ReturnMethodEnumeration."""

    RETURN_AT_KIOSK = "https://schema.org/ReturnAtKiosk"
    RETURN_BY_MAIL = "https://schema.org/ReturnByMail"
    RETURN_IN_STORE = "https://schema.org/ReturnInStore"


class MerchantReturnPolicy(ProductDiscoveryModel):
    """Corresponds to schema.org/MerchantReturnPolicy."""

    schema_type: Literal["MerchantReturnPolicy"] = Field(
        default="MerchantReturnPolicy", alias="@type"
    )
    applicable_country: str = Field(alias="applicableCountry")
    return_policy_category: MerchantReturnEnumeration = Field(
        alias="returnPolicyCategory"
    )

    merchant_return_days: int | None = Field(
        default=None, alias="merchantReturnDays"
    )
    return_fees: ReturnFeesEnumeration | None = Field(
        default=None, alias="returnFees"
    )
    return_method: ReturnMethodEnumeration | None = Field(alias="returnMethod")
    return_shipping_fees_amount: MonetaryAmount | None = Field(
        default=None, alias="returnShippingFeesAmount"
    )


class Rating(ProductDiscoveryModel):
    """Corresponds to schema.org/Rating."""

    schema_type: Literal["Rating"] = Field(default="Rating", alias="@type")
    rating_value: float = Field(alias="ratingValue")
    rating_explanation: str | None = Field(
        default=None, alias="ratingExplanation"
    )


class Certification(ProductDiscoveryModel):
    """Corresponds to schema.org/Certification."""

    schema_type: Literal["Certification"] = Field(
        default="Certification", alias="@type"
    )
    name: str
    issued_by: Organization = Field(alias="issuedBy")
    certification_rating: Rating | None = Field(
        default=None, alias="certificationRating"
    )
    certification_identification: str | None = Field(
        default=None, alias="certificationIdentification"
    )


class Offer(ProductDiscoveryModel):
    """Corresponds to schema.org/Offer."""

    price: str | None = None
    price_currency: str | None = Field(default=None, alias="priceCurrency")
    price_specification: (
        UnitPriceSpecification | list[UnitPriceSpecification] | None
    ) = Field(default=None, alias="priceSpecification")
    shipping_details: (
        OfferShippingDetails | list[OfferShippingDetails] | None
    ) = Field(default=None, alias="shippingDetails")
    availability: ItemAvailability | None = None
    item_condition: ItemCondition | None = Field(
        default=None, alias="itemCondition"
    )
    has_merchant_return_policy: MerchantReturnPolicy | None = Field(
        default=None, alias="hasMerchantReturnPolicy"
    )
    schema_type: Literal["Offer"] = Field(default="Offer", alias="@type")


class MediaObject(ProductDiscoveryModel):
    """Corresponds to schema.org/MediaObject."""

    schema_type: Literal["MediaObject"] = Field(
        default="MediaObject", alias="@type"
    )
    content_url: str | None = Field(default=None, alias="contentUrl")


class Model3D(ProductDiscoveryModel):
    """Corresponds to schema.org/3DModel."""

    schema_type: Literal["3DModel"] = Field(default="3DModel", alias="@type")
    encoding: MediaObject


class Product(ProductDiscoveryModel):
    """Corresponds to schema.org/Product."""

    schema_type: Literal["Product"] = Field(default="Product", alias="@type")
    product_id: str = Field(alias="productID")
    sku: str
    name: str
    image: str | list[str] | list[ImageObject] | None = None
    brand: Brand | None = None
    offers: Offer
    url: str | None = None

    color: str | None = None
    material: str | None = None
    pattern: str | None = None
    description: str | None = None
    gtin: str | None = None
    mpn: str | None = None
    size: SizeSpecification | str | None = None
    aggregate_rating: AggregateRating | None = Field(
        default=None, alias="aggregateRating"
    )
    in_product_group_with_id: str | list[str] | None = Field(
        default=None, alias="inProductGroupWithID"
    )
    has_certification: Certification | list[Certification] | None = Field(
        default=None, alias="hasCertification"
    )
    subject_of: Model3D | list[Model3D] | None = Field(
        default=None, alias="subjectOf"
    )
    width: QuantitativeValue | None = None
    height: QuantitativeValue | None = None
    depth: QuantitativeValue | None = None
    weight: QuantitativeValue | None = None
    additional_property: PropertyValue | list[PropertyValue] | None = Field(
        default=None, alias="additionalProperty"
    )


class ProductGroup(ProductDiscoveryModel):
    """Corresponds to schema.org/ProductGroup."""

    name: str
    product_group_id: str = Field(alias="productGroupID")
    image: str | list[str] | list[ImageObject] | None = None
    has_variant: list[Product] = Field(alias="hasVariant")
    schema_type: Literal["ProductGroup"] = Field(
        default="ProductGroup", alias="@type"
    )
    context: Literal["https://schema.org/"] = Field(
        default="https://schema.org/", alias="@context"
    )
    url: str | None = None
    description: str | None = None


class TypeAndQuantityNode(ProductDiscoveryModel):
    """Corresponds to schema.org/TypeAndQuantityNode."""

    schema_type: Literal["TypeAndQuantityNode"] = Field(
        default="TypeAndQuantityNode", alias="@type"
    )

    amount_of_this_good: int = Field(alias="amountOfThisGood")
    type_of_good: Product = Field(alias="typeOfGood")


class ProductCollection(ProductDiscoveryModel):
    """Corresponds to schema.org/ProductCollection."""

    schema_type: Literal["ProductCollection"] = Field(
        default="ProductCollection", alias="@type"
    )

    identifier: str
    name: str
    description: str | None = None
    image: str | list[str] | list[ImageObject] | None = None
    url: str | None = None
    includes_object: list[TypeAndQuantityNode] = Field(alias="includesObject")


class ProductResults(ProductDiscoveryModel):
    """Represents the results of a product search."""

    content: str | None = None
    hints: list[str] | None = None
    results: list[Product | ProductGroup | ProductCollection]
    next_page_token: str | None = None
