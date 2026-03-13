import { z } from "zod";

import {
  CheckoutCreateRequestSchema,
  CheckoutUpdateRequestSchema,
  CheckoutWithBuyerConsentSchema,
  CheckoutWithDiscountSchema,
  CheckoutWithFulfillmentCreateRequestSchema,
  CheckoutWithFulfillmentResponseSchema,
  CheckoutWithFulfillmentUpdateRequestSchema,
  FulfillmentDestinationResponseSchema,
  OrderSchema,
  PaymentCredentialSchema,
} from "./spec_generated";

export const ExtendedPaymentCredentialSchema = PaymentCredentialSchema.extend({
  token: z.string().optional(),
});
export type ExtendedPaymentCredential = z.infer<
  typeof ExtendedPaymentCredentialSchema
>;

export const PlatformConfigSchema = z.object({
  webhook_url: z.string().url().optional(),
});
export type PlatformConfig = z.infer<typeof PlatformConfigSchema>;

export const ExtendedCheckoutResponseSchema =
  CheckoutWithFulfillmentResponseSchema.extend(CheckoutWithDiscountSchema.shape)
    .extend(CheckoutWithBuyerConsentSchema.shape)
    .extend({
      order_id: z.string().optional(),
      order_permalink_url: z.string().optional(),
      platform: PlatformConfigSchema.optional(),
    });
export type ExtendedCheckoutResponse = z.infer<
  typeof ExtendedCheckoutResponseSchema
>;

export const ExtendedCheckoutCreateRequestSchema =
  CheckoutCreateRequestSchema.extend(
    CheckoutWithFulfillmentCreateRequestSchema.pick({ fulfillment: true })
      .shape,
  )
    .extend(CheckoutWithDiscountSchema.pick({ discounts: true }).shape)
    .extend(CheckoutWithBuyerConsentSchema.pick({ buyer: true }).shape);
export type ExtendedCheckoutCreateRequest = z.infer<
  typeof ExtendedCheckoutCreateRequestSchema
>;

export const ExtendedCheckoutUpdateRequestSchema =
  CheckoutUpdateRequestSchema.extend(
    CheckoutWithFulfillmentUpdateRequestSchema.pick({ fulfillment: true })
      .shape,
  )
    .extend(CheckoutWithDiscountSchema.pick({ discounts: true }).shape)
    .extend(CheckoutWithBuyerConsentSchema.pick({ buyer: true }).shape);
export type ExtendedCheckoutUpdateRequest = z.infer<
  typeof ExtendedCheckoutUpdateRequestSchema
>;

export const OrderUpdateSchema = OrderSchema;
export type OrderUpdate = z.infer<typeof OrderUpdateSchema>;
