"""
database.py - 存入 SQLite 資料庫
作業規範模組 3 (20%):
1. 建立 SQLite 資料庫 data.db
2. 建立資料表 TemperatureForecasts (id, regionName, dataDate, minT, maxT)
3. 批次存入提取之氣溫資料
4. 執行驗證查詢：
   - 列出所有地區名稱 (SELECT DISTINCT regionName...)
   - 查詢中部地區資料 (SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區')
"""

import sqlite3
import os
import pandas as pd
from parse_weather import parse_weather

DB_PATH = "data.db"
CSV_PATH = "weather_data.csv"

def init_db(db_path: str = DB_PATH):
    """建立資料庫連線並建立 TemperatureForecasts 資料表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 建立符合作業規格之資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TemperatureForecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT NOT NULL,
            dataDate TEXT NOT NULL,
            minT REAL NOT NULL,
            maxT REAL NOT NULL,
            UNIQUE(regionName, dataDate) ON CONFLICT REPLACE
        );
    """)
    conn.commit()
    return conn

def save_to_database(records=None, db_path: str = DB_PATH):
    """將氣溫預報資料寫入 SQLite 資料庫"""
    # 若無傳入 records，優先嘗試讀取中間產物 CSV，或執行 parse_weather()
    if records is None:
        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
            records = df.to_dict(orient="records")
        else:
            records = parse_weather()

    conn = init_db(db_path)
    cursor = conn.cursor()

    # 批次寫入資料
    insert_sql = """
        INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT)
        VALUES (?, ?, ?, ?);
    """
    data_tuples = [(r["regionName"], r["dataDate"], float(r["minT"]), float(r["maxT"])) for r in records]
    cursor.executemany(insert_sql, data_tuples)
    conn.commit()
    print(f"[SUCCESS] 成功將 {len(data_tuples)} 筆預報寫入 SQLite 資料庫 ({db_path})！\n")

    # 驗證查詢 1: 列出所有地區名稱 (作業評分項目)
    print("--- [驗證查詢 1: SELECT DISTINCT regionName FROM TemperatureForecasts;] ---")
    cursor.execute("SELECT DISTINCT regionName FROM TemperatureForecasts;")
    regions = cursor.fetchall()
    for row in regions:
        print(f"  • {row[0]}")
    print("------------------------------------------------------------------------\n")

    # 驗證查詢 2: 查詢中部地區資料 (作業評分項目)
    print("--- [驗證查詢 2: SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';] ---")
    cursor.execute("SELECT id, regionName, dataDate, minT, maxT FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate ASC;")
    central_rows = cursor.fetchall()
    print(f"{'id':<5}{'地區':<12}{'日期':<14}{'最低溫(°C)':<14}{'最高溫(°C)':<14}")
    for row in central_rows:
        print(f"{row[0]:<5}{row[1]:<12}{row[2]:<14}{row[3]:<14}{row[4]:<14}")
    print("------------------------------------------------------------------------\n")

    conn.close()

if __name__ == "__main__":
    save_to_database()
