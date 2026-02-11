import { type Context } from "hono";
import * as z from "zod";

/**
 * Middleware to handle Zod validation results.
 * Logs the validation status and returns a 422 error with a pretty-printed message if validation fails.
 *
 * @param result - The result of the Zod validation.
 * @param c - The Hono context.
 * @returns A response object if validation fails, otherwise void (implied continuation).
 */
export function prettyValidation<T>(
  result:
    | { success: true; data: T; target: string }
    | { success: false; error: any },
  c: Context,
) {
  if (result.success) {
    c.var.logger.info(
      `Request payload (${result.target}) passed validation:\n${JSON.stringify(result.data, null, 2)}`,
    );
  } else {
    c.var.logger.warn("Request payload failed validation");
    c.var.logger.warn(
      `Request payload:\n${JSON.stringify(c.req.json(), null, 2)}`,
    );
    const prettyError = z.prettifyError(result.error);

    c.var.logger.warn(prettyError);
    return c.text(prettyError, 422);
  }
}

/**
 * Schema for validating route parameters containing an ID.
 */
export const IdParamSchema = z.object({
  id: z.string(),
});
