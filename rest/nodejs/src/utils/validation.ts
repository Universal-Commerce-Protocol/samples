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

import { type Context, type Env } from "hono";
import * as z from "zod";

import { UcpError, ucpErrorResponse } from "./ucp_error";

/**
 * Middleware to handle Zod validation results.
 * Logs the validation status and returns a 422 error with a pretty-printed message if validation fails.
 *
 * @param result - The result of the Zod validation.
 * @param c - The Hono context.
 * @returns A response object if validation fails, otherwise void (implied continuation).
 */
const formatPath = (path: (string | number)[]) => {
  return path.reduce((acc, val) => {
    if (typeof val === "number") {
      return `${acc}[${val}]`;
    }
    return acc ? `${acc}.${val}` : String(val);
  }, "");
};

export function prettyValidation<T>(
  result:
    | { success: true; data: T; target: string }
    | {
        success: false;
        data: T;
        target: string;
        error: z.ZodError;
      },
  c: Context
) {
  if (result.success) {
    c.var.logger.info(
      `Request payload (${result.target}) passed validation:\n${JSON.stringify(result.data, null, 2)}`
    );
  } else {
    c.var.logger.warn("Request payload failed validation");
    c.var.logger.warn(
      `Request payload:\n${JSON.stringify(result.data, null, 2)}`
    );
    const prettyError = result.error.issues
      .map((issue) => {
        const path = formatPath(issue.path);
        return `✖ ${issue.message}\n  → at ${path}`;
      })
      .join("\n");

    c.var.logger.warn(prettyError);
    // checkout-rest.md shapes protocol errors as a JSON body carrying code and
    // content inside the UCP envelope. A request rejected by payload validation
    // is a protocol error like any other, so it answers in that shape; the
    // pretty diagnostic stays, as the envelope's content.
    return ucpErrorResponse(c, new UcpError(prettyError, "INVALID_REQUEST", 422));
  }
}

/**
 * Schema for validating route parameters containing an ID.
 */
export const IdParamSchema = z.object({
  id: z.string(),
});

export type IdParamContext = Context<
  Env,
  string,
  {
    in: { param: z.input<typeof IdParamSchema> };
    out: { param: z.output<typeof IdParamSchema> };
  }
>;
