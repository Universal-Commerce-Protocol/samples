// Copyright 2026 UCP Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { type Context } from "hono";
import { UCP_VERSION } from "../utils/config";

type DiscoveryCapability = {
  version: string;
  spec: string;
  schema: string;
  extends?: string;
};

type DiscoveryServiceBinding = {
  version: string;
  spec: string;
  schema: string;
  transport: "rest";
  endpoint: string;
};

type DiscoveryPaymentHandler = {
  id: string;
  name: string;
  version: string;
  spec: string;
  config_schema: string;
  instrument_schemas: string[];
  config: Record<string, any>;
};

type UcpDiscoveryMetadata = {
  version: string;
  services: Record<string, DiscoveryServiceBinding[]>;
  capabilities: Record<string, DiscoveryCapability[]>;
  payment_handlers: Record<string, DiscoveryPaymentHandler[]>;
};

/**
 * Service for handling UCP discovery requests.
 *
 * This service provides endpoints that allow UCP agents (clients) to discover
 * the capabilities, supported versions, and configuration of this UCP server.
 * This includes the UCP version, available services (like shopping), specific
 * capabilities (checkout, order, etc.), and supported payment handlers.
 */
export class DiscoveryService {
  readonly ucpVersion = UCP_VERSION;

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
    const payment_handlers = {
      "com.shopify.shop_pay": [
        {
          id: "shop_pay",
          name: "com.shopify.shop_pay",
          version: this.ucpVersion,
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
      ],
      "google.pay": [
        {
          id: "google_pay",
          name: "google.pay",
          version: "1.0",
          spec: "https://example.com/spec",
          config_schema: "https://example.com/schema",
          instrument_schemas: [],
          config: {},
        },
      ],
      "dev.ucp.mock_payment": [
        {
          id: "mock_payment_handler",
          name: "dev.ucp.mock_payment",
          version: "1.0",
          spec: `https://ucp.dev/${this.ucpVersion}/specification/mock`,
          config_schema: `https://ucp.dev/${this.ucpVersion}/schemas/mock.json`,
          instrument_schemas: [
            `https://ucp.dev/${this.ucpVersion}/schemas/shopping/types/card_payment_instrument.json`,
          ],
          config: {
            supported_tokens: ["success_token", "fail_token"],
          },
        },
      ],
    };

    const ucp = {
      version: this.ucpVersion,
      services: {
        "dev.ucp.shopping": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping`,
            transport: "rest",
            schema: `https://ucp.dev/${this.ucpVersion}/services/shopping/openapi.json`,
            endpoint: new URL(c.req.url).origin,
          },
        ],
      },
      capabilities: {
        "dev.ucp.shopping.checkout": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/checkout`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/checkout.json`,
          },
        ],
        "dev.ucp.shopping.order": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/order`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/order.json`,
          },
        ],
        "dev.ucp.shopping.refund": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/refund`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/refund.json`,
            extends: "dev.ucp.shopping.order",
          },
        ],
        "dev.ucp.shopping.return": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/return`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/return.json`,
            extends: "dev.ucp.shopping.order",
          },
        ],
        "dev.ucp.shopping.dispute": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/dispute`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/dispute.json`,
            extends: "dev.ucp.shopping.order",
          },
        ],
        "dev.ucp.shopping.discount": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/discount`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/discount.json`,
            extends: "dev.ucp.shopping.checkout",
          },
        ],
        "dev.ucp.shopping.fulfillment": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/fulfillment`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/fulfillment.json`,
            extends: "dev.ucp.shopping.checkout",
          },
        ],
        "dev.ucp.shopping.buyer_consent": [
          {
            version: this.ucpVersion,
            spec: `https://ucp.dev/${this.ucpVersion}/specification/shopping/buyer_consent`,
            schema: `https://ucp.dev/${this.ucpVersion}/schemas/shopping/buyer_consent.json`,
            extends: "dev.ucp.shopping.checkout",
          },
        ],
      },
      payment_handlers,
    } satisfies UcpDiscoveryMetadata;

    const discoveryProfile = {
      ucp,
      payment: {
        handlers: [
          ...payment_handlers["com.shopify.shop_pay"],
          ...payment_handlers["google.pay"],
          ...payment_handlers["dev.ucp.mock_payment"],
        ],
      },
    };

    return c.json(discoveryProfile);
  };
}
