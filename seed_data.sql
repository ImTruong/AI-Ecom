-- Master Seed Data for Enterprise Product Structure
-- Handle 10 categories and polymorphic products

-- 1. Clear existing data
DELETE FROM products_book;
DELETE FROM products_clothes;
DELETE FROM products_laptop;
DELETE FROM products_phone;
DELETE FROM products_tablet;
DELETE FROM products_camera;
DELETE FROM products_headphone;
DELETE FROM products_watch;
DELETE FROM products_shoe;
DELETE FROM products_furniture;
DELETE FROM products;
DELETE FROM categories;

-- 2. Seed Categories
INSERT INTO categories (name, slug, description, icon) VALUES
('Books', 'books', 'Books, E-books and Audiobooks', 'book'),
('Clothes', 'clothes', 'Fashion and Apparel', 'tshirt'),
('Laptops', 'laptops', 'High-performance computing', 'laptop'),
('Phones', 'phones', 'Smartphones and Accessories', 'mobile-alt'),
('Tablets', 'tablets', 'Portable touch devices', 'tablet-alt'),
('Cameras', 'cameras', 'Professional and hobbyist photography', 'camera'),
('Headphones', 'headphones', 'Audio and music gear', 'headphones'),
('Watches', 'watches', 'Analog and Smart watches', 'clock'),
('Shoes', 'shoes', 'Footwear for all occasions', 'shoe-prints'),
('Furniture', 'furniture', 'Home and Office furniture', 'couch');

-- 3. Seed Products (Base Table)
-- We need to insert into 'products' first, then into specific tables.
-- Using IDs starting from 100 for clarity

-- Book
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (101, (SELECT id FROM categories WHERE slug='books'), 'Clean Code', 'A Handbook of Agile Software Craftsmanship', 450000, 'https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg', 1, true, NOW(), NOW());
INSERT INTO products_book (product_ptr_id, author, isbn, publisher, page_count)
VALUES (101, 'Robert C. Martin', '978-0132350884', 'Prentice Hall', 464);

-- Laptop
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (102, (SELECT id FROM categories WHERE slug='laptops'), 'MacBook Pro M2', 'Powerful laptop for professionals', 35000000, 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mbp-spacegray-select-202206?wid=904&hei=840&fmt=jpeg&qlt=90&.v=1664497359473', 2, true, NOW(), NOW());
INSERT INTO products_laptop (product_ptr_id, cpu, ram, storage, gpu)
VALUES (102, 'Apple M2 Pro', 16, '512GB SSD', '16-core GPU');

-- Phone
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (103, (SELECT id FROM categories WHERE slug='phones'), 'iPhone 14 Pro', 'Dynamic Island, 48MP Camera', 25000000, 'https://m.media-amazon.com/images/I/61XO4bORHUL._AC_SL1500_.jpg', 2, true, NOW(), NOW());
INSERT INTO products_phone (product_ptr_id, screen_size, battery, camera_specs)
VALUES (103, '6.1 inch OLED', 3200, '48MP Main, 12MP Ultra Wide');

-- Clothes
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (104, (SELECT id FROM categories WHERE slug='clothes'), 'Git Hero Hoodie', 'Stay comfortable while coding', 550000, 'https://m.media-amazon.com/images/I/61k7B6kE-L._AC_UX679_.jpg', 3, true, NOW(), NOW());
INSERT INTO products_clothes (product_ptr_id, brand, material, gender)
VALUES (104, 'DevStyle', 'Cotton/Polyester', 'Unisex');

-- Tablet
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (105, (SELECT id FROM categories WHERE slug='tablets'), 'iPad Air', 'Light, bright, full of might', 15000000, 'https://m.media-amazon.com/images/I/61XZQXFQ36L._AC_SL1500_.jpg', 2, true, NOW(), NOW());
INSERT INTO products_tablet (product_ptr_id, screen_size, os, is_stylus_supported)
VALUES (105, '10.9 inch Liquid Retina', 'iPadOS', true);

-- Camera
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (106, (SELECT id FROM categories WHERE slug='cameras'), 'Sony A7 IV', 'The basic has never been this good', 60000000, 'https://m.media-amazon.com/images/I/718W93+D-OL._AC_SL1500_.jpg', 4, true, NOW(), NOW());
INSERT INTO products_camera (product_ptr_id, resolution, sensor_type, lens_included)
VALUES (106, '33MP', 'Full-frame CMOS', 'Body Only');

-- Headphone
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (107, (SELECT id FROM categories WHERE slug='headphones'), 'Sony WH-1000XM5', 'Industry-leading noise cancelling', 8000000, 'https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1200_.jpg', 4, true, NOW(), NOW());
INSERT INTO products_headphone (product_ptr_id, type, is_wireless, noise_cancelling)
VALUES (107, 'Over-ear', true, true);

-- Watch
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (108, (SELECT id FROM categories WHERE slug='watches'), 'Apple Watch Ultra', 'The ultimate sports watch', 20000000, 'https://m.media-amazon.com/images/I/91zI7SNo6XL._AC_SL1500_.jpg', 2, true, NOW(), NOW());
INSERT INTO products_watch (product_ptr_id, style, water_resistance, band_material)
VALUES (108, 'Smart', '100m', 'Ocean Band');

-- Shoe
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (109, (SELECT id FROM categories WHERE slug='shoes'), 'Nike Air Max', 'Classic comfort with style', 3000000, 'https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/603ed60b-f35c-4384-8186-508b98b9a1a0/air-max-270-shoes-V4D79L.png', 5, true, NOW(), NOW());
INSERT INTO products_shoe (product_ptr_id, size_eu, material, shoe_type)
VALUES (109, 42, 'Mesh/Synthetic', 'Sneaker');

-- Furniture
INSERT INTO products (id, category_id, name, description, price, image_url, supplier_id, is_active, created_at, updated_at)
VALUES (110, (SELECT id FROM categories WHERE slug='furniture'), 'Ergonomic Chair', 'Built for long working hours', 5000000, 'https://m.media-amazon.com/images/I/718yG7XonfL._AC_SL1500_.jpg', 6, true, NOW(), NOW());
INSERT INTO products_furniture (product_ptr_id, material, dimensions, weight_capacity)
VALUES (110, 'Breathable Mesh', '70x70x120cm', '150kg');
