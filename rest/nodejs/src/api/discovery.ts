import { type Context } from "hono";
import { type UcpDiscoveryProfile } from "../models";

/**
 * Service for handling UCP discovery requests.
 *
 * This service provides endpoints that allow UCP agents (clients) to discover
 * the capabilities, supported versions, and configuration of this UCP server.
 * This includes the UCP version, available services (like shopping), specific
 * capabilities (checkout, order, etc.), and supported payment handlers.
 */
export class DiscoveryService {
  readonly ucpVersion = "2026-01-23";

  /**
   * Returns the merchant profile, detailing the server's UCP configuration.
   *
   * This endpoint (`/.well-known/ucp`) is the entry point for UCP discovery.
   * It returns a JSON object containing:
   * - `ucp`: The UCP configuration including version, services, and capabilities.
   * - `payment`: Configuration for supported payment handlers.
   *
   * @param c The Hono context object.
   * @returns A JSON response containing the merchant profile.
   */
  getMerchantProfile = (c: Context) => {
    const discoveryProfile: UcpDiscoveryProfile = {
      ucp: {
        version: this.ucpVersion,
        services: {
          "dev.ucp.shopping": {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping",
            rest: {
              schema:
                "https://ucp.dev/2026-01-23/services/shopping/openapi.json",
              endpoint: "http://localhost:3000",
            },
          },
        },
        capabilities: [
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/checkout",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/checkout.json",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/order",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/order.json",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/refund",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/refund.json",
            extends: "dev.ucp.shopping.order",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/return",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/return.json",
            extends: "dev.ucp.shopping.order",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/dispute",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/dispute.json",
            extends: "dev.ucp.shopping.order",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/discount",
            schema: "https://ucp.dev/2026-01-23/schemas/shopping/discount.json",
            extends: "dev.ucp.shopping.checkout",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/fulfillment",
            schema:
              "https://ucp.dev/2026-01-23/schemas/shopping/fulfillment.json",
            extends: "dev.ucp.shopping.checkout",
          },
          {
            version: this.ucpVersion,
            spec: "https://ucp.dev/2026-01-23/specification/shopping/buyer_consent",
            schema:
              "https://ucp.dev/2026-01-23/schemas/shopping/buyer_consent.json",
            extends: "dev.ucp.shopping.checkout",
          },
        ],
      },
      payment: {
        handlers: [
          {
            id: "shop_pay",
            name: "com.shopify.shop_pay",
            version: "2026-01-23",
            spec: "https://shopify.dev/ucp/handlers/shop_pay",
            config_schema:
              "https://shopify.dev/ucp/handlers/shop_pay/config.json",
            instrument_schemas: [
              "https://shopify.dev/ucp/handlers/shop_pay/instrument.json",
            ],
            config: {
              shop_id: "test-shop-id",
            },
          },
          {
            id: "google_pay",
            name: "google.pay",
            version: "1.0",
            spec: "https://example.com/spec",
            config_schema: "https://example.com/schema",
            instrument_schemas: [],
            config: {},
          },
          {
            id: "mock_payment_handler",
            name: "dev.ucp.mock_payment",
            version: "1.0",
            spec: "https://ucp.dev/2026-01-23/specification/mock",
            config_schema: "https://ucp.dev/2026-01-23/schemas/mock.json",
            instrument_schemas: [
              "https://ucp.dev/2026-01-23/schemas/shopping/types/card_payment_instrument.json",
            ],
            config: {
              supported_tokens: ["success_token", "fail_token"],
            },
          },
        ],
      },
    };

    return c.json(discoveryProfile);
  };
}
