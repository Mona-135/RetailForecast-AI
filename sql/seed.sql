-- Seed initial Store and Department metadata (Walmart schema aligned)
INSERT INTO stores (store_id, store_type, size)
VALUES
    (1, 'A', 151315),
    (2, 'A', 202307),
    (3, 'B', 37392),
    (4, 'A', 205863),
    (5, 'B', 34875)
ON CONFLICT (store_id) DO NOTHING;

INSERT INTO departments (department_id, department_name)
VALUES
    (1, 'Candy & Snacks'),
    (2, 'Health & Beauty'),
    (3, 'Stationery & Crafts'),
    (4, 'Household Goods'),
    (5, 'Electronics & Media'),
    (6, 'Apparel & Footwear'),
    (7, 'Sporting Goods'),
    (8, 'Automotive'),
    (9, 'Garden & Patio'),
    (10, 'Grocery Essentials')
ON CONFLICT (department_id) DO NOTHING;
