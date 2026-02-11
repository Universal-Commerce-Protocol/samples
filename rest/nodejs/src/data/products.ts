import { getProductsDb } from "./db";

/**
 * Represents a product in the catalog.
 */
export interface Product {
  id: string;
  title: string;
  price: number; // Price in cents
  image_url: string | undefined;
}

/**
 * Retrieves a product from the database by its ID.
 *
 * @param productId The unique identifier of the product.
 * @returns The Product object if found, otherwise undefined.
 */
export function getProduct(productId: string): Product | undefined {
  const db = getProductsDb();
  const stmt = db.prepare(
    "SELECT id, title, price, image_url FROM products WHERE id = ?",
  );
  const result = stmt.get(productId) as Product | undefined;
  return result;
}
