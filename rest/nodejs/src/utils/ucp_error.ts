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
import { type ContentfulStatusCode } from "hono/utils/http-status";

import { UCP_VERSION } from "./config";

// UCP error taxonomy, mirroring the Python reference server
// (rest/python/server/exceptions.py). Business and protocol failures answer
// with the UCP error envelope — `ucp.status: "error"` plus a `messages[]`
// entry carrying `code`, `content`, and `severity` — rather than a flat
// `{ detail }` body, per checkout.md's error responses ("the response
// contains `ucp.status: \"error\"` with `messages` describing the failure")
// and checkout-rest.md's protocol errors ("JSON body containing `code` and
// `content`").

export type ErrorSeverity =
  | "recoverable"
  | "requires_buyer_input"
  | "requires_buyer_review"
  | "unrecoverable";

export class UcpError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: ContentfulStatusCode,
    public readonly severity: ErrorSeverity = "unrecoverable"
  ) {
    super(message);
    this.name = new.target.name;
  }
}

export class ResourceNotFoundError extends UcpError {
  constructor(message: string) {
    super(message, "RESOURCE_NOT_FOUND", 404);
  }
}

export class IdempotencyConflictError extends UcpError {
  constructor(message: string) {
    super(message, "IDEMPOTENCY_CONFLICT", 409);
  }
}

export class CheckoutNotModifiableError extends UcpError {
  constructor(message: string) {
    super(message, "CHECKOUT_NOT_MODIFIABLE", 409);
  }
}

export class OutOfStockError extends UcpError {
  constructor(message: string, statusCode: ContentfulStatusCode = 400) {
    super(message, "OUT_OF_STOCK", statusCode);
  }
}

export class PaymentFailedError extends UcpError {
  constructor(
    message: string,
    code = "PAYMENT_FAILED",
    statusCode: ContentfulStatusCode = 402
  ) {
    super(message, code, statusCode, "requires_buyer_input");
  }
}

export class InvalidRequestError extends UcpError {
  constructor(message: string) {
    super(message, "INVALID_REQUEST", 400);
  }
}

/**
 * Renders a UcpError as the UCP error envelope, byte-shape-identical to the
 * Python reference's ucp_exception_handler (rest/python/server/server.py).
 */
export function ucpErrorResponse(c: Context, error: UcpError) {
  return c.json(
    {
      ucp: {
        version: UCP_VERSION,
        status: "error",
      },
      messages: [
        {
          type: "error",
          code: error.code,
          content: error.message,
          severity: error.severity,
        },
      ],
    },
    error.statusCode
  );
}
