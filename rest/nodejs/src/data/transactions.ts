import { type ExtendedCheckoutResponse, type Order } from "../models";

import { getTransactionsDb } from "./db";

/**
 * Represents the structure of a checkout session stored in the database.
 */
export interface CheckoutSession {
  id: string;
  status: string;
  data: string; // JSON string
}

export interface IdempotencyRecord {
  key: string;
  request_hash: string;
  response_status: number;
  response_body: string;
}

/**
 * Saves or updates a checkout session in the database.
 * If a session with the given ID exists, it updates it; otherwise, it creates a
 * new one.
 *
 * @param checkoutId The unique identifier for the checkout session.
 * @param status The current status of the checkout (e.g., 'in_progress',
 *     'completed').
 * @param checkoutObj The full checkout object to be serialized and stored.
 */
export function saveCheckout(
  checkoutId: string,
  status: string,
  checkoutObj: ExtendedCheckoutResponse,
): void {
  const db = getTransactionsDb();

  // Check if exists
  const existingStmt = db.prepare("SELECT id FROM checkouts WHERE id = ?");
  const existing = existingStmt.get(checkoutId);

  const dataStr = JSON.stringify(checkoutObj);

  if (existing) {
    const updateStmt = db.prepare(
      "UPDATE checkouts SET status = ?, data = ? WHERE id = ?",
    );
    updateStmt.run(status, dataStr, checkoutId);
  } else {
    const insertStmt = db.prepare(
      "INSERT INTO checkouts (id, status, data) VALUES (?, ?, ?)",
    );
    insertStmt.run(checkoutId, status, dataStr);
  }
}

/**
 * Retrieves a checkout session from the database by its ID.
 * Parses the stored JSON data into a Checkout object.
 *
 * @param checkoutId The unique identifier of the checkout session.
 * @returns The Checkout object if found and successfully parsed, otherwise
 *     undefined.
 */
export function getCheckoutSession(
  checkoutId: string,
): ExtendedCheckoutResponse | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare("SELECT data FROM checkouts WHERE id = ?");
  const result = stmt.get(checkoutId) as { data: string } | undefined;

  if (result) {
    try {
      return JSON.parse(result.data) as ExtendedCheckoutResponse;
    } catch (e) {
      console.error("Failed to parse checkout data", e);
      return undefined;
    }
  }
  return undefined;
}

export function saveOrder(orderId: string, orderObj: Order): void {
  const db = getTransactionsDb();
  const dataStr = JSON.stringify(orderObj);

  const existingStmt = db.prepare("SELECT id FROM orders WHERE id = ?");
  const existing = existingStmt.get(orderId);

  if (existing) {
    const updateStmt = db.prepare("UPDATE orders SET data = ? WHERE id = ?");
    updateStmt.run(dataStr, orderId);
  } else {
    const insertStmt = db.prepare(
      "INSERT INTO orders (id, data) VALUES (?, ?)",
    );
    insertStmt.run(orderId, dataStr);
  }
}

export function getOrder(orderId: string): Order | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare("SELECT data FROM orders WHERE id = ?");
  const result = stmt.get(orderId) as { data: string } | undefined;

  if (result) {
    try {
      return JSON.parse(result.data) as Order;
    } catch (e) {
      console.error("Failed to parse order data", e);
      return undefined;
    }
  }
  return undefined;
}

export function logRequest(
  method: string,
  url: string,
  checkoutId: string | undefined,
  payload: unknown,
): void {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "INSERT INTO request_logs (method, url, checkout_id, payload) VALUES (?, ?, ?, ?)",
  );
  stmt.run(method, url, checkoutId || null, JSON.stringify(payload));
}

export function getIdempotencyRecord(
  key: string,
): IdempotencyRecord | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "SELECT key, request_hash, response_status, response_body FROM idempotency_keys WHERE key = ?",
  );
  return stmt.get(key) as IdempotencyRecord | undefined;
}

export function saveIdempotencyRecord(
  key: string,
  requestHash: string,
  status: number,
  responseBody: string,
): void {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "INSERT OR REPLACE INTO idempotency_keys (key, request_hash, response_status, response_body) VALUES (?, ?, ?, ?)",
  );
  stmt.run(key, requestHash, status, responseBody);
}
