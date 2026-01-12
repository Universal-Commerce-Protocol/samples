import {type Context} from 'hono';
import {type UcpDiscoveryProfile} from '../models';

/**
 * Service for handling UCP discovery requests.
 *
 * This service provides endpoints that allow UCP agents (clients) to discover
 * the capabilities, supported versions, and configuration of this UCP server.
 * This includes the UCP version, available services (like shopping), specific
 * capabilities (checkout, order, etc.), and supported payment handlers.
 */
export class DiscoveryService {
  readonly ucpVersion = '2026-01-11';

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
          'dev.ucp.shopping': {
            version: this.ucpVersion,
            spec: 'https://ucp.dev/services/shopping/rest.openapi.json',
            rest: {
              schema: 'https://ucp.dev/services/shopping/openapi.json',
              endpoint: 'http://localhost:3000',
            },
          },
        },
        capabilities: [
          {
            name: 'dev.ucp.shopping.checkout',
            version: this.ucpVersion,
            spec: 'https://ucp.dev/specification/checkout',
            schema: 'https://ucp.dev/schemas/shopping/checkout.json',
          },
          {
            name: 'dev.ucp.shopping.order',
            version: this.ucpVersion,
            spec: 'https://ucp.dev/specification/order',
            schema: 'https://ucp.dev/schemas/shopping/order.json',
          },
          {
            name: 'dev.ucp.shopping.discount',
            version: this.ucpVersion,
            spec: 'https://ucp.dev/specification/discount',
            schema: 'https://ucp.dev/schemas/shopping/discount.json',
            extends: 'dev.ucp.shopping.checkout',
          },
          {
            name: 'dev.ucp.shopping.fulfillment',
            version: this.ucpVersion,
            spec: 'https://ucp.dev/specification/fulfillment',
            schema: 'https://ucp.dev/schemas/shopping/fulfillment.json',
            extends: 'dev.ucp.shopping.checkout',
          },
          {
            name: 'dev.ucp.shopping.buyer_consent',
            version: this.ucpVersion,
            spec: 'https://ucp.dev/specification/buyer_consent',
            schema: 'https://ucp.dev/schemas/shopping/buyer_consent.json',
            extends: 'dev.ucp.shopping.checkout',
          },
        ],
      },
      payment: {
        handlers: [
          {
            id: 'shop_pay',
            name: 'com.shopify.shop_pay',
            version: '2026-01-11',
            spec: 'https://shopify.dev/ucp/handlers/shop_pay',
            config_schema:
              'https://shopify.dev/ucp/handlers/shop_pay/config.json',
            instrument_schemas: [
              'https://shopify.dev/ucp/handlers/shop_pay/instrument.json',
            ],
            config: {
              shop_id: 'test-shop-id',
            },
          },
          {
            id: 'google_pay',
            name: 'google.pay',
            version: '2026-01-11',
            spec: 'https://developers.google.com/merchant/ucp/guides/gpay-payment-handler',
            config_schema:
              'https://pay.google.com/gp/p/ucp/2026-01-11/schemas/gpay_config.json',
            instrument_schemas: [
              'https://pay.google.com/gp/p/ucp/2026-01-11/schemas/gpay_card_payment_instrument.json',
            ],
            config: {
              api_version: 2,
              api_version_minor: 0,
              merchant_info: {
                merchant_name: 'Flower Shop',
                merchant_id: 'TEST',
                merchant_origin: 'localhost',
              },
              allowed_payment_methods: [
                {
                  type: 'CARD',
                  parameters: {
                    allowedAuthMethods: ['PAN_ONLY', 'CRYPTOGRAM_3DS'],
                    allowedCardNetworks: ['VISA', 'MASTERCARD'],
                  },
                  tokenization_specification: [
                    {
                      type: 'PAYMENT_GATEWAY',
                      parameters: [
                        {
                          gateway: 'example',
                          gatewayMerchantId: 'exampleGatewayMerchantId',
                        },
                      ],
                    },
                  ],
                },
              ],
            },
          },
          {
            id: 'mock_payment_handler',
            name: 'dev.ucp.mock_payment',
            version: '2026-01-11',
            spec: 'https://ucp.dev/specs/mock',
            config_schema: 'https://ucp.dev/schemas/mock.json',
            instrument_schemas: [
              'https://ucp.dev/schemas/shopping/types/card_payment_instrument.json',
            ],
            config: {
              supported_tokens: ['success_token', 'fail_token'],
            },
          },
        ],
      },
    };

    return c.json(discoveryProfile);
  };
}
