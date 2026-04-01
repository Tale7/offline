-- 使用 warehouse 数据库
USE warehouse;

-- ==================== ODS 层（与业务库表结构一致） ====================
CREATE TABLE IF NOT EXISTS ods_users LIKE business.users;
CREATE TABLE IF NOT EXISTS ods_products LIKE business.products;
CREATE TABLE IF NOT EXISTS ods_orders LIKE business.orders;
CREATE TABLE IF NOT EXISTS ods_order_items LIKE business.order_items;

-- ==================== DWD 层（明细数据，增加 order_date 字段） ====================
CREATE TABLE IF NOT EXISTS dwd_orders (
    order_id INT PRIMARY KEY,
    user_id INT,
    order_date DATE,
    order_time DATETIME,
    total_amount DECIMAL(10,2),
    status TINYINT
);

CREATE TABLE IF NOT EXISTS dwd_order_items (
    item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2)
);

-- ==================== DWS 层（轻度汇总，按日聚合） ====================
CREATE TABLE IF NOT EXISTS dws_sales_daily (
    stat_date DATE PRIMARY KEY,
    order_count INT,
    revenue DECIMAL(15,2),
    user_count INT
);

-- ==================== ADS 层（应用数据，销量 Top 10） ====================
CREATE TABLE IF NOT EXISTS ads_top_products (
    product_id INT,
    product_name VARCHAR(200),
    total_sold INT,
    ranking INT   -- 注意：避免使用保留字 rank，改为 ranking
);
