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
    "SELECT id, title, price, image_url FROM products WHERE id = ?"
  );
  const result = stmt.get(productId) as Product | undefined;
  return result;
}
