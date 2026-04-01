import pandas as pd
from sqlalchemy import create_engine

# ==================== 数据库连接配置 ====================
# 请将 '123456' 替换为你的 MySQL root 密码
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

# 创建 SQLAlchemy 引擎（pandas 的 to_sql 需要）
engine_business = create_engine(
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/business?charset={DB_CONFIG['charset']}"
)
engine_warehouse = create_engine(
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/warehouse?charset={DB_CONFIG['charset']}"
)

# ==================== 1. ODS 层：全量同步 ====================
def sync_ods():
    """将 business 库中的表全量同步到 warehouse 的 ods 表"""
    tables = ['users', 'products', 'orders', 'order_items']
    for table in tables:
        print(f"正在同步 {table}...")
        df = pd.read_sql(f"SELECT * FROM {table}", engine_business)
        df.to_sql(f"ods_{table}", engine_warehouse, if_exists='replace', index=False, chunksize=10000)
        print(f"  -> 同步完成，共 {len(df)} 行")
    print("ODS 层同步完成\n")

# ==================== 2. DWD 层：清洗 + 增加日期字段 ====================
def transform_dwd():
    """生成 dwd_orders 和 dwd_order_items"""
    # 读取 ods_orders，增加 order_date 列
    print("正在处理 dwd_orders...")
    df_orders = pd.read_sql("SELECT * FROM ods_orders", engine_warehouse)
    df_orders['order_date'] = pd.to_datetime(df_orders['order_time']).dt.date
    # 只保留需要的列
    df_orders = df_orders[['order_id', 'user_id', 'order_date', 'order_time', 'total_amount', 'status']]
    df_orders.to_sql('dwd_orders', engine_warehouse, if_exists='replace', index=False)
    print(f"  -> dwd_orders 生成完成，共 {len(df_orders)} 行")

    # 订单明细直接复制
    print("正在处理 dwd_order_items...")
    df_items = pd.read_sql("SELECT * FROM ods_order_items", engine_warehouse)
    df_items.to_sql('dwd_order_items', engine_warehouse, if_exists='replace', index=False)
    print(f"  -> dwd_order_items 生成完成，共 {len(df_items)} 行\n")

# ==================== 3. DWS 层：按日聚合 ====================
def aggregate_dws():
    """生成 dws_sales_daily 按日汇总表"""
    print("正在生成 dws_sales_daily...")
    sql = """
        SELECT 
            order_date AS stat_date,
            COUNT(*) AS order_count,
            SUM(total_amount) AS revenue,
            COUNT(DISTINCT user_id) AS user_count
        FROM dwd_orders
        GROUP BY order_date
        ORDER BY order_date
    """
    df = pd.read_sql(sql, engine_warehouse)
    df.to_sql('dws_sales_daily', engine_warehouse, if_exists='replace', index=False)
    print(f"  -> dws_sales_daily 生成完成，共 {len(df)} 天数据\n")

# ==================== 4. ADS 层：Top 10 商品 ====================
def generate_ads():
    """生成 ads_top_products 表（销量 Top 10 商品）"""
    print("正在生成 ads_top_products...")
    sql = """
        SELECT 
            p.product_id,
            p.product_name,
            SUM(oi.quantity) AS total_sold
        FROM ods_products p
        JOIN dwd_order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 10
    """
    df = pd.read_sql(sql, engine_warehouse)
    df['ranking'] = range(1, len(df) + 1)   # 排名列（避免使用保留字 rank）
    df.to_sql('ads_top_products', engine_warehouse, if_exists='replace', index=False)
    print(f"  -> ads_top_products 生成完成，共 {len(df)} 行\n")

# ==================== 主流程 ====================
if __name__ == '__main__':
    print("开始执行 ETL...\n")
    sync_ods()
    transform_dwd()
    aggregate_dws()
    generate_ads()
    print("所有 ETL 任务执行完毕！")