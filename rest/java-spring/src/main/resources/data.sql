DELETE FROM products;
DELETE FROM inventory;
DELETE FROM promotions;
DELETE FROM shipping_rates;
DELETE FROM discounts;
DELETE FROM addresses;

INSERT INTO products (id, title, price) VALUES 
('bouquet_roses', 'Bouquet of Red Roses', 3500),
('pot_ceramic', 'Ceramic Pot', 1500),
('bouquet_sunflowers', 'Sunflower Bundle', 2500),
('bouquet_tulips', 'Spring Tulips', 3000),
('orchid_white', 'White Orchid', 4500),
('gardenias', 'Gardenias', 2000);

INSERT INTO inventory (product_id, quantity) VALUES 
('bouquet_roses', 1000),
('pot_ceramic', 2000),
('bouquet_sunflowers', 500),
('bouquet_tulips', 1500),
('orchid_white', 800),
('gardenias', 0);

INSERT INTO promotions (id, title, type, subtotal_threshold) VALUES 
('promo_1', 'Free Shipping on orders over $100', 'free_shipping', 10000);
-- ('promo_2', 'Free Shipping on Rose Bouquets', 'free_shipping', , '["bouquet_roses"]'); -- eligible_item_ids not supported yet

INSERT INTO shipping_rates (id, country_code, service_level, title, price) VALUES 
('std-ship', 'default', 'standard', 'Standard Shipping', 500),
('exp-ship-us', 'US', 'express', 'Express Shipping (US)', 1500),
('exp-ship-intl', 'default', 'express', 'International Express', 2500);

INSERT INTO discounts (code, type, discount_value, description) VALUES 
('10OFF', 'percentage', 10, '10% Off'),
('WELCOME20', 'percentage', 20, '20% Off'),
('FIXED500', 'fixed_amount', 500, '$5.00 Off');

INSERT INTO addresses (id, customer_email, street_address, city, state, postal_code, country) VALUES
('addr_1', 'john.doe@example.com', '123 Main St', 'Springfield', 'IL', '62704', 'US'),
('addr_2', 'john.doe@example.com', '456 Oak Ave', 'Metropolis', 'NY', '10012', 'US'),
('addr_3', 'jane.smith@example.com', '789 Pine Ln', 'Smallville', 'KS', '66002', 'US');
