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

import { createHash } from "crypto";
import { type Context } from "hono";
import { v4 as uuidv4 } from "uuid";
import { z } from "zod";
import { UCP_VERSION } from "../utils/config";

import {
  getCheckoutSession,
  getIdempotencyRecord,
  getInventory,
  getOrder,
  getProduct,
  logRequest,
  releaseStock,
  reserveStock,
  saveCheckout,
  saveIdempotencyRecord,
  saveOrder,
} from "../data";
import {
  CheckoutResponseStatusSchema,
  type Buyer,
  type Expectation,
  type ExpectationLineItem,
  type ExtendedCheckoutCreateRequest,
  type ExtendedCheckoutResponse,
  type ExtendedCheckoutUpdateRequest,
  ExtendedPaymentCredentialSchema,
  type FulfillmentDestinationRequest,
  type FulfillmentDestinationResponse,
  type FulfillmentOption,
  type FulfillmentRequest,
  type FulfillmentResponse,
  type LineItemCreateRequest,
  type LineItemResponse,
  type Order,
  type OrderLineItem,
  type PaymentCreateRequest,
  CheckoutCompleteRequestSchema,
  type CheckoutCompleteRequest,
  type PostalAddress,
} from "../models";
import {
  CheckoutNotModifiableError,
  IdempotencyConflictError,
  InvalidRequestError,
  OutOfStockError,
  PaymentFailedError,
  ResourceNotFoundError,
  UcpError,
  ucpErrorResponse,
} from "../utils/ucp_error";
import { signRequest } from "../utils/signature";
import { signingKey } from "../utils/webhook_signer";
import { type IdParamContext } from "../utils/validation";

// zCompleteCheckoutRequest and CompleteCheckoutRequest are now imported from SDK models

/**
 * Service for managing checkout sessions.
 */
export class CheckoutService {
  private computeHash(
    operation: string,
    data: unknown,
    resourceId?: string
  ): string {
    // Scope the fingerprint to the operation and, for update/complete/cancel,
    // the target checkout id — so a key cannot replay a different checkout or
    // a different operation. Mirrors the Python sample's idempotency scoping.
    // resourceId is always present (null for create), matching the Python
    // payload shape.
    const payload = {
      operation,
      resourceId: resourceId ?? null,
      data,
    };
    const replacer = (_key: string, value: unknown) =>
      typeof value === "object" && value !== null && !Array.isArray(value)
        ? Object.keys(value as Record<string, unknown>)
            .sort()
            .reduce<Record<string, unknown>>((sorted, k) => {
              sorted[k] = (value as Record<string, unknown>)[k];
              return sorted;
            }, {})
        : value;
    return createHash("sha256")
      .update(JSON.stringify(payload, replacer))
      .digest("hex");
  }

  private async parseAgentProfile(
    ucpAgentHeader: string | undefined
  ): Promise<{ webhook_url?: string } | undefined> {
    if (!ucpAgentHeader) return undefined;

    const match = ucpAgentHeader.match(/profile="([^"]+)"/);
    if (!match) return undefined;

    const profileUri = match[1];

    try {
      let profileData:
        | {
            ucp?: {
              capabilities?: Record<
                string,
                Array<{
                  name: string;
                  config?: { webhook_url?: string };
                }>
              >;
            };
          }
        | undefined;

      if (profileUri.startsWith("data:")) {
        const base64Data = profileUri.split(",")[1];
        if (base64Data) {
          const jsonStr = Buffer.from(base64Data, "base64").toString("utf-8");
          profileData = JSON.parse(jsonStr);
        }
      } else if (profileUri.startsWith("http")) {
        const response = await fetch(profileUri);
        if (response.ok) {
          profileData = (await response.json()) as typeof profileData;
        }
      }

      if (profileData && profileData.ucp && profileData.ucp.capabilities) {
        const orderCaps =
          profileData.ucp.capabilities["dev.ucp.shopping.order"];
        if (orderCaps && orderCaps.length > 0) {
          const orderCap = orderCaps[0];
          if (orderCap && orderCap.config && orderCap.config.webhook_url) {
            return { webhook_url: orderCap.config.webhook_url };
          }
        }
      }
    } catch (e) {
      console.warn("Failed to fetch or parse agent profile", e);
    }
    return undefined;
  }

  /**
   * Notifies the configured platform webhook of an order event.
   *
   * Per the UCP REST OpenAPI (`webhooks.orderEvent`), the request body is the
   * order object itself (`#/components/schemas/order`); the event type is
   * conveyed out of band in the `X-Event-Type` header. The body must always be
   * a valid order, so no notification is sent when there is no order to deliver.
   */
  private async notifyWebhook(
    checkout: ExtendedCheckoutResponse,
    eventType: string,
    baseUrl: string
  ): Promise<void> {
    if (!checkout.platform?.webhook_url) {
      return;
    }

    let orderData: Order | undefined = undefined;
    if (checkout.order) {
      orderData = getOrder(checkout.order.id);
    }

    if (!orderData) {
      console.warn(
        `Skipping ${eventType} webhook for checkout ${checkout.id}: no order to deliver`
      );
      return;
    }

    const webhookUrl = checkout.platform.webhook_url;
    // Serialize exactly once: the signed Content-Digest and the wire body
    // must be the same bytes (order.md, Webhook Signature Verification).
    const body = Buffer.from(JSON.stringify(orderData), "utf-8");
    const webhookId = uuidv4();
    const headers = {
      "Content-Type": "application/json",
      "X-Event-Type": eventType,
      "Webhook-Id": webhookId,
      "Webhook-Timestamp": Math.floor(Date.now() / 1000).toString(),
      // A webhook POST is a state-changing request, so the signed-component
      // table requires idempotency-key (signatures.md). The event id doubles
      // as the key: retries carry the same value, letting the platform
      // deduplicate redelivered events.
      "Idempotency-Key": webhookId,
      // Sign AS this business: the profile URL platforms fetch our
      // signing_keys[] from (order.md requires UCP-Agent on deliveries).
      "UCP-Agent": `profile="${baseUrl}/.well-known/ucp"`,
    };
    const maxAttempts = 3;

    // Delivery failures never propagate into the order flow: a webhook URL
    // the signer cannot handle, or a signing-identity error, degrades to a
    // logged failure exactly like an undeliverable receiver (the Python
    // reference's outer except Exception behaves the same way).
    try {
      const { privateKey, kid } = signingKey();

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        // Re-sign per attempt so the signature's `created` timestamp reflects
        // the actual send time of each delivery attempt.
        const additions = signRequest(
          privateKey,
          kid,
          "POST",
          webhookUrl,
          headers,
          body,
          undefined,
          ["webhook-id", "webhook-timestamp", "x-event-type"]
        );
        try {
          const response = await fetch(webhookUrl, {
            method: "POST",
            headers: { ...headers, ...additions },
            body,
            // A redirect transparently followed would re-POST to a URL the
            // signature does not cover; surface 3xx as a response instead
            // (the Python reference's httpx client does not follow either).
            redirect: "manual",
          });
          if (response.ok) {
            return;
          }
          if (response.status < 500) {
            console.error(
              `Webhook at ${webhookUrl} rejected delivery with status ${response.status}`
            );
            return;
          }
        } catch (e) {
          if (attempt === maxAttempts) {
            console.error(`Failed to notify webhook at ${webhookUrl}`, e);
            return;
          }
        }

        if (attempt < maxAttempts) {
          await new Promise((resolve) =>
            setTimeout(resolve, 100 * 2 ** (attempt - 1))
          );
        }
      }

      console.error(
        `Failed to notify webhook at ${webhookUrl} after ${maxAttempts} attempts`
      );
    } catch (e) {
      console.error(`Failed to notify webhook at ${webhookUrl}`, e);
    }
  }

  private addressesMatch(
    addr1: FulfillmentDestinationResponse,
    addr2: FulfillmentDestinationRequest
  ): boolean {
    return (
      addr1.street_address === addr2.street_address &&
      addr1.address_locality === addr2.address_locality &&
      addr1.address_region === addr2.address_region &&
      addr1.address_country === addr2.address_country &&
      addr1.postal_code === addr2.postal_code
    );
  }

  private constructFulfillmentResponse(
    reqFulfillment: FulfillmentRequest | undefined,
    lineItems: LineItemResponse[],
    buyer?: Buyer | null,
    existingFulfillment?: FulfillmentResponse
  ): FulfillmentResponse | undefined {
    if (!reqFulfillment) {
      return undefined;
    }

    const isKnownCustomer = buyer?.email === "john.doe@example.com";
    const mockDestinations: FulfillmentDestinationResponse[] = isKnownCustomer
      ? [
          {
            id: "addr_1",
            address_country: "US",
            street_address: "123 Main St",
            address_locality: "Springfield",
            address_region: "IL",
            postal_code: "62704",
            first_name: "John",
            last_name: "Doe",
          },
          {
            id: "addr_2",
            address_country: "US",
            street_address: "456 Oak Ave",
            address_locality: "Metropolis",
            address_region: "NY",
            postal_code: "10012",
            first_name: "John",
            last_name: "Doe",
          },
        ]
      : [];

    return {
      methods: (reqFulfillment.methods || []).map((m) => {
        let destinations: FulfillmentDestinationResponse[] | undefined =
          undefined;
        if (m.destinations && Array.isArray(m.destinations)) {
          destinations = m.destinations.map(
            (d): FulfillmentDestinationResponse => {
              if (!d.id) {
                const matched = mockDestinations.find((md) =>
                  this.addressesMatch(md, d)
                );
                if (matched) {
                  return {
                    ...d,
                    id: matched.id,
                  } as FulfillmentDestinationResponse;
                }
              }
              return {
                ...d,
                id: d.id || `dest_${uuidv4()}`,
              } as FulfillmentDestinationResponse;
            }
          );
        } else if (existingFulfillment && existingFulfillment.methods) {
          const targetType = m.type || "shipping";
          const existingMethod = existingFulfillment.methods.find(
            (em) => em.type === targetType
          );
          if (existingMethod && existingMethod.destinations) {
            destinations = existingMethod.destinations;
          }
        } else if (isKnownCustomer) {
          destinations = mockDestinations;
        }

        const groups = (m.groups || []).map((g) => ({
          id: `group_${uuidv4()}`,
          line_item_ids: lineItems.map((li) => li.id),
          selected_option_id: g.selected_option_id,
          options: [], // Will be populated in recalculateTotals
        }));

        return {
          id: `method_${uuidv4()}`,
          type: m.type || "shipping",
          line_item_ids: lineItems.map((li) => li.id),
          ...(destinations ? { destinations } : {}),
          selected_destination_id: m.selected_destination_id,
          groups,
        };
      }),
    };
  }

  private recalculateTotals(checkout: ExtendedCheckoutResponse): void {
    let grandTotal = 0;

    // Line Items
    for (const line of checkout.line_items) {
      const product = getProduct(line.item.id);
      if (!product) {
        throw new Error(`Product ${line.item.id} not found`);
      }
      // Authoritative price and title
      line.item.price = product.price;
      line.item.title = product.title;

      const lineTotal = product.price * line.quantity;
      line.totals = [
        { type: "subtotal", amount: lineTotal },
        { type: "total", amount: lineTotal },
      ];
      grandTotal += lineTotal;
    }

    checkout.totals = [];
    checkout.totals.push({ type: "subtotal", amount: grandTotal });

    // Fulfillment Logic (Mock)
    if (checkout.fulfillment?.methods) {
      for (const method of checkout.fulfillment.methods) {
        // fulfillment.md, "Business Response Behavior": with the default
        // supports_multi_group: false the response MUST carry one group per
        // method. Options are quoted per destination below, so a method the
        // merchant cannot quote for — a non-shipping type, or a destination it
        // does not serve — still reports its line items with no options rather
        // than no group at all.
        if (!method.groups || method.groups.length === 0) {
          method.groups = [
            {
              id: `group_${uuidv4()}`,
              // Required by fulfillment_group.json, so never left undefined.
              line_item_ids: method.line_item_ids ?? [],
              options: [],
            },
          ];
        }

        if (
          method.type === "shipping" &&
          method.selected_destination_id &&
          method.destinations
        ) {
          const dest = method.destinations.find(
            (d: FulfillmentDestinationResponse) =>
              d.id === method.selected_destination_id
          );

          // Extract country from flat field or nested address
          let country = dest?.address_country;
          if (!country && dest?.address) {
            country = dest.address.address_country;
          }

          if (dest && country) {
            const options: FulfillmentOption[] = [];

            if (country === "US") {
              const hasRoses = checkout.line_items.some(
                (li) => li.item.id === "bouquet_roses"
              );
              const isExpensive = grandTotal >= 10000;
              const stdShipCost = hasRoses || isExpensive ? 0 : 500;

              options.push(
                {
                  id: "std-ship",
                  title:
                    stdShipCost === 0
                      ? "Free Standard Shipping"
                      : "Standard Shipping",
                  description: "Arrives in 5-7 days",
                  totals: [
                    { type: "subtotal", amount: stdShipCost },
                    { type: "total", amount: stdShipCost },
                  ],
                },
                {
                  id: "exp-ship-us",
                  title: "Express Shipping (US)",
                  description: "Arrives in 2 days",
                  totals: [
                    { type: "subtotal", amount: 1500 },
                    { type: "total", amount: 1500 },
                  ],
                }
              );
            } else {
              options.push({
                id: "exp-ship-intl",
                title: "International Express",
                description: "Arrives in 5-10 days",
                totals: [
                  { type: "subtotal", amount: 3000 },
                  { type: "total", amount: 3000 },
                ],
              });
            }

            // Assign options to groups
            // Update all groups with available options
            for (const group of method.groups) {
              group.options = options;
            }

            // Calculate total from selected option
            for (const group of method.groups) {
              if (group.selected_option_id && group.options) {
                const selected = group.options.find(
                  (o: FulfillmentOption) => o.id === group.selected_option_id
                );
                if (selected) {
                  const totalObj = selected.totals.find(
                    (t) => t.type === "total"
                  );
                  const totalAmount = totalObj ? totalObj.amount : 0;
                  grandTotal += totalAmount;
                  checkout.totals.push({
                    type: "fulfillment",
                    amount: totalAmount,
                    display_text: selected.title,
                  });
                }
              }
            }
          }
        }
      }
    }

    // Discount Logic (Mock)
    if (!checkout.discounts) {
      checkout.discounts = {};
    }
    checkout.discounts.applied = [];
    if (checkout.discounts.codes) {
      for (const code of checkout.discounts.codes) {
        if (typeof code !== "string") continue;
        const upperCode = code.toUpperCase();
        if (upperCode === "10OFF") {
          const discountAmount = Math.floor(grandTotal * 0.1);
          grandTotal -= discountAmount;
          checkout.discounts.applied.push({
            code,
            title: "10% Off",
            amount: discountAmount,
            allocations: [
              {
                path: "$.totals[?(@.type=='subtotal')]",
                amount: discountAmount,
              },
            ],
          });
          checkout.totals.push({ type: "discount", amount: -discountAmount });
        } else if (upperCode === "WELCOME20") {
          const discountAmount = Math.floor(grandTotal * 0.2);
          grandTotal -= discountAmount;
          checkout.discounts.applied.push({
            code,
            title: "Welcome 20% Off",
            amount: discountAmount,
            allocations: [
              {
                path: "$.totals[?(@.type=='subtotal')]",
                amount: discountAmount,
              },
            ],
          });
          checkout.totals.push({ type: "discount", amount: -discountAmount });
        } else if (upperCode === "FIXED500") {
          const discountAmount = Math.min(grandTotal, 500);
          grandTotal -= discountAmount;
          checkout.discounts.applied.push({
            code,
            title: "$5.00 Off",
            amount: discountAmount,
            allocations: [
              {
                path: "$.totals[?(@.type=='subtotal')]",
                amount: discountAmount,
              },
            ],
          });
          checkout.totals.push({ type: "discount", amount: -discountAmount });
        }
      }
    }

    // Enrich Buyer Consent if present
    if (checkout.buyer?.consent) {
      for (const [purpose, value] of Object.entries(checkout.buyer.consent)) {
        if (value && typeof value === "object") {
          const consentValue = value as any;
          if (!consentValue.description) {
            consentValue.description = `Consent for ${purpose}`;
          }
          if (!consentValue.source) {
            consentValue.source = "platform";
          }
        }
      }
    }

    checkout.totals.push({ type: "total", amount: grandTotal });
  }

  private validateInventory(checkout: ExtendedCheckoutResponse): void {
    for (const line of checkout.line_items) {
      const qtyAvail = getInventory(line.item.id);
      if (qtyAvail === undefined || qtyAvail < line.quantity) {
        throw new OutOfStockError(
          `Insufficient stock for item ${line.item.id}`
        );
      }
    }
  }

  createCheckout = async (c: Context) => {
    const idempotencyKey = c.req.header("Idempotency-Key");
    const ucpAgent = c.req.header("UCP-Agent");
    const request = await c.req.json<ExtendedCheckoutCreateRequest>();
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash("create_checkout", request);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return ucpErrorResponse(
            c,
            new IdempotencyConflictError(
              "Idempotency key reused with different parameters"
            )
          );
        }
        return c.json(JSON.parse(record.response_body), 201);
      }
    }

    const checkoutId = uuidv4();

    // Log Request
    logRequest("POST", "/checkout-sessions", checkoutId, request);

    try {
      // Validate items exists and build initial line items from request
      // The client sends line_items with item.id and quantity.
      const lineItems: LineItemResponse[] = [];

      for (let i = 0; i < request.line_items.length; i++) {
        const reqLine = request.line_items[i];
        const productId = reqLine.item.id;
        const quantity = reqLine.quantity;

        if (!productId) {
          return ucpErrorResponse(
            c,
            new InvalidRequestError(`Line item ${i} missing product ID`)
          );
        }

        const product = getProduct(productId);
        if (!product) {
          return ucpErrorResponse(
            c,
            new InvalidRequestError(`Product ${productId} not found`)
          );
        }

        lineItems.push({
          id: `line_${i + 1}`,
          quantity,
          totals: [],
          item: {
            id: product.id,
            title: product.title,
            price: product.price,
            image_url: product.image_url,
          },
        });
      }

      // checkout.json marks continue_url, expires_at, messages and order as
      // ucp_request: omit, so the business owns them on the response and they
      // must not ride from the request into the response through the spread
      // below. ucp, id, status, totals, links and currency are already
      // overwritten by explicit keys; these four have no explicit key, so
      // they are dropped here.
      const {
        fulfillment: _reqFulfillment,
        continue_url: _reqContinueUrl,
        expires_at: _reqExpiresAt,
        messages: _reqMessages,
        order: _reqOrder,
        ...requestBody
      } = request as typeof request & {
        continue_url?: unknown;
        expires_at?: unknown;
        messages?: unknown;
        order?: unknown;
      };

      const fulfillment = this.constructFulfillmentResponse(
        _reqFulfillment,
        lineItems,
        request.buyer
      );

      // Construct authoritative checkout
      const platformConfig = await this.parseAgentProfile(ucpAgent);

      // The 04-08 schema binds checkout responses to
      // `ucp.json#/$defs/response_checkout_schema`, which adds
      // `required: ["payment_handlers"]` to the ucp envelope. Emit it as an
      // (empty) object, matching the Python reference
      // (`ResponseCheckout(..., payment_handlers={})`). This envelope is
      // persisted with the checkout, so the get/update/complete/cancel paths
      // that read it back inherit the field. It is declared as a standalone
      // object (rather than inline) so the extra property is carried onto the
      // wire even though the SDK's response type does not yet model it.
      const ucp = {
        version: UCP_VERSION,
        capabilities: {
          "dev.ucp.shopping.checkout": [
            {
              name: "dev.ucp.shopping.checkout",
              version: UCP_VERSION,
            },
          ],
        },
        payment_handlers: {},
      };

      const checkout: ExtendedCheckoutResponse = {
        ...requestBody, // Copy other fields like ucp, etc.
        id: checkoutId,
        fulfillment,
        ucp,
        status: CheckoutResponseStatusSchema.enum.incomplete,
        currency: "USD",
        line_items: lineItems,
        totals: [],
        links: [],
        platform: platformConfig,
        payment: request.payment,
      };

      // Calculate totals and validate inventory
      this.recalculateTotals(checkout);
      this.validateInventory(checkout);

      saveCheckout(checkout.id, checkout.status, checkout);

      if (idempotencyKey) {
        saveIdempotencyRecord(
          idempotencyKey,
          requestHash,
          201,
          JSON.stringify(checkout)
        );
      }

      return c.json(checkout, 201);
    } catch (e: unknown) {
      return ucpErrorResponse(
        c,
        e instanceof UcpError
          ? e
          : new InvalidRequestError(e instanceof Error ? e.message : String(e))
      );
    }
  };

  getCheckout = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");

    // Log Request
    logRequest("GET", `/checkout-sessions/${id}`, id, {});

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return ucpErrorResponse(
        c,
        new ResourceNotFoundError("Checkout session not found")
      );
    }
    return c.json(checkout, 200);
  };

  updateCheckout = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const ucpAgent = c.req.header("UCP-Agent");
    const updateRequest = await c.req.json<ExtendedCheckoutUpdateRequest>();
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash("update_checkout", updateRequest, id);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return ucpErrorResponse(
            c,
            new IdempotencyConflictError(
              "Idempotency key reused with different parameters"
            )
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    // Log Request
    logRequest("PUT", `/checkout-sessions/${id}`, id, updateRequest);

    const existing = getCheckoutSession(id);
    if (!existing) {
      return ucpErrorResponse(
        c,
        new ResourceNotFoundError("Checkout session not found")
      );
    }

    if (
      existing.status === CheckoutResponseStatusSchema.enum.completed ||
      existing.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      return ucpErrorResponse(
        c,
        new CheckoutNotModifiableError(
          `Cannot update a ${existing.status} checkout session`
        )
      );
    }

    // Merge updateRequest into existing.
    if (updateRequest.buyer) {
      existing.buyer = updateRequest.buyer;
    }
    const platformConfig = await this.parseAgentProfile(ucpAgent);
    if (platformConfig) {
      existing.platform = platformConfig;
    }

    // Simple merge for payment. In real world, this might be more complex.
    existing.payment = {
      ...existing.payment,
      ...updateRequest.payment,
    };

    if (updateRequest.discounts) {
      existing.discounts = updateRequest.discounts;
    }

    // Update Line Items
    const newLineItems: LineItemResponse[] = [];
    for (const reqLine of updateRequest.line_items) {
      const productId = reqLine.item.id;
      const quantity = reqLine.quantity;

      if (!productId) {
        return ucpErrorResponse(
          c,
          new InvalidRequestError(`Line item missing product ID`)
        );
      }
      const product = getProduct(productId);
      if (!product) {
        return ucpErrorResponse(
          c,
          new InvalidRequestError(`Product ${productId} not found`)
        );
      }

      newLineItems.push({
        id: reqLine.id || `line_${newLineItems.length + 1}`,
        quantity,
        totals: [],
        item: {
          id: product.id,
          title: product.title,
          price: product.price,
          image_url: product.image_url,
        },
      });
    }
    existing.line_items = newLineItems;

    if (updateRequest.fulfillment) {
      existing.fulfillment = this.constructFulfillmentResponse(
        updateRequest.fulfillment,
        existing.line_items,
        existing.buyer,
        existing.fulfillment
      );
    }

    // Recalculate and Validate
    try {
      this.recalculateTotals(existing);
      this.validateInventory(existing);

      saveCheckout(id, existing.status, existing);

      if (idempotencyKey) {
        saveIdempotencyRecord(
          idempotencyKey,
          requestHash,
          200,
          JSON.stringify(existing)
        );
      }

      return c.json(existing, 200);
    } catch (e: unknown) {
      return ucpErrorResponse(
        c,
        e instanceof UcpError
          ? e
          : new InvalidRequestError(e instanceof Error ? e.message : String(e))
      );
    }
  };

  completeCheckout = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const rawBody = await c.req.json<CheckoutCompleteRequest>();
    let requestHash = "";

    // Idempotency check for payment data
    if (idempotencyKey) {
      requestHash = this.computeHash("complete_checkout", rawBody, id);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return ucpErrorResponse(
            c,
            new IdempotencyConflictError(
              "Idempotency key reused with different parameters"
            )
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    // Log Request
    logRequest("POST", `/checkout-sessions/${id}/complete`, id, rawBody);

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return ucpErrorResponse(
        c,
        new ResourceNotFoundError("Checkout session not found")
      );
    }

    // Validate Fulfillment is complete. Require at least one method: an empty
    // methods array must not satisfy the gate via [].every(...) === true.
    const methods = checkout.fulfillment?.methods;
    const hasFulfillment =
      Array.isArray(methods) &&
      methods.length > 0 &&
      methods.every(
        (method) =>
          method.selected_destination_id &&
          method.groups?.every((group) => group.selected_option_id)
      );

    if (!hasFulfillment) {
      return ucpErrorResponse(
        c,
        new InvalidRequestError(
          "Fulfillment address and option must be selected"
        )
      );
    }

    if (
      checkout.status === CheckoutResponseStatusSchema.enum.completed ||
      checkout.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      // If already completed and not caught by idempotency, it's a conflict
      return ucpErrorResponse(
        c,
        new CheckoutNotModifiableError(`Checkout already completed or canceled`)
      );
    }

    // Process Payment
    const payment = rawBody.payment;
    if (!payment || !payment.instruments || payment.instruments.length === 0) {
      return ucpErrorResponse(
        c,
        new InvalidRequestError("Missing payment data")
      );
    }
    const selectedInstrument = payment.instruments[0];

    if (selectedInstrument) {
      const handlerId = selectedInstrument.handler_id;
      const credential = selectedInstrument.credential;
      if (!credential) {
        return ucpErrorResponse(
          c,
          new InvalidRequestError("Missing credentials in instrument")
        );
      }

      if (selectedInstrument.type === "card" && credential.type === "card") {
        // success
      } else {
        const parsedCredential =
          ExtendedPaymentCredentialSchema.safeParse(credential);
        const token = parsedCredential.success
          ? parsedCredential.data.token
          : undefined;

        if (handlerId === "mock_payment_handler") {
          if (token === "success_token") {
            // Success
          } else if (token === "fail_token") {
            return ucpErrorResponse(
              c,
              new PaymentFailedError(
                "Payment Failed: Insufficient Funds (Mock)",
                "INSUFFICIENT_FUNDS",
                402
              )
            );
          } else if (token === "fraud_token") {
            return ucpErrorResponse(
              c,
              new PaymentFailedError(
                "Payment Failed: Fraud Detected (Mock)",
                "FRAUD_DETECTED",
                403
              )
            );
          } else {
            return ucpErrorResponse(
              c,
              new PaymentFailedError(
                `Unknown mock token: ${token}`,
                "UNKNOWN_TOKEN",
                400
              )
            );
          }
        } else if (
          handlerId === "google_pay" ||
          handlerId === "gpay" ||
          handlerId === "shop_pay"
        ) {
          // Mock success
        } else {
          return ucpErrorResponse(
            c,
            new InvalidRequestError(`Unsupported payment handler: ${handlerId}`)
          );
        }
      }
    }

    // Atomic Inventory Reservation and Completion
    try {
      const reservedItems: Array<{ id: string; qty: number }> = [];

      for (const line of checkout.line_items) {
        const product = getProduct(line.item.id);
        if (product) {
          const success = reserveStock(line.item.id, line.quantity);
          if (!success) {
            // Rollback
            for (const reserved of reservedItems) {
              releaseStock(reserved.id, reserved.qty);
            }
            return ucpErrorResponse(
              c,
              new OutOfStockError(`Item ${line.item.id} is out of stock`, 409)
            );
          }
          reservedItems.push({ id: line.item.id, qty: line.quantity });
        }
      }

      // Success
      checkout.status = CheckoutResponseStatusSchema.enum.completed;

      // Create Order
      const orderId = `ord_${uuidv4()}`;

      // Order Fulfillment
      const expectations: Expectation[] = [];

      if (checkout.fulfillment?.methods) {
        for (const method of checkout.fulfillment.methods) {
          // Determine fulfillment address
          let fulfillmentAddress: PostalAddress = {};
          if (method.selected_destination_id && method.destinations) {
            const dest = method.destinations.find(
              (d: FulfillmentDestinationResponse) =>
                d.id === method.selected_destination_id
            );
            if (dest) {
              if (dest.address) {
                // It's a RetailLocation, use its address
                fulfillmentAddress = dest.address;
              } else {
                // It's a PostalAddress (or mixed object in generated types)
                fulfillmentAddress = dest;
              }
            }
          }

          if (method.groups) {
            for (const group of method.groups) {
              if (group.selected_option_id && group.options) {
                const selected = group.options.find(
                  (opt: FulfillmentOption) =>
                    opt.id === group.selected_option_id
                );
                if (selected) {
                  const expectationId = `exp_${uuidv4()}`;
                  const expLineItems: ExpectationLineItem[] = [];

                  if (group.line_item_ids) {
                    for (const liId of group.line_item_ids) {
                      const checkoutLineItem = checkout.line_items.find(
                        (li) => li.id === liId
                      );
                      if (checkoutLineItem) {
                        expLineItems.push({
                          id: checkoutLineItem.id,
                          quantity: checkoutLineItem.quantity,
                        });
                      }
                    }
                  }

                  expectations.push({
                    id: expectationId,
                    destination: fulfillmentAddress,
                    method_type: method.type,
                    line_items: expLineItems,
                    description: selected.title,
                  });
                }
              }
            }
          }
        }
      }

      const orderLineItems: OrderLineItem[] = checkout.line_items.map(
        (li: LineItemResponse) => {
          return {
            id: li.id,
            item: li.item,
            quantity: {
              total: li.quantity,
              fulfilled: 0,
            },
            totals: li.totals,
            status: "processing",
            parent_id: li.parent_id,
          };
        }
      );

      const order: Order = {
        ucp: checkout.ucp,
        id: orderId,
        checkout_id: checkout.id,
        permalink_url: `http://localhost:8080/orders/${orderId}`,
        line_items: orderLineItems,
        totals: checkout.totals,
        fulfillment: {
          expectations,
        },
        currency: checkout.currency,
      };

      saveOrder(order.id, order);

      // Save Checkout
      checkout.order = {
        id: orderId,
        permalink_url: order.permalink_url,
      };

      saveCheckout(id, checkout.status, checkout);

      // Notify webhook
      await this.notifyWebhook(
        checkout,
        "order_placed",
        new URL(c.req.url).origin
      );

      if (idempotencyKey) {
        saveIdempotencyRecord(
          idempotencyKey,
          requestHash,
          200,
          JSON.stringify(checkout)
        );
      }

      return c.json(checkout, 200);
    } catch (e) {
      console.error("Error completing checkout", e);
      return c.json({ detail: "Internal server error" }, 500);
    }
  };

  cancelCheckout = async (c: IdParamContext) => {
    const { id } = c.req.valid("param");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const rawBody = {}; // Empty body for cancel usually
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash("cancel_checkout", rawBody, id);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return ucpErrorResponse(
            c,
            new IdempotencyConflictError(
              "Idempotency key reused with different parameters"
            )
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    logRequest("POST", `/checkout-sessions/${id}/cancel`, id, rawBody);

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return ucpErrorResponse(
        c,
        new ResourceNotFoundError("Checkout session not found")
      );
    }

    if (
      checkout.status === CheckoutResponseStatusSchema.enum.completed ||
      checkout.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      return ucpErrorResponse(
        c,
        new CheckoutNotModifiableError(
          `Cannot cancel a ${checkout.status} checkout session`
        )
      );
    }

    checkout.status = CheckoutResponseStatusSchema.enum.canceled;
    saveCheckout(id, checkout.status, checkout);

    if (idempotencyKey) {
      saveIdempotencyRecord(
        idempotencyKey,
        requestHash,
        200,
        JSON.stringify(checkout)
      );
    }

    return c.json(checkout, 200);
  };

  shipOrder = async (orderId: string, baseUrl: string): Promise<void> => {
    const order = getOrder(orderId);
    if (!order) {
      throw new Error("Order not found");
    }

    if (!order.fulfillment.events) {
      order.fulfillment.events = [];
    }

    order.fulfillment.events.push({
      id: `evt_${uuidv4()}`,
      type: "shipped",
      occurred_at: new Date(),
      line_items: order.line_items.map((lineItem) => ({
        id: lineItem.id,
        quantity: lineItem.quantity.total,
      })),
    });

    saveOrder(order.id, order);

    const checkout = getCheckoutSession(order.checkout_id);
    if (checkout) {
      await this.notifyWebhook(checkout, "order_shipped", baseUrl);
    }
  };
}
