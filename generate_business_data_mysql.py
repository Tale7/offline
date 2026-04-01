import pymysql
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('zh_CN')

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',   # 你的密码
    database='business',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 删除已有表（按依赖顺序）
cursor.execute("DROP TABLE IF EXISTS order_items")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS users")

# 建表
cursor.execute("""
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    email VARCHAR(100),
    register_time DATETIME
)
""")
cursor.execute("""
CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10,2)
)
""")
cursor.execute("""
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    order_time DATETIME,
    total_amount DECIMAL(10,2),
    status TINYINT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")
cursor.execute("""
CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
)
""")

# 插入用户（1万）
users = []
for i in range(10000):
    username = fake.user_name()
    email = fake.email()
    reg_time = fake.date_time_between(start_date='-2y')
    users.append((username, email, reg_time))
cursor.executemany("INSERT INTO users (username, email, register_time) VALUES (%s, %s, %s)", users)
conn.commit()

# 插入商品（100）
categories = ['电子产品', '服装', '食品', '图书', '家居']
products = []
for i in range(100):
    name = f"{fake.word()}_{i}"
    category = random.choice(categories)
    price = round(random.uniform(10, 2000), 2)
    products.append((name, category, price))
cursor.executemany("INSERT INTO products (product_name, category, price) VALUES (%s, %s, %s)", products)
conn.commit()

# 获取所有 user_id 和 product_id
cursor.execute("SELECT user_id FROM users")
user_ids = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT product_id, price FROM products")
products_list = cursor.fetchall()

# 插入订单（10万）和明细
orders_data = []
items_data = []
for i in range(100000):
    if i % 10000 == 0:
        print(f"生成订单进度: {i}/100000")
    user_id = random.choice(user_ids)
    order_time = fake.date_time_between(start_date='-2y')
    num_items = random.randint(1, 5)
    chosen = random.choices(products_list, k=num_items)
    total = 0
    items = []
    for prod_id, prod_price in chosen:
        qty = random.randint(1, 3)
        total += prod_price * qty
        items.append((prod_id, qty, prod_price))
    orders_data.append((user_id, order_time, total))
    items_data.append(items)

# 批量插入订单
cursor.executemany("INSERT INTO orders (user_id, order_time, total_amount) VALUES (%s, %s, %s)", orders_data)
conn.commit()

# 获取订单ID范围
cursor.execute("SELECT order_id FROM orders ORDER BY order_id")
order_ids = [row[0] for row in cursor.fetchall()]

# 插入明细
all_items = []
for idx, items in enumerate(items_data):
    order_id = order_ids[idx]
    for prod_id, qty, price in items:
        all_items.append((order_id, prod_id, qty, price))
cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)", all_items)
conn.commit()

print("业务数据生成完成")
cursor.close()
conn.close()