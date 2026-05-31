import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="大台中宮廟排程平台", page_icon="🛕", layout="wide")

st.title("🚀 大台中 18 間宮廟排程：智慧調度與演算法評估中心")
st.markdown("本系統整合了真實地理空間資訊與演算法效能數據，呈現車輛途程問題 (VRP) 在實務與數學最佳化間的權衡。")

# ==========================================
# 2. 準備資料庫
# ==========================================
# (A) 演算法效能數據
@st.cache_data
def load_data():
    data = {
        '演算法': ['ALNS', 'MILP', 'MA', 'ACO', 'Savings', 'TS', '2-Opt', 'SA', 'GA', 'Greedy'],
        '總距離 (km)': [137.36, 143.13, 143.13, 144.74, 144.87, 146.07, 156.44, 163.89, 167.03, 199.69],
        '運算時間 (s)': [1.01, 1.58, 3.17, 0.57, 0.001, 3.55, 0.003, 0.89, 4.80, 0.001],
        '車隊一 (間)': [17, 13, 13, 13, 13, 11, 15, 10, 6, 15],
        '車隊二 (間)': [0, 4, 4, 4, 4, 6, 2, 7, 11, 2]
    }
    return pd.DataFrame(data)

df = load_data()

# (B) 宮廟經緯度座標
temple_coords = {
    0: ("南屯萬和宮", 24.138, 120.638), 1: ("西屯福壽宮", 24.170, 120.645),
    2: ("北區明德宮天聖堂", 24.161, 120.675), 3: ("北屯紫微宮", 24.175, 120.685),
    4: ("潭子潭水亭觀音廟", 24.212, 120.705), 5: ("社口萬興宮", 24.240, 120.670),
    6: ("豐原慈濟宮", 24.252, 120.718), 7: ("東勢東聖宮", 24.258, 120.827),
    8: ("大甲鎮瀾宮", 24.344, 120.623), 9: ("清水紫雲巖", 24.269, 120.578),
    10: ("梧棲浩天宮", 24.240, 120.536), 11: ("沙鹿玉皇殿", 24.238, 120.560),
    12: ("龍井新庄永順宮", 24.195, 120.540), 13: ("大肚瑞安宮", 24.155, 120.545),
    14: ("南區醒修宮", 24.125, 120.670), 15: ("大里杙福興宮", 24.098, 120.678),
    16: ("太平聖和宮", 24.125, 120.715), 17: ("中區順天宮輔順將軍廟", 24.145, 120.682)
}

# (C) ★ 完整擴充：10 種演算法的真實路線軌跡 ★
routes_data = {
    "👑 ALNS (137.36 km | 17 間 vs 0 間) - AI 血汗極限": {
        "route1": [0, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 17, 16, 15, 14, 0],
        "route2": []
    },
    "🎯 MILP (143.13 km | 13 間 vs 4 間) - 數學雙車極限": {
        "route1": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0],
        "route2": [0, 14, 15, 16, 17, 0]
    },
    "🧠 MA 迷因演算法 (143.13 km | 13 間 vs 4 間)": {
        "route1": [0, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        "route2": [0, 17, 16, 15, 14, 0]
    },
    "🐜 ACO 蟻群演算法 (144.74 km | 13 間 vs 4 間)": {
        "route1": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0],
        "route2": [0, 14, 17, 16, 15, 0]
    },
    "🦅 Savings 節約法 (144.87 km | 13 間 vs 4 間) - 業界霸主": {
        "route1": [0, 14, 15, 16, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0],
        "route2": [0, 1, 3, 2, 17, 0]
    },
    "禁忌搜尋法 TS (146.07 km | 11 間 vs 6 間)": {
        "route1": [0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0],
        "route2": [0, 1, 2, 17, 16, 15, 14, 0]
    },
    "2-Opt 局部搜尋 (156.44 km | 15 間 vs 2 間)": {
        "route1": [0, 14, 17, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 12, 1, 0],
        "route2": [0, 15, 16, 0]
    },
    "🔥 SA 模擬退火法 (163.89 km | 10 間 vs 7 間) - 平衡妥協": {
        "route1": [0, 15, 16, 6, 7, 8, 9, 10, 11, 12, 13, 0],
        "route2": [0, 14, 17, 1, 3, 5, 4, 2, 0]
    },
    "🧬 GA 基因演算法 (167.03 km | 6 間 vs 11 間)": {
        "route1": [0, 12, 8, 9, 10, 11, 13, 0],
        "route2": [0, 14, 15, 16, 7, 6, 5, 4, 3, 2, 1, 17, 0]
    },
    "🤡 全域貪婪法 Greedy (199.69 km | 15 間 vs 2 間) - 反面教材": {
        "route1": [0, 14, 17, 2, 1, 3, 4, 6, 5, 7, 9, 11, 10, 12, 13, 8, 0],
        "route2": [0, 15, 16, 0]
    }
}

# ==========================================
# 3. 網頁側邊欄 (Sidebar 控制中心)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/zh/thumb/1/1a/National_Yang_Ming_Chiao_Tung_University_logo.svg/1200px-National_Yang_Ming_Chiao_Tung_University_logo.svg.png", width=150)
st.sidebar.header("⚙️ 系統控制中心")

# 地圖控制
st.sidebar.subheader("🗺️ 第一階段：路線模擬")
selected_algo = st.sidebar.selectbox("切換地圖上的演算法路線：", list(routes_data.keys()))

st.sidebar.divider()

# 儀表板控制
st.sidebar.subheader("📊 第二階段：數據分析")
sort_by = st.sidebar.radio(
    "動態排序儀表板圖表：",
    ("總距離 (由小到大)", "運算時間 (由快到慢)", "工作量差異 (血汗程度)")
)

if sort_by == "總距離 (由小到大)":
    df = df.sort_values(by='總距離 (km)').reset_index(drop=True)
elif sort_by == "運算時間 (由快到慢)":
    df = df.sort_values(by='運算時間 (s)').reset_index(drop=True)
else:
    df['差異'] = abs(df['車隊一 (間)'] - df['車隊二 (間)'])
    df = df.sort_values(by=['差異', '總距離 (km)']).reset_index(drop=True)

# ==========================================
# 4. 頂端 KPI 數據卡
# ==========================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌍 總任務點", "18 間宮廟", "大台中地區")
col2.metric("🏆 最短總距離", "137.36 km", "ALNS 演算法")
col3.metric("⚡ 最快耗時", "0.001 秒", "Savings 節約法")
col4.metric("⚖️ 最佳排班平衡", "10 間 / 7 間", "SA 模擬退火")

st.divider()

# ==========================================
# 5. 上半部：Folium 互動地圖
# ==========================================
st.subheader("📍 即時路線模擬地圖")

def draw_map(algo_name):
    m = folium.Map(location=[24.22, 120.65], zoom_start=11, tiles="CartoDB positron")
    
    for idx, info in temple_coords.items():
        name, lat, lon = info
        if idx == 0:
            folium.Marker([lat, lon], tooltip=f"⭐ 總部：{name}", icon=folium.Icon(color="red", icon="home")).add_to(m)
        else:
            folium.Marker([lat, lon], tooltip=name, icon=folium.Icon(color="gray", icon="info-sign")).add_to(m)

    r1_indices = routes_data[algo_name]["route1"]
    r2_indices = routes_data[algo_name]["route2"]
    
    if len(r1_indices) > 0:
        r1_coords = [[temple_coords[idx][1], temple_coords[idx][2]] for idx in r1_indices]
        folium.PolyLine(r1_coords, color="#e74c3c", weight=5, opacity=0.8, tooltip="🚗 車隊一 (紅線)").add_to(m)
        
    if len(r2_indices) > 0:
        r2_coords = [[temple_coords[idx][1], temple_coords[idx][2]] for idx in r2_indices]
        folium.PolyLine(r2_coords, color="#3498db", weight=5, opacity=0.8, tooltip="🚙 車隊二 (藍線)").add_to(m)
        
    return m

map_obj = draw_map(selected_algo)
st_folium(map_obj, width="100%", height=500, returned_objects=[])

st.divider()

# ==========================================
# 6. 下半部：Plotly 互動儀表板
# ==========================================
st.subheader(f"📊 演算法效能深度分析 (排序依據：{sort_by})")

colors = ['#e74c3c' if val <= 143.13 else '#3498db' for val in df['總距離 (km)']]
fig1 = px.bar(df, x='演算法', y='總距離 (km)', text='總距離 (km)', title='🏆 最佳總距離比較 (距離越短越好)', hover_data={'運算時間 (s)': True})
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
fig1.update_layout(yaxis=dict(range=[120, 205]), margin=dict(t=40), template='plotly_white')
st.plotly_chart(fig1, use_container_width=True)

col_left, col_right = st.columns(2)

with col_left:
    fig3 = px.scatter(df, x='運算時間 (s)', y='總距離 (km)', color='演算法', size=[20]*len(df), hover_name='演算法', title='⏱️ 運算時間 vs 總距離 權衡 (Trade-off)')
    fig3.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig3.add_vrect(x0=-0.2, x1=1.8, fillcolor="green", opacity=0.1, line_width=0, annotation_text="理想區 (快又短)")
    fig3.update_layout(margin=dict(t=40), template='plotly_white')
    st.plotly_chart(fig3, use_container_width=True)

with col_right:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df['演算法'], y=df['車隊一 (間)'], name='車隊一', marker_color='#f39c12', text=df['車隊一 (間)'], textposition='auto'))
    fig2.add_trace(go.Bar(x=df['演算法'], y=df['車隊二 (間)'], name='車隊二', marker_color='#2c3e50', text=df['車隊二 (間)'], textposition='auto'))
    fig2.update_layout(barmode='stack', title='⚖️ 工作量分配 (血汗指數分析)', yaxis_title='負責宮廟數量', margin=dict(t=40), template='plotly_white')
    fig2.add_hline(y=8.5, line_dash="dash", line_color="red", annotation_text="完美平均線")
    st.plotly_chart(fig2, use_container_width=True)