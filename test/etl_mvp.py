import tushare as ts
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# ==========================================
# 1. 基础配置 (Configuration)
# ==========================================
# Tushare Token (请替换为你自己的 Token)
TUSHARE_TOKEN = 'your_tushare_token_here'
# PostgreSQL 数据库连接串 (用户名:密码@主机:端口/数据库名)
DB_URL = 'postgresql://postgres:123456@localhost:5432/quant_db'

# 初始化 Tushare 和 数据库引擎
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
engine = create_engine(DB_URL)

# ==========================================
# 2. 数据抽取 (Extract)
# ==========================================
def extract_tushare_data(trade_date: str):
    print(f"[{trade_date}] 正在从 Tushare 拉取原始数据...")
    
    # 拉取日线行情 (开高低收、成交量、成交额)
    df_daily = pro.daily(trade_date=trade_date)
    
    # 拉取复权因子 (极其重要：用于计算前复权价格)
    df_adj = pro.adj_factor(trade_date=trade_date)
    
    # 拉取每日基本面 (获取 PE_TTM, PB 等现成因子)
    df_basic = pro.daily_basic(trade_date=trade_date)
    
    if df_daily.empty:
        raise ValueError(f"{trade_date} 没有行情数据，可能是非交易日。")
        
    print(f"[{trade_date}] 拉取成功：行情 {len(df_daily)} 条。")
    return df_daily, df_adj, df_basic

# ==========================================
# 3. 数据转换与清洗 (Transform)
# ==========================================
def transform_to_ods(df_daily, df_adj, trade_date):
    """将数据转换为满足 ods_daily_bar 契约的格式"""
    print("正在拼接行情与复权因子 (ODS 层)...")
    
    # 按照 ts_code 合并每日行情和复权因子
    df_merged = pd.merge(df_daily, df_adj[['ts_code', 'adj_factor']], on='ts_code', how='left')
    
    # 重命名列以对齐我们之前设计的 Data Contract
    df_ods = pd.DataFrame()
    df_ods['security_id'] = df_merged['ts_code']
    df_ods['trade_date'] = pd.to_datetime(trade_date)
    df_ods['open'] = df_merged['open']
    df_ods['high'] = df_merged['high']
    df_ods['low'] = df_merged['low']
    df_ods['close'] = df_merged['close']
    df_ods['vol'] = df_merged['vol']
    df_ods['amount'] = df_merged['amount']
    df_ods['adj_factor'] = df_merged['adj_factor']
    df_ods['source'] = 'tushare'
    df_ods['updated_at'] = datetime.now()
    
    return df_ods

def transform_to_dwd_factor(df_basic, trade_date):
    """将基础财务指标转换为 dwd_factor_value 契约格式"""
    print("正在提取并计算核心因子 (DWD 层)...")
    
    # 我们这里提取 PE_TTM 作为首个估值因子演示
    df_factor = pd.DataFrame()
    df_factor['security_id'] = df_basic['ts_code']
    df_factor['trade_date'] = pd.to_datetime(trade_date)
    df_factor['factor_id'] = 'PE_TTM'
    df_factor['factor_value'] = df_basic['pe_ttm']  # Tushare 已经帮我们算好了
    df_factor['value_type'] = 'raw'
    df_factor['source'] = 'tushare_daily_basic'
    df_factor['updated_at'] = datetime.now()
    
    # 过滤掉空值（有的股票可能停牌或没有PE数据）
    df_factor = df_factor.dropna(subset=['factor_value'])
    
    return df_factor

# ==========================================
# 4. 幂等入库 (Load)
# ==========================================
def load_to_db(df, table_name, trade_date, engine):
    """
    最简单的幂等策略：先删除该日期的数据，再全量插入。
    这保证了无论你今天重跑多少次脚本，数据库都不会有主键冲突或重复数据。
    """
    print(f"正在将 {len(df)} 条数据写入表 [{table_name}]...")
    
    with engine.begin() as conn:
        # 1. 清理今日旧数据 (Idempotent 清理)
        delete_sql = text(f"DELETE FROM {table_name} WHERE trade_date = :td")
        conn.execute(delete_sql, {"td": trade_date})
        
        # 2. 批量写入新数据
        df.to_sql(table_name, con=conn, if_exists='append', index=False, chunksize=2000)
        
    print(f"✅ [{table_name}] 写入完成。")

# ==========================================
# 5. 调度主引擎 (Main Pipeline)
# ==========================================
def run_pipeline(trade_date):
    try:
        # 1. 抽取
        df_daily, df_adj, df_basic = extract_tushare_data(trade_date)
        
        # 2. 转换
        ods_daily = transform_to_ods(df_daily, df_adj, trade_date)
        dwd_factor = transform_to_dwd_factor(df_basic, trade_date)
        
        # 3. 加载
        load_to_db(ods_daily, 'ods_daily_bar', trade_date, engine)
        load_to_db(dwd_factor, 'dwd_factor_value', trade_date, engine)
        
        print(f"🎉 交易日 {trade_date} 的 ETL 流水线全部执行成功！")
        
    except Exception as e:
        print(f"❌ ETL 发生致命错误: {e}")

if __name__ == "__main__":
    # 测试拉取最后一个交易日的数据（请替换为真实的最近交易日，如 '20260220'）
    # 注意：Tushare 的 trade_date 格式必须是 YYYYMMDD
    TARGET_DATE = '20260220' 
    run_pipeline(TARGET_DATE)