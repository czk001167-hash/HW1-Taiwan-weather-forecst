"""
app.py - Streamlit 氣溫預報互動式 Web 應用程式
作業規範模組 4 & 5 (40% + 加分項):
1. 下拉選單選擇地區 (北部、中部、南部、東北部、東部、東南部)
2. 使用 SQL 從 SQLite (data.db) 查詢資料 (嚴禁前端直連 API)
3. 顯示最高/最低溫折線圖 (MaxT 紅色 / MinT 藍色)
4. 顯示一週資料表格 (Date, MinT, MaxT)
5. 進階台灣地圖視覺化 (Folium + streamlit-folium，依平均溫度分級著色)
"""

import sqlite3
import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 頁面配置
st.set_page_config(
    page_title="Taiwan Weather Forecast 台灣天氣預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂現代化外觀 CSS
st.markdown("""
<style>
    /* 全域文字與字型 */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px rgba(30, 60, 114, 0.2);
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #e0e7ff;
        font-size: 1.05rem;
        margin-top: 8px;
        margin-bottom: 0;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        background: rgba(255, 255, 255, 0.2);
        color: #fff;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .metric-card .val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-card .label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
    }
    .legend-box {
        background: white;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "data.db"

# 六大區域中心經緯度座標（用於 Folium 地圖標記）
REGION_COORDINATES = {
    "北部地區": [25.04, 121.55],
    "中部地區": [24.15, 120.67],
    "南部地區": [22.62, 120.30],
    "東北部地區": [24.75, 121.75],
    "東部地區": [23.99, 121.60],
    "東南部地區": [22.75, 121.15],
}

def get_temp_color(temp: float) -> str:
    """依作業規範溫度區間設定標記顏色"""
    if temp < 20:
        return "#2b83ba"   # < 20°C (藍色)
    elif 20 <= temp < 25:
        return "#2ecc71"   # 20 - 25°C (綠色)
    elif 25 <= temp <= 30:
        return "#f39c12"   # 25 - 30°C (黃色)
    else:
        return "#e74c3c"   # > 30°C (紅色)

def get_temp_color_name(temp: float) -> str:
    if temp < 20:
        return "blue"
    elif 20 <= temp < 25:
        return "green"
    elif 25 <= temp <= 30:
        return "orange"
    else:
        return "red"

def check_db_exists():
    return os.path.exists(DB_PATH)

def load_regions():
    """從 SQLite 讀取所有可選地區名稱 (使用 SQL 查詢)"""
    if not check_db_exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY id ASC;")
    regions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return regions

def load_forecast_for_region(region_name: str):
    """使用 SQL 從 SQLite 資料庫查詢指定地區之一週預報"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT dataDate AS Date, minT AS MinT, maxT AS MaxT
        FROM TemperatureForecasts
        WHERE regionName = ?
        ORDER BY dataDate ASC;
    """
    df = pd.read_sql_query(query, conn, params=(region_name,))
    conn.close()
    return df

def load_all_regions_summary():
    """使用 SQL 查詢各區域首日與一週氣溫概要（供地圖展示）"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT regionName, 
               MIN(dataDate) as firstDate,
               AVG((minT + maxT) / 2.0) as avgTemp,
               MIN(minT) as minTemp,
               MAX(maxT) as maxTemp
        FROM TemperatureForecasts
        GROUP BY regionName;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 主畫面標題
st.markdown("""
<div class="main-header">
    <div style="margin-bottom: 8px;">
        <span class="badge">HW1 作業</span>
        <span class="badge">CWA API</span>
        <span class="badge">SQLite3</span>
        <span class="badge">Streamlit Web App</span>
    </div>
    <h1>🌤️ Taiwan Weather Forecast 台灣天氣預報</h1>
    <p>從氣象資料到互動式天氣預報應用程式 ｜ 資料獲取 · 資料分析 · 資料儲存 · 資料查詢 · 視覺化展示</p>
</div>
""", unsafe_allow_html=True)

# 檢查資料庫狀態
if not check_db_exists():
    st.error("⚠️ 尚未偵測到 SQLite 資料庫 `data.db`！")
    st.info("請先於終端機依序執行資料處理管線指令：\n1. `python fetch_weather.py`\n2. `python parse_weather.py`\n3. `python database.py`")
    st.stop()

# 側邊欄控制項
with st.sidebar:
    st.header("⚙️ 預報選項設定")
    available_regions = load_regions()
    if not available_regions:
        available_regions = ["北部地區", "中部地區", "南部地區", "東北部地區", "東部地區", "東南部地區"]

    # 下拉選單選擇地區 (作業模組 4 需求: Select Region)
    default_index = available_regions.index("中部地區") if "中部地區" in available_regions else 0
    selected_region = st.selectbox(
        "📍 選擇地區 (Select Region)：",
        options=available_regions,
        index=default_index,
        help="請選擇欲查詢一週氣溫預報的台灣地理分區"
    )

    st.markdown("---")
    st.caption("📡 資料來源：交通部中央氣象署 Open Data API")

# 透過 SQL 查詢所選地區資料
df_forecast = load_forecast_for_region(selected_region)

if df_forecast.empty:
    st.warning(f"目前資料庫中查無 {selected_region} 的預報資料。")
    st.stop()

# 顯示所選區域核心氣象指標 (KPI Metrics)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
today_row = df_forecast.iloc[0]
avg_temp = round((df_forecast["MinT"].mean() + df_forecast["MaxT"].mean()) / 2, 1)

with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">📅 首日最低溫 (MinT)</div>
        <div class="val" style="color: #2b83ba;">{today_row['MinT']}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">📅 首日最高溫 (MaxT)</div>
        <div class="val" style="color: #d7191c;">{today_row['MaxT']}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">🌡️ 本週平均溫度</div>
        <div class="val" style="color: #2e7d32;">{avg_temp}°C</div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    temp_range = round(df_forecast['MaxT'].max() - df_forecast['MinT'].min(), 1)
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">📈 本週最大溫差</div>
        <div class="val" style="color: #f39c12;">{temp_range}°C</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 左右並排整合展示：左側折線圖與資料表格，右側台灣互動地圖視覺化（無需切換頁籤）
col_chart, col_map = st.columns([1.15, 1.0], gap="large")

with col_chart:
    st.subheader(f"📈 氣溫預報折線圖 - {selected_region}")
    
    # 準備繪圖 DataFrame
    plot_df = df_forecast.copy()
    # 轉換日期顯示格式 (MM/DD) 以符合作業圖例
    plot_df["DisplayDate"] = plot_df["Date"].apply(lambda d: d[5:] if len(d) >= 10 else d)
    
    # 自訂折線圖 (使用 Streamlit 原生折線圖與色彩)
    chart_data = plot_df.set_index("DisplayDate")[["MaxT", "MinT"]]
    st.line_chart(
        chart_data,
        color=["#e74c3c", "#3498db"], # MaxT 紅色, MinT 藍色
        use_container_width=True,
        y_label="Temperature (°C)"
    )
    st.caption("🔴 紅線：每日最高溫 (MaxT) ｜ 🔵 藍線：每日最低溫 (MinT)")

    st.markdown("##### 📋 一週預報資料表格 (7 天詳細預報)")
    formatted_table = df_forecast.copy()
    st.dataframe(
        formatted_table,
        column_config={
            "Date": st.column_config.TextColumn("預報日期 (Date)"),
            "MinT": st.column_config.NumberColumn("最低溫 (°C)", format="%.1f"),
            "MaxT": st.column_config.NumberColumn("最高溫 (°C)", format="%.1f")
        },
        hide_index=True,
        use_container_width=True
    )

with col_map:
    st.subheader("🗺️ 台灣六大區域氣溫地圖")
    st.caption("依各區平均氣溫動態標色，點擊圖中圓點即可查看該區詳細氣溫卡片。")

    # 取得六大區域彙總數據
    df_summary = load_all_regions_summary()
    
    # 建立 Folium 地圖，中心對準台灣 (23.7, 120.95)，縮放比例為 7
    m = folium.Map(
        location=[23.7, 120.95],
        zoom_start=7,
        tiles="OpenStreetMap"
    )

    # 在地圖上為六大區域標註圓點
    for _, row in df_summary.iterrows():
        reg_name = row["regionName"]
        if reg_name in REGION_COORDINATES:
            coord = REGION_COORDINATES[reg_name]
            avg_t = round(row["avgTemp"], 1)
            min_t = round(row["minTemp"], 1)
            max_t = round(row["maxTemp"], 1)
            color_hex = get_temp_color(avg_t)

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 140px; padding: 6px;">
                <h4 style="margin: 0 0 6px 0; color: #1e3c72; border-bottom: 2px solid #3498db; padding-bottom: 4px;">{reg_name}</h4>
                <p style="margin: 3px 0; font-size: 13px;"><b>一週均溫:</b> <span style="color:{color_hex}; font-weight:bold;">{avg_t}°C</span></p>
                <p style="margin: 3px 0; font-size: 13px;"><b>最低溫 MinT:</b> {min_t}°C</p>
                <p style="margin: 3px 0; font-size: 13px;"><b>最高溫 MaxT:</b> {max_t}°C</p>
            </div>
            """

            folium.CircleMarker(
                location=coord,
                radius=14,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"<b>{reg_name}</b> (均溫 {avg_t}°C，點擊查看詳情)",
                color=color_hex,
                fill=True,
                fill_color=color_hex,
                fill_opacity=0.85,
                weight=2
            ).add_to(m)

    # 嵌入地圖
    st_folium(m, width="100%", height=400)

    # 溫度圖例說明
    st.markdown("""
    <div class="legend-box">
        <h4 style="margin-top:0; font-size: 0.95rem;">🎨 依平均溫度設定顏色：</h4>
        <div style="display:flex; flex-wrap:wrap; gap:10px; font-size:0.85rem;">
            <div style="display:flex; align-items:center;">
                <span style="background-color:#2b83ba; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:5px;"></span>
                <span><b>&lt; 20°C</b> (藍色)</span>
            </div>
            <div style="display:flex; align-items:center;">
                <span style="background-color:#2ecc71; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:5px;"></span>
                <span><b>20 - 25°C</b> (綠色)</span>
            </div>
            <div style="display:flex; align-items:center;">
                <span style="background-color:#f39c12; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:5px;"></span>
                <span><b>25 - 30°C</b> (黃色)</span>
            </div>
            <div style="display:flex; align-items:center;">
                <span style="background-color:#e74c3c; width:12px; height:12px; border-radius:50%; display:inline-block; margin-right:5px;"></span>
                <span><b>&gt; 30°C</b> (紅色)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("💡 提示：地圖支援平移縮放，點擊圓點可查看氣溫詳情。")

st.markdown("---")
st.caption("程式探索天氣 · 資料看見台灣 ｜ Designed with Streamlit & Folium")
