-- Extra Seed Data for TruongShop

-- 1. Insert new categories
INSERT INTO categories (id, name, description, created_at)
VALUES 
(3, 'Self-Help', 'Books for personal growth and productivity', NOW()),
(4, 'Hoodie', 'Warm and stylish hoodies', NOW()),
(5, 'Accessories', 'Tech accessories and more', NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. Insert 15 more products using category_obj_id
INSERT INTO products (id, name, description, price, product_type, category_obj_id, image_url, supplier_id, attributes, is_active, created_at, updated_at)
VALUES 
(10, 'Introduction to Algorithms', 'The Bible of algorithms covering everything from basics to advanced topics.', 1200000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/41T077EHWGL._SX412_BO1,204,203,200_.jpg', 1, '{"author": "CLRS", "isbn": "978-0262033848"}', true, NOW(), NOW()),
(11, 'Design Patterns', 'Elements of Reusable Object-Oriented Software. The foundation of modern software design.', 850000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/51szY7S9SXL._SX395_BO1,204,203,200_.jpg', 1, '{"author": "Gang of Four", "isbn": "978-0201633610"}', true, NOW(), NOW()),
(12, 'Refactoring', 'Improving the Design of Existing Code by Martin Fowler.', 950000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/41S7iWreAgL._SX395_BO1,204,203,200_.jpg', 1, '{"author": "Martin Fowler", "isbn": "978-0134757599"}', true, NOW(), NOW()),
(13, 'Python Crash Course', 'A Hands-On, Project-Based Introduction to Programming.', 450000, 'book', 1, 'https://images-na.ssl-images-amazon.com/images/I/51Hh410SxvL._SX379_BO1,204,203,200_.jpg', 1, '{"author": "Eric Matthes", "isbn": "978-1593279288"}', true, NOW(), NOW()),
(14, 'Soft Skills', 'The software developer''s life manual.', 350000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/4102-Y98fKL._SX331_BO1,204,203,200_.jpg', 1, '{"author": "John Sonmez", "isbn": "978-1617292392"}', true, NOW(), NOW()),
(15, 'Deep Work', 'Rules for Focused Success in a Distracted World.', 250000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/417P6UQC0CL._SX326_BO1,204,203,200_.jpg', 1, '{"author": "Cal Newport", "isbn": "978-1455586691"}', true, NOW(), NOW()),
(16, 'Atomic Habits', 'An Easy & Proven Way to Build Good Habits & Break Bad Ones.', 280000, 'book', 3, 'https://images-na.ssl-images-amazon.com/images/I/51-nXsSRfZL._SX328_BO1,204,203,200_.jpg', 1, '{"author": "James Clear", "isbn": "978-0735211292"}', true, NOW(), NOW()),
(17, 'Linux Terminal T-Shirt', 'Black t-shirt with $ sudo rm -rf / print.', 250000, 'clothes', 2, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{"material": "Cotton"}', true, NOW(), NOW()),
(18, 'Git Hero Hoodie', 'Stay safe with git commit -m "Save life".', 550000, 'clothes', 4, 'https://m.media-amazon.com/images/I/61k7B6kE-L._AC_UX679_.jpg', 2, '{"material": "Fleece"}', true, NOW(), NOW()),
(19, 'Cyber Security Cap', 'Protect your head like you protect your data.', 150000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(20, 'JavaScript Ninja T-Shirt', 'Show your JS mastery.', 270000, 'clothes', 2, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(21, 'Docker Container Socks', 'Keep your feet isolated and scalable.', 120000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(22, 'Code Review Mug', 'Drink coffee, find bugs.', 180000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(23, 'Mechanical Keyboard Desk Mat', 'Large desk mat for your mechanical keyboard.', 350000, 'clothes', 5, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW()),
(24, 'Binary Code Jacket', 'Stylish jacket with binary pattern.', 890000, 'clothes', 4, 'https://m.media-amazon.com/images/I/61mNnQ9oK+L._AC_UX679_.jpg', 2, '{}', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 3. Insert variants
INSERT INTO product_variants (id, product_id, name, price_override, stock, sku, options)
VALUES
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
