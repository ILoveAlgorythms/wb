-- schema.sql
-- CREATE TABLE IF NOT EXISTS products (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     nm_id INTEGER NOT NULL
-- );

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    last_change_date TEXT NOT NULL,
    supplier_article TEXT NOT NULL,
    tech_size TEXT,
    barcode TEXT,
    total_price REAL,
    discount_percent INTEGER,
    is_supply BOOLEAN,
    is_realization BOOLEAN,
    promo_code_discount REAL,
    warehouse_name TEXT,
    country_name TEXT,
    oblast_okrug_name TEXT,
    region_name TEXT,
    income_id INTEGER,
    sale_id TEXT NOT NULL,
    odid INTEGER,
    spp REAL,
    for_pay REAL,
    finished_price REAL,
    price_with_disc REAL,
    nm_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantity INTEGER,
    last_change_date TEXT NOT NULL,
    supplier_article TEXT NOT NULL,
    tech_size TEXT,
    barcode TEXT,
    is_supply BOOLEAN,
    is_realization BOOLEAN,
    quantity_full INTEGER,
    warehouse_name TEXT,
    nm_id INTEGER NOT NULL
);


-- view1
-- товар: наименование, бренд, товарная группа
-- продажи по N неделям (в штуках, рублях, рентабельность)
-- сумма по продажам
-- остатки на текущий момент
-- оборачиваемость (остатки/продажи)
-- ?продажи в другой аналогичный период времени
-- ?какой-то прогноз
-- CREATE VIEW view1 AS
-- SELECT
--     sales.name, sales.brand, sales.category, -- товар: наименование, бренд, товарная группа
--     COUNT(sales.sale_id) OVER (ORDER BY date),  
--     SUM(sales.price_with_disc) AS total_sales,
--     stocks.quantity / SUM(sales.price_with_disc) AS turnover
-- FROM sales
-- INNER JOIN (
--     SELECT * FROM stocks ORDER BY last_change_date DESC LIMIT 1
-- ) stocks ON sales.nm_id = stocks.nm_id