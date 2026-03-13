import * as z from "zod";

// Key usage. Should be 'sig' for signing keys.

export const UseSchema = z.enum(["enc", "sig"]);
export type Use = z.infer<typeof UseSchema>;

// The type of card number. Network tokens are preferred with fallback to FPAN.
// See PCI Scope for more details.

export const CardNumberTypeSchema = z.enum(["dpan", "fpan", "network_token"]);
export type CardNumberType = z.infer<typeof CardNumberTypeSchema>;

// A URI pointing to a schema definition (e.g., JSON Schema) used to validate
// the structure of the instrument object.

export const CardPaymentInstrumentTypeSchema = z.enum(["card"]);
export type CardPaymentInstrumentType = z.infer<
  typeof CardPaymentInstrumentTypeSchema
>;

// Type of total categorization.

export const TotalResponseTypeSchema = z.enum([
  "discount",
  "fee",
  "fulfillment",
  "items_discount",
  "subtotal",
  "tax",
  "total",
]);
export type TotalResponseType = z.infer<typeof TotalResponseTypeSchema>;

// Content format, default = plain.

export const ContentTypeSchema = z.enum(["markdown", "plain"]);
export type ContentType = z.infer<typeof ContentTypeSchema>;

// Declares who resolves this error. 'recoverable': agent can fix via API.
// 'requires_buyer_input': merchant requires information their API doesn't
// support collecting programmatically (checkout incomplete).
// 'requires_buyer_review': buyer must authorize before order placement due to
// policy, regulatory, or entitlement rules (checkout complete). Errors with
// 'requires_*' severity contribute to 'status: requires_escalation'.

export const SeveritySchema = z.enum([
  "recoverable",
  "requires_buyer_input",
  "requires_buyer_review",
]);
export type Severity = z.infer<typeof SeveritySchema>;

export const MessageTypeSchema = z.enum(["error", "info", "warning"]);
export type MessageType = z.infer<typeof MessageTypeSchema>;

// Checkout state indicating the current phase and required action. See Checkout
// Status lifecycle documentation for state transition details.

export const CheckoutResponseStatusSchema = z.enum([
  "canceled",
  "complete_in_progress",
  "completed",
  "incomplete",
  "ready_for_complete",
  "requires_escalation",
]);
export type CheckoutResponseStatus = z.infer<
  typeof CheckoutResponseStatusSchema
>;

// Adjustment status.

export const AdjustmentStatusSchema = z.enum([
  "completed",
  "failed",
  "pending",
]);
export type AdjustmentStatus = z.infer<typeof AdjustmentStatusSchema>;

// Delivery method type (shipping, pickup, digital).

export const MethodTypeSchema = z.enum(["digital", "pickup", "shipping"]);
export type MethodType = z.infer<typeof MethodTypeSchema>;

// Derived status: fulfilled if quantity.fulfilled == quantity.total, partial if
// quantity.fulfilled > 0, otherwise processing.

export const OrderLineItemStatusSchema = z.enum([
  "fulfilled",
  "partial",
  "processing",
]);
export type OrderLineItemStatus = z.infer<typeof OrderLineItemStatusSchema>;

// Fulfillment method type this availability applies to.
//
// Fulfillment method type.

export const TypeElementSchema = z.enum(["pickup", "shipping"]);
export type TypeElement = z.infer<typeof TypeElementSchema>;

export const MessageErrorTypeSchema = z.enum(["error"]);
export type MessageErrorType = z.infer<typeof MessageErrorTypeSchema>;

export const MessageInfoTypeSchema = z.enum(["info"]);
export type MessageInfoType = z.infer<typeof MessageInfoTypeSchema>;

export const MessageWarningTypeSchema = z.enum(["warning"]);
export type MessageWarningType = z.infer<typeof MessageWarningTypeSchema>;

// Current fulfillment status.

export const OrderFulfillmentDetailStatusSchema = z.enum([
  "canceled",
  "delivered",
  "failed_attempt",
  "in_transit",
  "out_for_delivery",
  "processing",
  "shipped",
]);
export type OrderFulfillmentDetailStatus = z.infer<
  typeof OrderFulfillmentDetailStatusSchema
>;

// Allocation method. 'each' = applied independently per item. 'across' = split
// proportionally by value.

export const MethodSchema = z.enum(["across", "each"]);
export type Method = z.infer<typeof MethodSchema>;

export const PaymentHandlerResponseSchema = z.object({
  config: z.record(z.string(), z.any()),
  config_schema: z.string(),
  id: z.string(),
  instrument_schemas: z.array(z.string()),
  name: z.string(),
  spec: z.string(),
  version: z.string(),
});
export type PaymentHandlerResponse = z.infer<
  typeof PaymentHandlerResponseSchema
>;

export const SigningKeySchema = z.object({
  alg: z.string().optional(),
  crv: z.string().optional(),
  e: z.string().optional(),
  kid: z.string(),
  kty: z.string(),
  n: z.string().optional(),
  use: UseSchema.optional(),
  x: z.string().optional(),
  y: z.string().optional(),
});
export type SigningKey = z.infer<typeof SigningKeySchema>;

export const CapabilityDiscoverySchema = z.object({
  config: z.record(z.string(), z.any()).optional(),
  extends: z.string().optional(),
  name: z.string(),
  schema: z.string(),
  spec: z.string(),
  version: z.string(),
});
export type CapabilityDiscovery = z.infer<typeof CapabilityDiscoverySchema>;

export const A2ASchema = z.object({
  endpoint: z.string(),
});
export type A2A = z.infer<typeof A2ASchema>;

export const EmbeddedSchema = z.object({
  schema: z.string(),
});
export type Embedded = z.infer<typeof EmbeddedSchema>;

export const McpSchema = z.object({
  endpoint: z.string(),
  schema: z.string(),
});
export type Mcp = z.infer<typeof McpSchema>;

export const RestSchema = z.object({
  endpoint: z.string(),
  schema: z.string(),
});
export type Rest = z.infer<typeof RestSchema>;

export const BuyerSchema = z.object({
  email: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
});
export type Buyer = z.infer<typeof BuyerSchema>;

export const ItemCreateRequestSchema = z.object({
  id: z.string(),
});
export type ItemCreateRequest = z.infer<typeof ItemCreateRequestSchema>;

export const PostalAddressSchema = z.object({
  address_country: z.string().optional(),
  address_locality: z.string().optional(),
  address_region: z.string().optional(),
  extended_address: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
  postal_code: z.string().optional(),
  street_address: z.string().optional(),
});
export type PostalAddress = z.infer<typeof PostalAddressSchema>;

export const PaymentCredentialSchema = z.object({
  type: z.string(),
  card_number_type: CardNumberTypeSchema.optional(),
  cryptogram: z.string().optional(),
  cvc: z.string().optional(),
  eci_value: z.string().optional(),
  expiry_month: z.number().optional(),
  expiry_year: z.number().optional(),
  name: z.string().optional(),
  number: z.string().optional(),
});
export type PaymentCredential = z.infer<typeof PaymentCredentialSchema>;

export const ItemResponseSchema = z.object({
  id: z.string(),
  image_url: z.string().optional(),
  price: z.number(),
  title: z.string(),
});
export type ItemResponse = z.infer<typeof ItemResponseSchema>;

export const TotalResponseSchema = z.object({
  amount: z.number(),
  display_text: z.string().optional(),
  type: TotalResponseTypeSchema,
});
export type TotalResponse = z.infer<typeof TotalResponseSchema>;

export const LinkSchema = z.object({
  title: z.string().optional(),
  type: z.string(),
  url: z.string(),
});
export type Link = z.infer<typeof LinkSchema>;

export const MessageSchema = z.object({
  code: z.string().optional(),
  content: z.string(),
  content_type: ContentTypeSchema.optional(),
  path: z.string().optional(),
  severity: SeveritySchema.optional(),
  type: MessageTypeSchema,
});
export type Message = z.infer<typeof MessageSchema>;

export const CapabilityResponseSchema = z.object({
  config: z.record(z.string(), z.any()).optional(),
  extends: z.string().optional(),
  name: z.string(),
  schema: z.string().optional(),
  spec: z.string().optional(),
  version: z.string(),
});
export type CapabilityResponse = z.infer<typeof CapabilityResponseSchema>;

export const ItemUpdateRequestSchema = z.object({
  id: z.string(),
});
export type ItemUpdateRequest = z.infer<typeof ItemUpdateRequestSchema>;

export const AdjustmentLineItemSchema = z.object({
  id: z.string(),
  quantity: z.number(),
});
export type AdjustmentLineItem = z.infer<typeof AdjustmentLineItemSchema>;

export const FulfillmentEventLineItemSchema = z.object({
  id: z.string(),
  quantity: z.number(),
});
export type FulfillmentEventLineItem = z.infer<
  typeof FulfillmentEventLineItemSchema
>;

export const ExpectationLineItemSchema = z.object({
  id: z.string(),
  quantity: z.number(),
});
export type ExpectationLineItem = z.infer<typeof ExpectationLineItemSchema>;

export const QuantitySchema = z.object({
  fulfilled: z.number(),
  total: z.number(),
});
export type Quantity = z.infer<typeof QuantitySchema>;

export const UcpOrderResponseSchema = z.object({
  capabilities: z.array(CapabilityResponseSchema),
  version: z.string(),
});
export type UcpOrderResponse = z.infer<typeof UcpOrderResponseSchema>;

export const PaymentAccountInfoSchema = z.object({
  payment_account_reference: z.string().optional(),
});
export type PaymentAccountInfo = z.infer<typeof PaymentAccountInfoSchema>;

export const IdentityClassSchema = z.object({
  access_token: z.string(),
});
export type IdentityClass = z.infer<typeof IdentityClassSchema>;

export const CardCredentialSchema = z.object({
  card_number_type: CardNumberTypeSchema,
  cryptogram: z.string().optional(),
  cvc: z.string().optional(),
  eci_value: z.string().optional(),
  expiry_month: z.number().optional(),
  expiry_year: z.number().optional(),
  name: z.string().optional(),
  number: z.string().optional(),
  type: CardPaymentInstrumentTypeSchema,
});
export type CardCredential = z.infer<typeof CardCredentialSchema>;

export const CardPaymentInstrumentSchema = z.object({
  billing_address: PostalAddressSchema.optional(),
  credential: PaymentCredentialSchema.optional(),
  handler_id: z.string(),
  id: z.string(),
  type: CardPaymentInstrumentTypeSchema,
  brand: z.string(),
  expiry_month: z.number().optional(),
  expiry_year: z.number().optional(),
  last_digits: z.string(),
  rich_card_art: z.string().optional(),
  rich_text_description: z.string().optional(),
});
export type CardPaymentInstrument = z.infer<typeof CardPaymentInstrumentSchema>;

export const FulfillmentDestinationRequestSchema = z.object({
  address_country: z.string().optional(),
  address_locality: z.string().optional(),
  address_region: z.string().optional(),
  extended_address: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
  postal_code: z.string().optional(),
  street_address: z.string().optional(),
  id: z.string().optional(),
  address: PostalAddressSchema.optional(),
  name: z.string().optional(),
});
export type FulfillmentDestinationRequest = z.infer<
  typeof FulfillmentDestinationRequestSchema
>;

export const FulfillmentGroupCreateRequestSchema = z.object({
  selected_option_id: z.union([z.null(), z.string()]).optional(),
});
export type FulfillmentGroupCreateRequest = z.infer<
  typeof FulfillmentGroupCreateRequestSchema
>;

export const FulfillmentGroupUpdateRequestSchema = z.object({
  id: z.string(),
  selected_option_id: z.union([z.null(), z.string()]).optional(),
});
export type FulfillmentGroupUpdateRequest = z.infer<
  typeof FulfillmentGroupUpdateRequestSchema
>;

export const FulfillmentDestinationRequestElementSchema = z.object({
  address_country: z.string().optional(),
  address_locality: z.string().optional(),
  address_region: z.string().optional(),
  extended_address: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
  postal_code: z.string().optional(),
  street_address: z.string().optional(),
  id: z.string().optional(),
  address: PostalAddressSchema.optional(),
  name: z.string().optional(),
});
export type FulfillmentDestinationRequestElement = z.infer<
  typeof FulfillmentDestinationRequestElementSchema
>;

export const GroupElementSchema = z.object({
  selected_option_id: z.union([z.null(), z.string()]).optional(),
});
export type GroupElement = z.infer<typeof GroupElementSchema>;

export const GroupClassSchema = z.object({
  id: z.string(),
  selected_option_id: z.union([z.null(), z.string()]).optional(),
});
export type GroupClass = z.infer<typeof GroupClassSchema>;

export const AllowsMultiDestinationSchema = z.object({
  pickup: z.boolean().optional(),
  shipping: z.boolean().optional(),
});
export type AllowsMultiDestination = z.infer<
  typeof AllowsMultiDestinationSchema
>;

export const MessageErrorSchema = z.object({
  code: z.string(),
  content: z.string(),
  content_type: ContentTypeSchema.optional(),
  path: z.string().optional(),
  severity: SeveritySchema,
  type: MessageErrorTypeSchema,
});
export type MessageError = z.infer<typeof MessageErrorSchema>;

export const MessageInfoSchema = z.object({
  code: z.string().optional(),
  content: z.string(),
  content_type: ContentTypeSchema.optional(),
  path: z.string().optional(),
  type: MessageInfoTypeSchema,
});
export type MessageInfo = z.infer<typeof MessageInfoSchema>;

export const MessageWarningSchema = z.object({
  code: z.string(),
  content: z.string(),
  content_type: ContentTypeSchema.optional(),
  path: z.string().optional(),
  type: MessageWarningTypeSchema,
});
export type MessageWarning = z.infer<typeof MessageWarningSchema>;

export const FulfillmentOptionResponseSchema = z.object({
  carrier: z.string().optional(),
  description: z.string().optional(),
  earliest_fulfillment_time: z.coerce.date().optional(),
  id: z.string(),
  latest_fulfillment_time: z.coerce.date().optional(),
  subtotal: z.number().optional(),
  tax: z.number().optional(),
  title: z.string(),
  total: z.number(),
});
export type FulfillmentOptionResponse = z.infer<
  typeof FulfillmentOptionResponseSchema
>;

export const PaymentIdentitySchema = z.object({
  access_token: z.string(),
});
export type PaymentIdentity = z.infer<typeof PaymentIdentitySchema>;

export const PaymentInstrumentBaseSchema = z.object({
  billing_address: PostalAddressSchema.optional(),
  credential: PaymentCredentialSchema.optional(),
  handler_id: z.string(),
  id: z.string(),
  type: z.string(),
});
export type PaymentInstrumentBase = z.infer<typeof PaymentInstrumentBaseSchema>;

export const PlatformFulfillmentConfigSchema = z.object({
  supports_multi_group: z.boolean().optional(),
});
export type PlatformFulfillmentConfig = z.infer<
  typeof PlatformFulfillmentConfigSchema
>;

export const RetailLocationRequestSchema = z.object({
  address: PostalAddressSchema.optional(),
  name: z.string(),
});
export type RetailLocationRequest = z.infer<typeof RetailLocationRequestSchema>;

export const RetailLocationResponseSchema = z.object({
  address: PostalAddressSchema.optional(),
  id: z.string(),
  name: z.string(),
});
export type RetailLocationResponse = z.infer<
  typeof RetailLocationResponseSchema
>;

export const TokenCredentialCreateRequestSchema = z.object({
  token: z.string(),
  type: z.string(),
});
export type TokenCredentialCreateRequest = z.infer<
  typeof TokenCredentialCreateRequestSchema
>;

export const TokenCredentialResponseSchema = z.object({
  type: z.string(),
});
export type TokenCredentialResponse = z.infer<
  typeof TokenCredentialResponseSchema
>;

export const TokenCredentialUpdateRequestSchema = z.object({
  token: z.string(),
  type: z.string(),
});
export type TokenCredentialUpdateRequest = z.infer<
  typeof TokenCredentialUpdateRequestSchema
>;

export const Ap2CompleteRequestObjectSchema = z.object({
  checkout_mandate: z.string(),
});
export type Ap2CompleteRequestObject = z.infer<
  typeof Ap2CompleteRequestObjectSchema
>;

export const Ap2CheckoutResponseObjectSchema = z.object({
  merchant_authorization: z.string(),
});
export type Ap2CheckoutResponseObject = z.infer<
  typeof Ap2CheckoutResponseObjectSchema
>;

export const ConsentSchema = z.object({
  analytics: z.boolean().optional(),
  marketing: z.boolean().optional(),
  preferences: z.boolean().optional(),
  sale_of_data: z.boolean().optional(),
});
export type Consent = z.infer<typeof ConsentSchema>;

export const AllocationElementSchema = z.object({
  amount: z.number(),
  path: z.string(),
});
export type AllocationElement = z.infer<typeof AllocationElementSchema>;

export const MethodElementSchema = z.object({
  destinations: z.array(FulfillmentDestinationRequestElementSchema).optional(),
  groups: z.array(GroupElementSchema).optional(),
  line_item_ids: z.array(z.string()).optional(),
  selected_destination_id: z.union([z.null(), z.string()]).optional(),
  type: TypeElementSchema,
});
export type MethodElement = z.infer<typeof MethodElementSchema>;

export const FulfillmentAvailableMethodResponseSchema = z.object({
  description: z.string().optional(),
  fulfillable_on: z.union([z.null(), z.string()]).optional(),
  line_item_ids: z.array(z.string()),
  type: TypeElementSchema,
});
export type FulfillmentAvailableMethodResponse = z.infer<
  typeof FulfillmentAvailableMethodResponseSchema
>;

export const FulfillmentDestinationResponseSchema = z.object({
  address_country: z.string().optional(),
  address_locality: z.string().optional(),
  address_region: z.string().optional(),
  extended_address: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
  postal_code: z.string().optional(),
  street_address: z.string().optional(),
  id: z.string(),
  address: PostalAddressSchema.optional(),
  name: z.string().optional(),
});
export type FulfillmentDestinationResponse = z.infer<
  typeof FulfillmentDestinationResponseSchema
>;

export const FulfillmentGroupResponseSchema = z.object({
  id: z.string(),
  line_item_ids: z.array(z.string()),
  options: z.array(FulfillmentOptionResponseSchema).optional(),
  selected_option_id: z.union([z.null(), z.string()]).optional(),
});
export type FulfillmentGroupResponse = z.infer<
  typeof FulfillmentGroupResponseSchema
>;

export const PaymentSchema = z.object({
  handlers: z.array(PaymentHandlerResponseSchema).optional(),
});
export type Payment = z.infer<typeof PaymentSchema>;

export const UcpServiceSchema = z.object({
  a2a: A2ASchema.optional(),
  embedded: EmbeddedSchema.optional(),
  mcp: McpSchema.optional(),
  rest: RestSchema.optional(),
  spec: z.string(),
  version: z.string(),
});
export type UcpService = z.infer<typeof UcpServiceSchema>;

export const LineItemCreateRequestSchema = z.object({
  item: ItemCreateRequestSchema,
  quantity: z.number(),
});
export type LineItemCreateRequest = z.infer<typeof LineItemCreateRequestSchema>;

export const PaymentInstrumentSchema = z.object({
  billing_address: PostalAddressSchema.optional(),
  credential: PaymentCredentialSchema.optional(),
  handler_id: z.string(),
  id: z.string(),
  type: CardPaymentInstrumentTypeSchema,
  brand: z.string(),
  expiry_month: z.number().optional(),
  expiry_year: z.number().optional(),
  last_digits: z.string(),
  rich_card_art: z.string().optional(),
  rich_text_description: z.string().optional(),
});
export type PaymentInstrument = z.infer<typeof PaymentInstrumentSchema>;

export const LineItemResponseSchema = z.object({
  id: z.string(),
  item: ItemResponseSchema,
  parent_id: z.string().optional(),
  quantity: z.number(),
  totals: z.array(TotalResponseSchema),
});
export type LineItemResponse = z.infer<typeof LineItemResponseSchema>;

export const PaymentResponseSchema = z.object({
  handlers: z.array(PaymentHandlerResponseSchema),
  instruments: z.array(PaymentInstrumentSchema).optional(),
  selected_instrument_id: z.string().optional(),
});
export type PaymentResponse = z.infer<typeof PaymentResponseSchema>;

export const UcpCheckoutResponseSchema = z.object({
  capabilities: z.array(CapabilityResponseSchema),
  version: z.string(),
});
export type UcpCheckoutResponse = z.infer<typeof UcpCheckoutResponseSchema>;

export const LineItemUpdateRequestSchema = z.object({
  id: z.string().optional(),
  item: ItemUpdateRequestSchema,
  parent_id: z.string().optional(),
  quantity: z.number(),
});
export type LineItemUpdateRequest = z.infer<typeof LineItemUpdateRequestSchema>;

export const CheckoutUpdateRequestPaymentSchema = z.object({
  instruments: z.array(PaymentInstrumentSchema).optional(),
  selected_instrument_id: z.string().optional(),
});
export type CheckoutUpdateRequestPayment = z.infer<
  typeof CheckoutUpdateRequestPaymentSchema
>;

export const AdjustmentSchema = z.object({
  amount: z.number().optional(),
  description: z.string().optional(),
  id: z.string(),
  line_items: z.array(AdjustmentLineItemSchema).optional(),
  occurred_at: z.coerce.date(),
  status: AdjustmentStatusSchema,
  type: z.string(),
});
export type Adjustment = z.infer<typeof AdjustmentSchema>;

export const FulfillmentEventSchema = z.object({
  carrier: z.string().optional(),
  description: z.string().optional(),
  id: z.string(),
  line_items: z.array(FulfillmentEventLineItemSchema),
  occurred_at: z.coerce.date(),
  tracking_number: z.string().optional(),
  tracking_url: z.string().optional(),
  type: z.string(),
});
export type FulfillmentEvent = z.infer<typeof FulfillmentEventSchema>;

export const ExpectationSchema = z.object({
  description: z.string().optional(),
  destination: PostalAddressSchema,
  fulfillable_on: z.string().optional(),
  id: z.string(),
  line_items: z.array(ExpectationLineItemSchema),
  method_type: MethodTypeSchema,
});
export type Expectation = z.infer<typeof ExpectationSchema>;

export const OrderLineItemSchema = z.object({
  id: z.string(),
  item: ItemResponseSchema,
  parent_id: z.string().optional(),
  quantity: QuantitySchema,
  status: OrderLineItemStatusSchema,
  totals: z.array(TotalResponseSchema),
});
export type OrderLineItem = z.infer<typeof OrderLineItemSchema>;

export const PaymentCreateRequestSchema = z.object({
  instruments: z.array(PaymentInstrumentSchema).optional(),
  selected_instrument_id: z.string().optional(),
});
export type PaymentCreateRequest = z.infer<typeof PaymentCreateRequestSchema>;

export const PaymentDataSchema = z.object({
  payment_data: PaymentInstrumentSchema,
});
export type PaymentData = z.infer<typeof PaymentDataSchema>;

export const PaymentUpdateRequestSchema = z.object({
  instruments: z.array(PaymentInstrumentSchema).optional(),
  selected_instrument_id: z.string().optional(),
});
export type PaymentUpdateRequest = z.infer<typeof PaymentUpdateRequestSchema>;

export const BindingSchema = z.object({
  checkout_id: z.string(),
  identity: IdentityClassSchema.optional(),
});
export type Binding = z.infer<typeof BindingSchema>;

export const FulfillmentMethodCreateRequestSchema = z.object({
  destinations: z.array(FulfillmentDestinationRequestElementSchema).optional(),
  groups: z.array(GroupElementSchema).optional(),
  line_item_ids: z.array(z.string()).optional(),
  selected_destination_id: z.union([z.null(), z.string()]).optional(),
  type: TypeElementSchema,
});
export type FulfillmentMethodCreateRequest = z.infer<
  typeof FulfillmentMethodCreateRequestSchema
>;

export const FulfillmentMethodUpdateRequestSchema = z.object({
  destinations: z.array(FulfillmentDestinationRequestElementSchema).optional(),
  groups: z.array(GroupClassSchema).optional(),
  id: z.string(),
  line_item_ids: z.array(z.string()),
  selected_destination_id: z.union([z.null(), z.string()]).optional(),
});
export type FulfillmentMethodUpdateRequest = z.infer<
  typeof FulfillmentMethodUpdateRequestSchema
>;

export const MerchantFulfillmentConfigSchema = z.object({
  allows_method_combinations: z.array(z.array(TypeElementSchema)).optional(),
  allows_multi_destination: AllowsMultiDestinationSchema.optional(),
});
export type MerchantFulfillmentConfig = z.infer<
  typeof MerchantFulfillmentConfigSchema
>;

export const OrderFulfillmentDetailSchema = z.object({
  expected_fulfillment_time: z.string().optional(),
  fulfillment_address: PostalAddressSchema.optional(),
  fulfillment_option: FulfillmentOptionResponseSchema,
  fulfillment_tracking_url: z.string().optional(),
  id: z.string(),
  status: OrderFulfillmentDetailStatusSchema,
  tracking_identifier: z.string().optional(),
});
export type OrderFulfillmentDetail = z.infer<
  typeof OrderFulfillmentDetailSchema
>;

export const CompleteCheckoutRequestWithAp2Schema = z.object({
  ap2: Ap2CompleteRequestObjectSchema.optional(),
});
export type CompleteCheckoutRequestWithAp2 = z.infer<
  typeof CompleteCheckoutRequestWithAp2Schema
>;

export const CheckoutWithAp2MandateSchema = z.object({
  buyer: BuyerSchema.optional(),
  continue_url: z.string().optional(),
  currency: z.string(),
  expires_at: z.coerce.date().optional(),
  id: z.string(),
  line_items: z.array(LineItemResponseSchema),
  links: z.array(LinkSchema),
  messages: z.array(MessageSchema).optional(),
  order_id: z.string().optional(),
  order_permalink_url: z.string().optional(),
  payment: PaymentResponseSchema,
  status: CheckoutResponseStatusSchema,
  totals: z.array(TotalResponseSchema),
  ucp: UcpCheckoutResponseSchema,
  ap2: Ap2CheckoutResponseObjectSchema.optional(),
});
export type CheckoutWithAp2Mandate = z.infer<
  typeof CheckoutWithAp2MandateSchema
>;

export const BuyerWithConsentSchema = z.object({
  email: z.string().optional(),
  first_name: z.string().optional(),
  full_name: z.string().optional(),
  last_name: z.string().optional(),
  phone_number: z.string().optional(),
  consent: ConsentSchema.optional(),
});
export type BuyerWithConsent = z.infer<typeof BuyerWithConsentSchema>;

export const AppliedElementSchema = z.object({
  allocations: z.array(AllocationElementSchema).optional(),
  amount: z.number(),
  automatic: z.boolean().optional(),
  code: z.string().optional(),
  method: MethodSchema.optional(),
  priority: z.number().optional(),
  title: z.string(),
});
export type AppliedElement = z.infer<typeof AppliedElementSchema>;

export const FulfillmentRequestSchema = z.object({
  methods: z.array(MethodElementSchema).optional(),
});
export type FulfillmentRequest = z.infer<typeof FulfillmentRequestSchema>;

export const CheckoutWithFulfillmentUpdateRequestSchema = z.object({
  buyer: BuyerSchema.optional(),
  currency: z.string(),
  id: z.string(),
  line_items: z.array(LineItemUpdateRequestSchema),
  payment: CheckoutUpdateRequestPaymentSchema,
  fulfillment: FulfillmentRequestSchema.optional(),
});
export type CheckoutWithFulfillmentUpdateRequest = z.infer<
  typeof CheckoutWithFulfillmentUpdateRequestSchema
>;

export const FulfillmentMethodResponseSchema = z.object({
  destinations: z.array(FulfillmentDestinationResponseSchema).optional(),
  groups: z.array(FulfillmentGroupResponseSchema).optional(),
  id: z.string(),
  line_item_ids: z.array(z.string()),
  selected_destination_id: z.union([z.null(), z.string()]).optional(),
  type: TypeElementSchema,
});
export type FulfillmentMethodResponse = z.infer<
  typeof FulfillmentMethodResponseSchema
>;

export const UcpClassSchema = z.object({
  capabilities: z.array(CapabilityDiscoverySchema),
  services: z.record(z.string(), UcpServiceSchema),
  version: z.string(),
});
export type UcpClass = z.infer<typeof UcpClassSchema>;

export const PaymentClassSchema = z.object({
  instruments: z.array(PaymentInstrumentSchema).optional(),
  selected_instrument_id: z.string().optional(),
});
export type PaymentClass = z.infer<typeof PaymentClassSchema>;

export const CheckoutResponseSchema = z.object({
  buyer: BuyerSchema.optional(),
  continue_url: z.string().optional(),
  currency: z.string(),
  expires_at: z.coerce.date().optional(),
  id: z.string(),
  line_items: z.array(LineItemResponseSchema),
  links: z.array(LinkSchema),
  messages: z.array(MessageSchema).optional(),
  order_id: z.string().optional(),
  order_permalink_url: z.string().optional(),
  payment: PaymentResponseSchema,
  status: CheckoutResponseStatusSchema,
  totals: z.array(TotalResponseSchema),
  ucp: UcpCheckoutResponseSchema,
});
export type CheckoutResponse = z.infer<typeof CheckoutResponseSchema>;

export const CheckoutUpdateRequestSchema = z.object({
  buyer: BuyerSchema.optional(),
  currency: z.string(),
  id: z.string(),
  line_items: z.array(LineItemUpdateRequestSchema),
  payment: CheckoutUpdateRequestPaymentSchema,
});
export type CheckoutUpdateRequest = z.infer<typeof CheckoutUpdateRequestSchema>;

export const FulfillmentSchema = z.object({
  events: z.array(FulfillmentEventSchema).optional(),
  expectations: z.array(ExpectationSchema).optional(),
});
export type Fulfillment = z.infer<typeof FulfillmentSchema>;

export const CheckoutWithBuyerConsentSchema = z.object({
  buyer: BuyerWithConsentSchema.optional(),
  continue_url: z.string().optional(),
  currency: z.string(),
  expires_at: z.coerce.date().optional(),
  id: z.string(),
  line_items: z.array(LineItemResponseSchema),
  links: z.array(LinkSchema),
  messages: z.array(MessageSchema).optional(),
  order_id: z.string().optional(),
  order_permalink_url: z.string().optional(),
  payment: PaymentResponseSchema,
  status: CheckoutResponseStatusSchema,
  totals: z.array(TotalResponseSchema),
  ucp: UcpCheckoutResponseSchema,
});
export type CheckoutWithBuyerConsent = z.infer<
  typeof CheckoutWithBuyerConsentSchema
>;

export const DiscountsClassSchema = z.object({
  applied: z.array(AppliedElementSchema).optional(),
  codes: z.array(z.string()).optional(),
});
export type DiscountsClass = z.infer<typeof DiscountsClassSchema>;

export const CheckoutWithFulfillmentCreateRequestSchema = z.object({
  buyer: BuyerSchema.optional(),
  currency: z.string(),
  line_items: z.array(LineItemCreateRequestSchema),
  payment: PaymentClassSchema,
  fulfillment: FulfillmentRequestSchema.optional(),
});
export type CheckoutWithFulfillmentCreateRequest = z.infer<
  typeof CheckoutWithFulfillmentCreateRequestSchema
>;

export const FulfillmentResponseSchema = z.object({
  available_methods: z
    .array(FulfillmentAvailableMethodResponseSchema)
    .optional(),
  methods: z.array(FulfillmentMethodResponseSchema).optional(),
});
export type FulfillmentResponse = z.infer<typeof FulfillmentResponseSchema>;

export const UcpDiscoveryProfileSchema = z.object({
  payment: PaymentSchema.optional(),
  signing_keys: z.array(SigningKeySchema).optional(),
  ucp: UcpClassSchema,
});
export type UcpDiscoveryProfile = z.infer<typeof UcpDiscoveryProfileSchema>;

export const CheckoutCreateRequestSchema = z.object({
  buyer: BuyerSchema.optional(),
  currency: z.string(),
  line_items: z.array(LineItemCreateRequestSchema),
  payment: PaymentClassSchema,
});
export type CheckoutCreateRequest = z.infer<typeof CheckoutCreateRequestSchema>;

export const OrderSchema = z.object({
  adjustments: z.array(AdjustmentSchema).optional(),
  checkout_id: z.string(),
  fulfillment: FulfillmentSchema,
  id: z.string(),
  line_items: z.array(OrderLineItemSchema),
  permalink_url: z.string(),
  totals: z.array(TotalResponseSchema),
  ucp: UcpOrderResponseSchema,
});
export type Order = z.infer<typeof OrderSchema>;

export const CheckoutWithDiscountSchema = z.object({
  buyer: BuyerSchema.optional(),
  continue_url: z.string().optional(),
  currency: z.string(),
  expires_at: z.coerce.date().optional(),
  id: z.string(),
  line_items: z.array(LineItemResponseSchema),
  links: z.array(LinkSchema),
  messages: z.array(MessageSchema).optional(),
  order_id: z.string().optional(),
  order_permalink_url: z.string().optional(),
  payment: PaymentResponseSchema,
  status: CheckoutResponseStatusSchema,
  totals: z.array(TotalResponseSchema),
  ucp: UcpCheckoutResponseSchema,
  discounts: DiscountsClassSchema.optional(),
});
export type CheckoutWithDiscount = z.infer<typeof CheckoutWithDiscountSchema>;

export const CheckoutWithFulfillmentResponseSchema = z.object({
  buyer: BuyerSchema.optional(),
  continue_url: z.string().optional(),
  currency: z.string(),
  expires_at: z.coerce.date().optional(),
  id: z.string(),
  line_items: z.array(LineItemResponseSchema),
  links: z.array(LinkSchema),
  messages: z.array(MessageSchema).optional(),
  order_id: z.string().optional(),
  order_permalink_url: z.string().optional(),
  payment: PaymentResponseSchema,
  status: CheckoutResponseStatusSchema,
  totals: z.array(TotalResponseSchema),
  ucp: UcpCheckoutResponseSchema,
  fulfillment: FulfillmentResponseSchema.optional(),
});
export type CheckoutWithFulfillmentResponse = z.infer<
  typeof CheckoutWithFulfillmentResponseSchema
>;
