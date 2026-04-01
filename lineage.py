import re
from graphviz import Digraph

# 定义表与对应的 SQL（可根据实际 ETL 脚本调整）
queries = [
    ("ods_users", "SELECT * FROM business.users"),
    ("ods_products", "SELECT * FROM business.products"),
    ("ods_orders", "SELECT * FROM business.orders"),
    ("ods_order_items", "SELECT * FROM business.order_items"),
    ("dwd_orders", "SELECT * FROM ods_orders"),
    ("dwd_order_items", "SELECT * FROM ods_order_items"),
    ("dws_sales_daily", """
        SELECT order_date, COUNT(*) AS order_count, SUM(total_amount) AS revenue, COUNT(DISTINCT user_id) AS user_count
        FROM dwd_orders
        GROUP BY order_date
    """),
    ("ads_top_products", """
        SELECT p.product_id, p.product_name, SUM(oi.quantity) AS total_sold
        FROM ods_products p
        JOIN dwd_order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 10
    """)
]

def extract_tables(sql):
    """从 SQL 中提取 FROM 和 JOIN 后的表名（简单正则）"""
    pattern = r'\bFROM\s+([a-zA-Z0-9_]+)|\bJOIN\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    tables = set()
    for match in matches:
        for part in match:
            if part:
                tables.add(part)
    return tables

# 构建边关系 (源表 -> 目标表)
edges = []
for target, sql in queries:
    sources = extract_tables(sql)
    for src in sources:
        edges.append((src, target))

edges = list(set(edges))

# 生成有向图
dot = Digraph(comment='Data Lineage', format='png')
for src, tgt in edges:
    dot.edge(src, tgt)

# 渲染并自动打开图片
dot.render('lineage', view=True)
print("血缘图已生成：lineage.png")