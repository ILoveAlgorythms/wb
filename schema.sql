-- SQLITE
-- CREATE TABLE IF NOT EXISTS products (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     nm_id INTEGER NOT NULL
-- );

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nmId TEXT NOT NULL,
    lastChangeDate TEXT NOT NULL,
    date TEXT NOT NULL,
    finishedPrice REAL NOT NULL,
    forPay REAL NOT NULL,
    totalPrice REAL NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    barcode TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nmId TEXT NOT NULL,
    lastChangeDate TEXT NOT NULL,

    quantity INTEGER NOT NULL,

    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    barcode TEXT NOT NULL
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
--     sales.name, sales.brand, sales.category,
--     SUM(sales.price_with_disc) AS total_sales,
--     stocks.quantity,
--     REAL(stocks.quantity) / SUM(sales.price_with_disc) AS turnover
-- FROM sales
-- INNER JOIN (
--     SELECT * FROM stocks ORDER BY last_change_date DESC LIMIT 1
-- ) stocks ON sales.nm_id = stocks.nm_id

CREATE VIEW IF NOT EXISTS weekly_sales AS
SELECT
    nmId as "wb article",
    any_value(category), -- ?
    sum(totalPrice) as "total price",
    sum(forPay) as "for pay",
    count(*) as count,
    strftime(date(date), '%W') as "week number"
FROM sales
GROUP BY nmId, strftime(date(date), '%W');