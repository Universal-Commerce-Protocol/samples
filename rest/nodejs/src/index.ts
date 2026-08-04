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

import { serve } from "@hono/node-server";
import { zValidator } from "@hono/zod-validator";
import { type Context, Hono } from "hono";
import { requestId } from "hono/request-id";
import { pinoHttp } from "pino-http";

import { CheckoutService } from "./api/checkout";
import { DiscoveryService } from "./api/discovery";
import { OrderService } from "./api/order";
import { TestingService } from "./api/testing";
import { initDbs } from "./data/db";
import {
  ExtendedCheckoutCreateRequestSchema,
  ExtendedCheckoutUpdateRequestSchema,
  CheckoutCompleteRequestSchema,
  OrderSchema,
} from "./models";
import { verifySignature } from "./utils/signature";
import { IdParamSchema, prettyValidation } from "./utils/validation";

const app = new Hono();

initDbs("databases/products.db", "databases/transactions.db");

const checkoutService = new CheckoutService();
const orderService = new OrderService();
const discoveryService = new DiscoveryService();
const testingService = new TestingService(checkoutService);

// Setup logging for each request
app.use(requestId());
app.use(async (c: Context, next: () => Promise<void>) => {
  c.env.incoming.id = c.var.requestId;

  await new Promise<void>((resolve) =>
    pinoHttp({
      quietReqLogger: true,
      transport: {
        target: "pino-http-print",
        options: {
          destination: 1,
          all: true,
          translateTime: true,
        },
      },
    })(c.env.incoming, c.env.outgoing, () => resolve())
  );

  c.set("logger", c.env.incoming.log);

  await next();
});

// Middleware for Version Negotiation
app.use(async (c: Context, next: () => Promise<void>) => {
  const ucpAgent = c.req.header("UCP-Agent");
  if (ucpAgent) {
    // Simple regex to find version="YYYY-MM-DD"
    const match = ucpAgent.match(/version="([^"]+)"/);
    if (match) {
      const clientVersion = match[1];
      const serverVersion = discoveryService.ucpVersion;
      // Simple string comparison for now, assuming ISO dates.
      // Ideally we'd parse and check compatibility.
      if (clientVersion > serverVersion) {
        return c.json(
          {
            ucp: {
              version: serverVersion,
              status: "error",
            },
            messages: [
              {
                type: "error",
                code: "VERSION_UNSUPPORTED",
                content: `Version ${clientVersion} is not supported. This merchant implements version ${serverVersion}.`,
                severity: "unrecoverable",
              },
            ],
          },
          422
        );
      }
    }
  }
  await next();
});

/* Discovery endpoints */
// The discovery profile is served unverified: it is the public document a
// platform must be able to read before it can sign anything.
app.get("/.well-known/ucp", discoveryService.getMerchantProfile);

/* Checkout Capability endpoints */
// Every business endpoint below verifies RFC 9421 request signatures via
// verifySignature (enforced when REQUIRE_SIGNATURES=true, verify-and-log
// otherwise), mirroring the Python reference server.
app.post(
  "/checkout-sessions",
  verifySignature,
  zValidator("json", ExtendedCheckoutCreateRequestSchema, prettyValidation),
  checkoutService.createCheckout
);
app.get(
  "/checkout-sessions/:id",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  checkoutService.getCheckout
);
app.put(
  "/checkout-sessions/:id",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  zValidator("json", ExtendedCheckoutUpdateRequestSchema, prettyValidation),
  checkoutService.updateCheckout
);
app.post(
  "/checkout-sessions/:id/complete",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  zValidator("json", CheckoutCompleteRequestSchema, prettyValidation),
  checkoutService.completeCheckout
);
app.post(
  "/checkout-sessions/:id/cancel",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  checkoutService.cancelCheckout
);

/* Order Capability endpoints */
app.get(
  "/orders/:id",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  orderService.getOrder
);
app.put(
  "/orders/:id",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  zValidator("json", OrderSchema, prettyValidation),
  orderService.updateOrder
);

/* Testing endpoints */
app.post(
  "/testing/simulate-shipping/:id",
  verifySignature,
  zValidator("param", IdParamSchema, prettyValidation),
  testingService.shipOrder
);

serve(
  {
    fetch: app.fetch,
    port: 3000,
  },
  (info) => {
    console.log(`Server is running on http://localhost:${info.port}`);
  }
);
