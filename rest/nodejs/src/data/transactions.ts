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
  checkoutObj: ExtendedCheckoutResponse
): void {
  const db = getTransactionsDb();

  // Check if exists
  const existingStmt = db.prepare("SELECT id FROM checkouts WHERE id = ?");
  const existing = existingStmt.get(checkoutId);

  const dataStr = JSON.stringify(checkoutObj);

  if (existing) {
    const updateStmt = db.prepare(
      "UPDATE checkouts SET status = ?, data = ? WHERE id = ?"
    );
    updateStmt.run(status, dataStr, checkoutId);
  } else {
    const insertStmt = db.prepare(
      "INSERT INTO checkouts (id, status, data) VALUES (?, ?, ?)"
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
  checkoutId: string
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
      "INSERT INTO orders (id, data) VALUES (?, ?)"
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
  payload: unknown
): void {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "INSERT INTO request_logs (method, url, checkout_id, payload) VALUES (?, ?, ?, ?)"
  );
  stmt.run(method, url, checkoutId || null, JSON.stringify(payload));
}

export function getIdempotencyRecord(
  key: string
): IdempotencyRecord | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "SELECT key, request_hash, response_status, response_body FROM idempotency_keys WHERE key = ?"
  );
  return stmt.get(key) as IdempotencyRecord | undefined;
}

/**
 * Records the response for an idempotency key, unless one is already
 * recorded. Returns undefined when this call recorded it. Returns the
 * existing record when another request has already recorded this key: the
 * caller lost a concurrent race on the key and must answer with that record,
 * not with its own result.
 */
export function saveIdempotencyRecord(
  key: string,
  requestHash: string,
  status: number,
  responseBody: string
): IdempotencyRecord | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "INSERT INTO idempotency_keys (key, request_hash, response_status, response_body) VALUES (?, ?, ?, ?) ON CONFLICT(key) DO NOTHING"
  );
  const inserted =
    stmt.run(key, requestHash, status, responseBody).changes === 1;
  return inserted ? undefined : getIdempotencyRecord(key);
}

/**
 * Claims the idempotency key and persists the checkout in one transaction,
 * so a record is never left behind for a checkout that was not stored. Both
 * writes are synchronous, so unlike the read at the top of the handler they
 * can share a transaction. Returns undefined when this request won and the
 * checkout is stored. Returns the existing record when another request has
 * already claimed the key; nothing is written in that case.
 */
export function claimIdempotencyAndSaveCheckout(
  key: string,
  requestHash: string,
  status: number,
  responseBody: string,
  checkoutId: string,
  checkoutStatus: string,
  checkoutObj: ExtendedCheckoutResponse
): IdempotencyRecord | undefined {
  const db = getTransactionsDb();
  return db.transaction((): IdempotencyRecord | undefined => {
    const winner = saveIdempotencyRecord(
      key,
      requestHash,
      status,
      responseBody
    );
    if (winner) {
      return winner;
    }
    saveCheckout(checkoutId, checkoutStatus, checkoutObj);
    return undefined;
  })();
}
