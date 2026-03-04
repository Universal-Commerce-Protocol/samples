import { getTransactionsDb } from "./db";

/**
 * Retrieves the available inventory quantity for a given product.
 *
 * @param productId The ID of the product to check.
 * @returns The quantity available, or undefined if the product is not found in inventory.
 */
export function getInventory(productId: string): number | undefined {
  const db = getTransactionsDb();
  const stmt = db.prepare(
    "SELECT quantity FROM inventory WHERE product_id = ?",
  );
  const result = stmt.get(productId) as { quantity: number } | undefined;
  return result?.quantity;
}

/**
 * Attempts to reserve a specified quantity of stock for a product.
 * Decrements the inventory only if sufficient stock is available.
 *
 * @param productId The ID of the product.
 * @param quantity The amount to reserve (decrement).
 * @returns True if the stock was successfully reserved, false if there was insufficient stock.
 */
export function reserveStock(productId: string, quantity: number): boolean {
  const db = getTransactionsDb();
  // Use a transaction to ensure atomicity if needed, but a single update statement is atomic in SQLite.
  // We want to decrement quantity only if we have enough.
  const stmt = db.prepare(`
    UPDATE inventory
    SET quantity = quantity - ?
    WHERE product_id = ? AND quantity >= ?
  `);

  const info = stmt.run(quantity, productId, quantity);
  return info.changes > 0;
}

/**
 * Releases reserved stock back to the inventory.
 * Used for rollbacks or cancellations.
 *
 * @param productId The ID of the product.
 * @param quantity The amount to release (increment).
 */
export function releaseStock(productId: string, quantity: number): void {
  const db = getTransactionsDb();
  const stmt = db.prepare(`
    UPDATE inventory
    SET quantity = quantity + ?
    WHERE product_id = ?
  `);
  stmt.run(quantity, productId);
}
