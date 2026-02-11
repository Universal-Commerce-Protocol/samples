import { createHash } from "crypto";
import { type Context } from "hono";
import { v4 as uuidv4 } from "uuid";
import { z } from "zod";

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
  type Expectation,
  type ExpectationLineItem,
  type ExtendedCheckoutCreateRequest,
  type ExtendedCheckoutResponse,
  type ExtendedCheckoutUpdateRequest,
  ExtendedPaymentCredentialSchema,
  type FulfillmentDestinationRequest,
  type FulfillmentDestinationResponse,
  type FulfillmentOptionResponse,
  type FulfillmentRequest,
  type FulfillmentResponse,
  type LineItemCreateRequest,
  type LineItemResponse,
  type Order,
  type OrderLineItem,
  type PaymentCreateRequest,
  PaymentDataSchema,
  type PostalAddress,
} from "../models";

/**
 * Schema for the request body when completing a checkout session.
 */
export const zCompleteCheckoutRequest = z
  .object({
    risk_signals: z.record(z.string(), z.unknown()).optional(),
  })
  .extend(PaymentDataSchema.shape);

/**
 * Type definition for the complete checkout request body.
 */
export type CompleteCheckoutRequest = z.infer<typeof zCompleteCheckoutRequest>;

/**
 * Service for managing checkout sessions.
 */
export class CheckoutService {
  private computeHash(data: unknown): string {
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
      .update(JSON.stringify(data, replacer))
      .digest("hex");
  }

  private async parseAgentProfile(
    ucpAgentHeader: string | undefined,
  ): Promise<{ webhook_url?: string } | undefined> {
    if (!ucpAgentHeader) return undefined;

    const match = ucpAgentHeader.match(/profile="([^"]+)"/);
    if (!match) return undefined;

    const profileUri = match[1];

    try {
      let profileData:
        | {
            ucp?: {
              capabilities?: Array<{
                name: string;
                config?: { webhook_url?: string };
              }>;
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
        const orderCap = profileData.ucp.capabilities.find(
          (c) => c.name === "dev.ucp.shopping.order",
        );
        if (orderCap && orderCap.config && orderCap.config.webhook_url) {
          return { webhook_url: orderCap.config.webhook_url };
        }
      }
    } catch (e) {
      console.warn("Failed to fetch or parse agent profile", e);
    }
    return undefined;
  }

  private async notifyWebhook(
    checkout: ExtendedCheckoutResponse,
    eventType: string,
  ): Promise<void> {
    if (!checkout.platform?.webhook_url) {
      return;
    }
    const webhookUrl = checkout.platform.webhook_url;
    let orderData: Order | undefined = undefined;
    if (checkout.order_id) {
      orderData = getOrder(checkout.order_id);
    }

    const payload = {
      event_type: eventType,
      checkout_id: checkout.id,
      order: orderData,
    };

    try {
      await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      console.error(`Failed to notify webhook at ${webhookUrl}`, e);
    }
  }

  private constructFulfillmentResponse(
    reqFulfillment: FulfillmentRequest | undefined,
    lineItems: LineItemResponse[],
    existingFulfillment?: FulfillmentResponse,
  ): FulfillmentResponse | undefined {
    if (!reqFulfillment) {
      return undefined;
    }

    const mockDestinations: FulfillmentDestinationResponse[] = [
      {
        id: "dest_1",
        name: "Home (US)",
        address_country: "US",
        address: {
          address_country: "US",
          street_address: "1600 Amphitheatre Pkwy",
          address_locality: "Mountain View",
          address_region: "CA",
          postal_code: "94043",
          full_name: "John Doe",
        },
      },
      {
        id: "dest_2",
        name: "Office (DE)",
        address_country: "DE",
        address: {
          address_country: "DE",
          street_address: "ABC Str. 1",
          address_locality: "Berlin",
          postal_code: "10115",
          full_name: "Max Mustermann",
        },
      },
    ];

    return {
      methods: (reqFulfillment.methods || []).map((m) => {
        // Use provided destinations or fallback to mock
        let destinations: FulfillmentDestinationResponse[] = mockDestinations;
        if (m.destinations && Array.isArray(m.destinations)) {
          destinations = m.destinations.map(
            (d): FulfillmentDestinationResponse => ({
              ...d,
              id: d.id || `dest_${uuidv4()}`,
            }),
          );
        } else if (existingFulfillment && existingFulfillment.methods) {
          // Default to shipping if type is not provided in request
          const targetType = m.type || "shipping";
          const existingMethod = existingFulfillment.methods.find(
            (em) => em.type === targetType,
          );
          if (existingMethod && existingMethod.destinations) {
            destinations = existingMethod.destinations;
          }
        }

        // Initialize groups, preserving selection if provided
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
          destinations,
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
        if (
          method.type === "shipping" &&
          method.selected_destination_id &&
          method.destinations
        ) {
          const dest = method.destinations.find(
            (d: FulfillmentDestinationResponse) =>
              d.id === method.selected_destination_id,
          );

          // Extract country from flat field or nested address
          let country = dest?.address_country;
          if (!country && dest?.address) {
            country = dest.address.address_country;
          }

          if (dest && country) {
            const options: FulfillmentOptionResponse[] = [];

            if (country === "US") {
              options.push(
                {
                  id: "std-ship",
                  title: "Standard Shipping",
                  description: "Arrives in 5-7 days",
                  total: 500,
                  subtotal: 500,
                  tax: 0,
                },
                {
                  id: "exp-ship-us",
                  title: "Express Shipping (US)",
                  description: "Arrives in 2 days",
                  total: 1500,
                  subtotal: 1500,
                  tax: 0,
                },
              );
            } else {
              options.push({
                id: "exp-ship-intl",
                title: "International Express",
                description: "Arrives in 5-10 days",
                total: 3000,
                subtotal: 3000,
                tax: 0,
              });
            }

            // Assign options to groups
            if (!method.groups || method.groups.length === 0) {
              method.groups = [
                {
                  id: `group_${uuidv4()}`,
                  line_item_ids: method.line_item_ids,
                  options,
                },
              ];
            } else {
              // Update all groups with available options
              for (const group of method.groups) {
                group.options = options;
              }
            }

            // Calculate total from selected option
            for (const group of method.groups) {
              if (group.selected_option_id && group.options) {
                const selected = group.options.find(
                  (o: FulfillmentOptionResponse) =>
                    o.id === group.selected_option_id,
                );
                if (selected) {
                  grandTotal += selected.total;
                  checkout.totals.push({
                    type: "fulfillment",
                    amount: selected.total,
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
        if (typeof code === "string" && code.toUpperCase() === "10OFF") {
          const discountAmount = Math.floor(grandTotal * 0.1);
          grandTotal -= discountAmount;
          checkout.discounts.applied.push({
            code,
            title: "10% Off",
            amount: discountAmount,
            allocations: [{ path: "subtotal", amount: discountAmount }],
          });
          checkout.totals.push({ type: "discount", amount: discountAmount });
        }
      }
    }

    checkout.totals.push({ type: "total", amount: grandTotal });
  }

  private validateInventory(checkout: ExtendedCheckoutResponse): void {
    for (const line of checkout.line_items) {
      const qtyAvail = getInventory(line.item.id);
      if (qtyAvail === undefined || qtyAvail < line.quantity) {
        throw new Error(`Insufficient stock for item ${line.item.id}`);
      }
    }
  }

  createCheckout = async (c: Context) => {
    const idempotencyKey = c.req.header("Idempotency-Key");
    const ucpAgent = c.req.header("UCP-Agent");
    const request = await c.req.json<ExtendedCheckoutCreateRequest>();
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash(request);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return c.json(
            { detail: "Idempotency key reused with different parameters" },
            409,
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
          return c.json({ detail: `Line item ${i} missing product ID` }, 400);
        }

        const product = getProduct(productId);
        if (!product) {
          return c.json({ detail: `Product ${productId} not found` }, 400);
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

      const { fulfillment: _reqFulfillment, ...requestBody } = request;

      const fulfillment = this.constructFulfillmentResponse(
        _reqFulfillment,
        lineItems,
      );

      // Construct authoritative checkout
      const platformConfig = await this.parseAgentProfile(ucpAgent);

      const checkout: ExtendedCheckoutResponse = {
        ...requestBody, // Copy other fields like ucp, etc.
        id: checkoutId,
        fulfillment,
        ucp: { version: "2022-01-01", capabilities: [] },
        status: CheckoutResponseStatusSchema.enum.incomplete,
        currency: request.currency || "USD",
        line_items: lineItems,
        totals: [],
        links: [],
        platform: platformConfig,
        payment: {
          ...request.payment,
          handlers: [
            {
              id: "google_pay",
              name: "google.pay",
              version: "2025-03-25",
              spec: "https://example.com/spec",
              config_schema: "https://example.com/schema",
              instrument_schemas: ["https://example.com/instrument_schema"],
              config: {},
            },
          ],
        },
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
          JSON.stringify(checkout),
        );
      }

      return c.json(checkout, 201);
    } catch (e: unknown) {
      return c.json(
        { detail: e instanceof Error ? e.message : String(e) },
        400,
      );
    }
  };

  getCheckout = async (c: Context) => {
    const id = c.req.param("id");

    // Log Request
    logRequest("GET", `/checkout-sessions/${id}`, id, {});

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return c.json({ detail: "Checkout session not found" }, 404);
    }
    return c.json(checkout, 200);
  };

  updateCheckout = async (c: Context) => {
    const id = c.req.param("id");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const ucpAgent = c.req.header("UCP-Agent");
    const updateRequest = await c.req.json<ExtendedCheckoutUpdateRequest>();
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash(updateRequest);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return c.json(
            { detail: "Idempotency key reused with different parameters" },
            409,
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    // Log Request
    logRequest("PUT", `/checkout-sessions/${id}`, id, updateRequest);

    const existing = getCheckoutSession(id);
    if (!existing) {
      return c.json({ detail: "Checkout session not found" }, 404);
    }

    if (
      existing.status === CheckoutResponseStatusSchema.enum.completed ||
      existing.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      return c.json(
        { detail: `Cannot update a ${existing.status} checkout session` },
        409,
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
    existing.currency = updateRequest.currency;

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
        return c.json({ detail: `Line item missing product ID` }, 400);
      }
      const product = getProduct(productId);
      if (!product) {
        return c.json({ detail: `Product ${productId} not found` }, 400);
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
        existing.fulfillment,
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
          JSON.stringify(existing),
        );
      }

      return c.json(existing, 200);
    } catch (e: unknown) {
      return c.json(
        { detail: e instanceof Error ? e.message : String(e) },
        400,
      );
    }
  };

  completeCheckout = async (c: Context) => {
    const id = c.req.param("id");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const rawBody = await c.req.json<CompleteCheckoutRequest>();
    let requestHash = "";

    // Idempotency check for payment data
    if (idempotencyKey) {
      requestHash = this.computeHash(rawBody);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return c.json(
            { detail: "Idempotency key reused with different parameters" },
            409,
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    // Log Request
    logRequest("POST", `/checkout-sessions/${id}/complete`, id, rawBody);

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return c.json({ detail: "Checkout session not found" }, 404);
    }

    if (
      checkout.status === CheckoutResponseStatusSchema.enum.completed ||
      checkout.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      // If already completed and not caught by idempotency, it's a conflict
      return c.json({ detail: `Checkout already completed or canceled` }, 409);
    }

    // Process Payment
    const selectedInstrument = rawBody.payment_data;

    if (!selectedInstrument) {
      return c.json({ detail: "Missing payment data" }, 400);
    }

    if (selectedInstrument) {
      const handlerId = selectedInstrument.handler_id;
      const credential = selectedInstrument.credential;
      if (!credential) {
        return c.json({ detail: "Missing credentials in instrument" }, 400);
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
            return c.json(
              { detail: "Payment Failed: Insufficient Funds (Mock)" },
              402,
            );
          } else if (token === "fraud_token") {
            return c.json(
              { detail: "Payment Failed: Fraud Detected (Mock)" },
              403,
            );
          } else {
            return c.json({ detail: `Unknown mock token: ${token}` }, 400);
          }
        } else if (
          handlerId === "google_pay" ||
          handlerId === "gpay" ||
          handlerId === "shop_pay"
        ) {
          // Mock success
        } else {
          return c.json(
            { detail: `Unsupported payment handler: ${handlerId}` },
            400,
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
            return c.json(
              { detail: `Item ${line.item.id} is out of stock` },
              409,
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
                d.id === method.selected_destination_id,
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
                  (opt: FulfillmentOptionResponse) =>
                    opt.id === group.selected_option_id,
                );
                if (selected) {
                  const expectationId = `exp_${uuidv4()}`;
                  const expLineItems: ExpectationLineItem[] = [];

                  if (group.line_item_ids) {
                    for (const liId of group.line_item_ids) {
                      const checkoutLineItem = checkout.line_items.find(
                        (li) => li.id === liId,
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
        },
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
      };

      saveOrder(order.id, order);

      // Save Checkout
      checkout.order_id = orderId;
      checkout.order_permalink_url = order.permalink_url;

      saveCheckout(id, checkout.status, checkout);

      // Notify webhook
      await this.notifyWebhook(checkout, "order_placed");

      if (idempotencyKey) {
        saveIdempotencyRecord(
          idempotencyKey,
          requestHash,
          200,
          JSON.stringify(checkout),
        );
      }

      return c.json(checkout, 200);
    } catch (e) {
      console.error("Error completing checkout", e);
      return c.json({ detail: "Internal server error" }, 500);
    }
  };

  cancelCheckout = async (c: Context) => {
    const id = c.req.param("id");
    const idempotencyKey = c.req.header("Idempotency-Key");
    const rawBody = {}; // Empty body for cancel usually
    let requestHash = "";

    if (idempotencyKey) {
      requestHash = this.computeHash(rawBody);
      const record = getIdempotencyRecord(idempotencyKey);
      if (record) {
        if (record.request_hash !== requestHash) {
          return c.json(
            { detail: "Idempotency key reused with different parameters" },
            409,
          );
        }
        return c.json(JSON.parse(record.response_body), 200);
      }
    }

    logRequest("POST", `/checkout-sessions/${id}/cancel`, id, rawBody);

    const checkout = getCheckoutSession(id);
    if (!checkout) {
      return c.json({ detail: "Checkout session not found" }, 404);
    }

    if (
      checkout.status === CheckoutResponseStatusSchema.enum.completed ||
      checkout.status === CheckoutResponseStatusSchema.enum.canceled
    ) {
      return c.json(
        { detail: `Cannot cancel a ${checkout.status} checkout session` },
        409,
      );
    }

    checkout.status = CheckoutResponseStatusSchema.enum.canceled;
    saveCheckout(id, checkout.status, checkout);

    if (idempotencyKey) {
      saveIdempotencyRecord(
        idempotencyKey,
        requestHash,
        200,
        JSON.stringify(checkout),
      );
    }

    return c.json(checkout, 200);
  };

  shipOrder = async (orderId: string): Promise<void> => {
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
      line_items: [],
    });

    saveOrder(order.id, order);

    const checkout = getCheckoutSession(order.checkout_id);
    if (checkout) {
      await this.notifyWebhook(checkout, "order_shipped");
    }
  };
}
