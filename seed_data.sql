-- ===========================================
-- MASTER SEED DATA FOR TRUONGSHOP
-- ===========================================

-- 1. AUTH SERVICE (auth_db)
INSERT INTO customers (id, email, password_hash, full_name, is_active, created_at, updated_at)
VALUES (1, 'customer@truongshop.com', 'pbkdf2_sha256$600000$randomsalt123$abcdefghijklmnopqrstuvwxyz1234567890', 'Nguyễn Văn Khách', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO staff (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
VALUES (1, 'staff@truongshop.com', 'pbkdf2_sha256$600000$randomsalt456$abcdefghijklmnopqrstuvwxyz0987654321', 'Trần Thị Nhân Viên', 'admin', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. SUPPLIER SERVICE (supplier_db)
INSERT INTO suppliers (id, name, email, phone, address, created_at, updated_at)
VALUES 
(1, 'Books Wholesale Co', 'sales@bw.com', '555-0111', '123 Main St', NOW(), NOW()),
(2, 'Global Textiles', 'info@gt.com', '555-0222', '456 Textile Blvd', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 3. PRODUCT SERVICE (product_db)
INSERT INTO categories (id, name, description, created_at)
VALUES 
(1, 'Programming', 'Books and items for developers', NOW()),
(2, 'T-Shirt', 'Stylish developer t-shirts', NOW()),
(3, 'Self-Help', 'Books for personal growth and productivity', NOW()),
(4, 'Hoodie', 'Warm and stylish hoodies', NOW()),
(5, 'Accessories', 'Tech accessories and more', NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO products (id, name, description, price, product_type, category_obj_id, image_url, supplier_id, attributes, is_active, created_at, updated_at)
VALUES 
(1, 'Clean Code', 'A Handbook of Agile Software Craftsmanship.', 450000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg', 1, '{"author": "Robert C. Martin"}', true, NOW(), NOW()),
(2, 'The Pragmatic Programmer', 'Your Journey To Mastery.', 520000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/51cUVaBWZzL._SX396_BO1,204,203,200_.jpg', 1, '{"author": "Andrew Hunt"}', true, NOW(), NOW()),
(3, 'Developer T-Shirt', 'Comfortable cotton t-shirt.', 299000, 'clothes', 2, 'https://i.pinimg.com/originals/a3/18/64/a318643ad39b00dca6de73e901d2169c.jpg', 2, '{}', true, NOW(), NOW()),
(4, 'Programmer Hoodie', 'Warm hoodie with code design.', 599000, 'clothes', 4, 'https://images-na.ssl-images-amazon.com/images/I/61kFGcrHSQL._UX466_.jpg', 2, '{}', true, NOW(), NOW()),
(10, 'Introduction to Algorithms', 'The Bible of algorithms.', 1200000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/41T077EHWGL._SX412_BO1,204,203,200_.jpg', 1, '{"author": "CLRS"}', true, NOW(), NOW()),
(11, 'Design Patterns', 'Reusable Object-Oriented Software.', 850000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/51szY7S9SXL._SX395_BO1,204,203,200_.jpg', 1, '{"author": "Gang of Four"}', true, NOW(), NOW()),
(12, 'Refactoring', 'Improving Existing Code.', 950000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/41S7iWreAgL._SX395_BO1,204,203,200_.jpg', 1, '{"author": "Martin Fowler"}', true, NOW(), NOW()),
(13, 'Python Crash Course', 'Project-Based Introduction.', 450000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/51Hh410SxvL._SX379_BO1,204,203,200_.jpg', 1, '{"author": "Eric Matthes"}', true, NOW(), NOW()),
(14, 'Soft Skills', 'The developer life manual.', 350000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/4102-Y98fKL._SX331_BO1,204,203,200_.jpg', 1, '{"author": "John Sonmez"}', true, NOW(), NOW()),
(15, 'Deep Work', 'Rules for Focused Success.', 250000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/417P6UQC0CL._SX326_BO1,204,203,200_.jpg', 1, '{"author": "Cal Newport"}', true, NOW(), NOW()),
(16, 'Atomic Habits', 'Build Good Habits.', 280000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/51-nXsSRfZL._SX328_BO1,204,203,200_.jpg', 1, '{"author": "James Clear"}', true, NOW(), NOW()),
(17, 'Linux Terminal T-Shirt', '$ sudo rm -rf / print.', 250000, 'clothes', 2, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(18, 'Git Hero Hoodie', 'git commit -m "Save life".', 550000, 'clothes', 4, 'https://m.media-amazon.com/images/I/61k7B6kE-L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(19, 'Cyber Security Cap', 'Protect your head.', 150000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(20, 'JavaScript Ninja T-Shirt', 'Show your JS mastery.', 270000, 'clothes', 2, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(21, 'Docker Container Socks', 'Keep your feet isolated.', 120000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(22, 'Code Review Mug', 'Drink coffee, find bugs.', 180000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(23, 'Desk Mat', 'Large desk mat.', 350000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(24, 'Binary Code Jacket', 'Stylish jacket.', 890000, 'clothes', 4, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO product_variants (id, product_id, name, price_override, stock, sku, options)
VALUES
(1, 1, 'Hardcover', NULL, 25, 'BK-CC-01', '{"format": "Hardcover"}'),
(2, 1, 'E-book', 300000, 100, 'BK-CC-02', '{"format": "E-book"}'),
(3, 2, 'Paperback', NULL, 18, 'BK-PP-01', '{"format": "Paperback"}'),
(4, 3, 'Black, S', NULL, 10, 'CL-DT-BS', '{"color": "Black", "size": "S"}'),
(5, 3, 'Black, M', NULL, 15, 'CL-DT-BM', '{"color": "Black", "size": "M"}'),
(10, 10, 'Hardcover', NULL, 10, 'BK-ALGO-H', '{"format": "Hardcover"}'),
(11, 11, 'Paperback', NULL, 15, 'BK-DP-P', '{"format": "Paperback"}'),
(12, 12, 'Hardcover', NULL, 20, 'BK-REF-H', '{"format": "Hardcover"}'),
(13, 13, 'Paperback', NULL, 50, 'BK-PY-P', '{"format": "Paperback"}'),
(14, 14, 'E-book', 150000, 100, 'BK-SS-E', '{"format": "E-book"}'),
(15, 15, 'Paperback', NULL, 30, 'BK-DW-P', '{"format": "Paperback"}'),
(16, 16, 'Paperback', NULL, 40, 'BK-AH-P', '{"format": "Paperback"}'),
(17, 17, 'Black, L', NULL, 25, 'CL-LINUX-L', '{"color": "Black", "size": "L"}'),
(18, 18, 'Black, XL', NULL, 15, 'CL-GIT-XL', '{"color": "Black", "size": "XL"}'),
(19, 19, 'Universal', NULL, 100, 'CL-CAP-U', '{"size": "Universal"}'),
(20, 20, 'Yellow, M', NULL, 30, 'CL-JS-M', '{"color": "Yellow", "size": "M"}'),
(21, 21, 'Universal', NULL, 50, 'CL-SOCK-U', '{"size": "Universal"}'),
(22, 22, 'White', NULL, 20, 'CL-MUG-W', '{"color": "White"}'),
(23, 23, 'Extra Large', NULL, 15, 'CL-MAT-XL', '{"size": "XL"}'),
(24, 24, 'Black, M', NULL, 10, 'CL-JACK-M', '{"color": "Black", "size": "M"}')
ON CONFLICT (id) DO NOTHING;

-- 4. RATING SERVICE (rating_db)
INSERT INTO ratings (order_id, customer_id, product_type, product_id, product_name, stars, comment, created_at)
VALUES 
(1, 1, 'book', 1, 'Clean Code', 5, 'Exceptional book!', NOW())
ON CONFLICT DO NOTHING;

-- 5. CUSTOMER SERVICE (customer_db)
INSERT INTO customers (auth_customer_id, email, full_name, is_active, created_at, updated_at)
VALUES (1, 'customer@truongshop.com', 'Nguyễn Văn Khách', true, NOW(), NOW())
ON CONFLICT (auth_customer_id) DO NOTHING;

-- ===========================================
-- DISTRIBUTED PRODUCT SEEDS (For specialized services)
-- ===========================================

-- 6. Diversified Product Data for the 10 New Services
-- (These will be skips in containers that don't have matching local tables, 
-- but will populate correctly in the specific service containers)

INSERT INTO products (id, name, description, price, product_type, category_obj_id, image_url, supplier_id, attributes, is_active, created_at, updated_at)
VALUES 
(30, 'MacBook Air M2', 'Thin and light powerful laptop.', 32000000, 'laptop', 1, 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=500', 1, '{"cpu": "M2", "ram": "8GB"}', true, NOW(), NOW()),
(31, 'Surface Laptop 5', 'Elegant and powerful.', 28000000, 'laptop', 1, 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=500', 1, '{"os": "Windows 11"}', true, NOW(), NOW()),
(40, 'Galaxy S23 Ultra', 'The ultimate smartphone.', 25000000, 'phone', 1, 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500', 1, '{"camera": "200MP", "storage": "512GB"}', true, NOW(), NOW()),
(41, 'Google Pixel 8', 'The smartest phone.', 20000000, 'phone', 1, 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500', 1, '{"chip": "Tensor G3"}', true, NOW(), NOW()),
(50, 'iPad Pro 12.9', 'The most capable tablet.', 30000000, 'tablet', 1, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500', 1, '{"screen": "Liquid Retina XDR"}', true, NOW(), NOW()),
(60, 'Sony A7 IV', 'The hybrid master camera.', 62000000, 'camera', 1, 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500', 1, '{"sensor": "Full Frame"}', true, NOW(), NOW()),
(70, 'WH-1000XM5', 'Industry-leading noise cancelling.', 8000000, 'headphone', 1, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500', 1, '{"battery": "30h"}', true, NOW(), NOW()),
(80, 'Apple Watch Ultra', 'The most rugged watch.', 19000000, 'watch', 1, 'https://images.unsplash.com/photo-1544117518-30df57809ca7?w=500', 1, '{"gps": "Dual Frequency"}', true, NOW(), NOW()),
(90, 'Air Jordan 1', 'The iconic sneaker.', 4500000, 'shoe', 1, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500', 2, '{"color": "Red/White"}', true, NOW(), NOW()),
(100, 'Standing Desk', 'Adjustable height desk.', 12000000, 'furniture', 1, 'https://images.unsplash.com/photo-1595515106969-1ce29566ff1c?w=500', 2, '{"material": "Wood"}', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO product_variants (id, product_id, name, price_override, stock, sku, options)
VALUES
(30, 30, 'Silver', NULL, 10, 'LP-MA-S', '{"color": "Silver"}'),
(31, 31, 'Black', NULL, 5, 'LP-SL-B', '{"color": "Black"}'),
(40, 40, 'Green', NULL, 20, 'PH-GS-G', '{"color": "Green"}'),
(41, 41, 'Rose', NULL, 15, 'PH-GP-R', '{"color": "Rose"}'),
(50, 50, 'Space Gray', NULL, 5, 'TB-IP-S', '{"color": "Space Gray"}'),
(60, 60, 'Body Only', NULL, 3, 'CM-SA-B', '{"package": "Body"}'),
(70, 70, 'Midnight', NULL, 50, 'HP-WH-M', '{"color": "Midnight"}'),
(80, 80, 'Alpine Loop', NULL, 10, 'WT-AW-A', '{"strap": "Alpine"}'),
(90, 90, 'Size 42', NULL, 25, 'SH-AJ-42', '{"size": "42"}'),
(100, 100, 'Walnut', NULL, 5, 'FR-SD-W', '{"finish": "Walnut"}')
ON CONFLICT (id) DO NOTHING;
