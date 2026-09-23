"""
parse_weather.py - 分析 JSON，提取氣溫資料
作業規範模組 2 (20%):
1. 分析 records -> locations -> location[] -> weatherElement[] -> time[] 結構
2. 提取六大地區每日最高溫 (MaxT) 與最低溫 (MinT)
3. 輸出結構化資料表並儲存為中間產物 weather_data.csv
"""

import json
import os
import pandas as pd

RAW_JSON_PATH = "cwa_weather_raw.json"
OUTPUT_CSV_PATH = "weather_data.csv"

# 指定六大分析區域
TARGET_REGIONS = ["北部地區", "中部地區", "南部地區", "東北部地區", "東部地區", "東南部地區"]

def parse_weather(json_path: str = RAW_JSON_PATH):
    """解析氣象 JSON 並萃取六大區域氣溫資料"""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到原始 JSON 檔案 {json_path}，請先執行 fetch_weather.py！")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 兼容 locations 為物件或清單
    records = data.get("records", {})
    locations_wrapper = records.get("locations", {})
    if isinstance(locations_wrapper, list):
        location_list = locations_wrapper[0].get("location", [])
    elif isinstance(locations_wrapper, dict):
        location_list = locations_wrapper.get("location", [])
    else:
        location_list = []

    print(f"[INFO] 讀取到 {len(location_list)} 個地區資料，開始提取每日高低溫...")

    extracted_records = []

    for loc in location_list:
        region_name = loc.get("locationName")
        if region_name not in TARGET_REGIONS:
            continue

        mint_by_date = {}
        maxt_by_date = {}

        # 走訪 weatherElement (MinT / MaxT)
        for element in loc.get("weatherElement", []):
            elem_name = element.get("elementName")
            
            if elem_name == "MinT":
                for t in element.get("time", []):
                    # 擷取日期 (格式 YYYY-MM-DD)
                    start_time = t.get("startTime", "")
                    date_str = start_time[:10]
                    # 取得溫度數值
                    elem_vals = t.get("elementValue", [{}])
                    val = elem_vals[0].get("value")
                    if val is not None:
                        mint_by_date[date_str] = float(val)

            elif elem_name == "MaxT":
                for t in element.get("time", []):
                    start_time = t.get("startTime", "")
                    date_str = start_time[:10]
                    elem_vals = t.get("elementValue", [{}])
                    val = elem_vals[0].get("value")
                    if val is not None:
                        maxt_by_date[date_str] = float(val)

        # 對齊日期 (一週 7 天)
        common_dates = sorted(list(set(mint_by_date.keys()) & set(maxt_by_date.keys())))
        for d in common_dates:
            extracted_records.append({
                "regionName": region_name,
                "dataDate": d,
                "minT": mint_by_date[d],
                "maxT": maxt_by_date[d]
            })

    # 轉為 DataFrame 進行檢驗與展示
    df = pd.DataFrame(extracted_records)
    print(f"[SUCCESS] 成功提取 {len(df)} 筆預報資料（6 地區 × 7 天預報）！\n")

    # 輸出提取結果範例（作業評分項目要求）
    print("--- [提取結果範例 (前 10 筆資料)] ---")
    print(df.head(10).to_string(index=False))
    print("---------------------------------------\n")

    # 儲存為中間產物 weather_data.csv
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[SUCCESS] 結構化資料已存為中間產物：{OUTPUT_CSV_PATH}")

    return extracted_records

if __name__ == "__main__":
    parse_weather()
