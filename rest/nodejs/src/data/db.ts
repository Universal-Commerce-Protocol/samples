import Database from "better-sqlite3";

let productsDb: Database.Database | null = null;
let transactionsDb: Database.Database | null = null;

/**
 * Initializes the SQLite database connections for products and transactions.
 * Creates the necessary tables if they do not exist.
 *
 * @param productsPath Path to the products SQLite database file.
 * @param transactionsPath Path to the transactions SQLite database file.
 */
export function initDbs(productsPath: string, transactionsPath: string) {
  productsDb = new Database(productsPath);
  transactionsDb = new Database(transactionsPath);

  // Initialize Products DB schema
  productsDb.exec(`
    CREATE TABLE IF NOT EXISTS products (
      id TEXT PRIMARY KEY,
      title TEXT,
      price INTEGER,
      image_url TEXT
    )
  `);

  // Initialize Transactions DB schema
  transactionsDb.exec(`
    CREATE TABLE IF NOT EXISTS inventory (
      product_id TEXT PRIMARY KEY,
      quantity INTEGER DEFAULT 0
    )
  `);

  transactionsDb.exec(`
    CREATE TABLE IF NOT EXISTS checkouts (
      id TEXT PRIMARY KEY,
      status TEXT,
      data TEXT
    )
  `);

  transactionsDb.exec(`
    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY,
      data TEXT
    )
  `);

  transactionsDb.exec(`
    CREATE TABLE IF NOT EXISTS request_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      method TEXT,
      url TEXT,
      checkout_id TEXT,
      payload TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  transactionsDb.exec(`
    CREATE TABLE IF NOT EXISTS idempotency_keys (
      key TEXT PRIMARY KEY,
      request_hash TEXT,
      response_status INTEGER,
      response_body TEXT
    )
  `);
}

/**
 * Returns the initialized products database instance.
 * Throws an error if initDbs has not been called.
 *
 * @returns The better-sqlite3 Database instance for products.
 */
export function getProductsDb(): Database.Database {
  if (!productsDb) {
    throw new Error("Products DB not initialized. Call initDbs first.");
  }
  return productsDb;
}

/**
 * Returns the initialized transactions database instance.
 * Throws an error if initDbs has not been called.
 *
 * @returns The better-sqlite3 Database instance for transactions.
 */
export function getTransactionsDb(): Database.Database {
  if (!transactionsDb) {
    throw new Error("Transactions DB not initialized. Call initDbs first.");
  }
  return transactionsDb;
}
