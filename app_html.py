import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import pandas as pd

# 讓程式自動讀取剛剛演算法們寫入的成績單
with open("results.json", "r", encoding="utf-8") as f:
    live_data = json.load(f)

import plotly.express as px
import plotly.graph_objects as go
import folium
import base64

print("⏳ 正在將【暗黑版】地圖與圖表打包成單一 HTML 網頁檔...")

# ==========================================
# 1. 準備實驗數據與軌跡資料庫
# ==========================================
# 示意程式碼：讓 data 陣列從 live_data 裡面自動抓取最新成績
data = {
    '演算法': [], '總距離 (km)': [], '運算時間 (s)': [], '車隊一 (間)': [], '車隊二 (間)': []
}
routes_data = {}

for algo_name, result in live_data.items():
    data['演算法'].append(algo_name)
    data['總距離 (km)'].append(result['distance'])
    data['運算時間 (s)'].append(result['time'])
    data['車隊一 (間)'].append(result['car1_count'])
    data['車隊二 (間)'].append(result['car2_count'])
    
    # 地圖軌跡也自動抓
    routes_data[algo_name] = {"route1": result["route1"], "route2": result["route2"]}
df = pd.DataFrame(data).sort_values(by='總距離 (km)').reset_index(drop=True)

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

routes_data = {
    "👑 ALNS (137.36 km | 17 間 vs 0 間)": {"route1": [0, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 17, 16, 15, 14, 0], "route2": []},
    "🎯 MILP (143.13 km | 13 間 vs 4 間)": {"route1": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 14, 15, 16, 17, 0]},
    "🧠 MA 迷因演算法 (143.13 km | 13 間 vs 4 間)": {"route1": [0, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0], "route2": [0, 17, 16, 15, 14, 0]},
    "🐜 ACO 蟻群演算法 (144.74 km | 13 間 vs 4 間)": {"route1": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 14, 17, 16, 15, 0]},
    "🦅 Savings (144.87 km | 13 間 vs 4 間)": {"route1": [0, 14, 15, 16, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 1, 3, 2, 17, 0]},
    "禁忌搜尋法 TS (146.07 km | 11 間 vs 6 間)": {"route1": [0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 1, 2, 17, 16, 15, 14, 0]},
    "2-Opt 局部搜尋 (156.44 km | 15 間 vs 2 間)": {"route1": [0, 14, 17, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 12, 1, 0], "route2": [0, 15, 16, 0]},
    "🔥 SA 模擬退火 (163.89 km | 10 間 vs 7 間)": {"route1": [0, 15, 16, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 14, 17, 1, 3, 5, 4, 2, 0]},
    "🧬 GA 基因演算法 (167.03 km | 6 間 vs 11 間)": {"route1": [0, 12, 8, 9, 10, 11, 13, 0], "route2": [0, 14, 15, 16, 7, 6, 5, 4, 3, 2, 1, 17, 0]},
    "🤡 Greedy (199.69 km | 15 間 vs 2 間)": {"route1": [0, 14, 17, 2, 1, 3, 4, 6, 5, 7, 9, 11, 10, 12, 13, 8, 0], "route2": [0, 15, 16, 0]}
}

# ==========================================
# 2. 建立含有「圖層控制」的黑夜版 Folium 地圖
# ==========================================
# ★ 將 tiles 改為 CartoDB dark_matter 以配合暗黑模式 ★
m = folium.Map(location=[24.22, 120.65], zoom_start=11, tiles="CartoDB dark_matter")

for idx, info in temple_coords.items():
    name, lat, lon = info
    if idx == 0:
        folium.Marker([lat, lon], tooltip=f"⭐ 總部：{name}", icon=folium.Icon(color="red", icon="home")).add_to(m)
    else:
        folium.CircleMarker([lat, lon], radius=5, color="#a3a8b8", fill=True, fill_opacity=0.8, tooltip=name).add_to(m)

for algo_name, routes in routes_data.items():
    is_active = "ALNS" in algo_name 
    fg = folium.FeatureGroup(name=algo_name, show=is_active)
    
    r1, r2 = routes["route1"], routes["route2"]
    if len(r1) > 0:
        folium.PolyLine([[temple_coords[i][1], temple_coords[i][2]] for i in r1], color="#e74c3c", weight=5, opacity=0.9).add_to(fg)
    if len(r2) > 0:
        folium.PolyLine([[temple_coords[i][1], temple_coords[i][2]] for i in r2], color="#3498db", weight=5, opacity=0.9).add_to(fg)
    fg.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

map_html_string = m.get_root().render()
map_b64 = base64.b64encode(map_html_string.encode('utf-8')).decode('utf-8')
iframe_src = f"data:text/html;base64,{map_b64}"

# ==========================================
# 3. 生成 Plotly 互動圖表 (套用暗黑主題與透明背景)
# ==========================================
colors = ['#e74c3c' if val <= 143.13 else '#3498db' for val in df['總距離 (km)']]

# 共通的暗黑佈景設定
dark_layout = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#fafafa')
)

fig1 = px.bar(df, x='演算法', y='總距離 (km)', text='總距離 (km)', title='🏆 最佳總距離比較 (越低越好)', hover_data={'運算時間 (s)': True})
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
fig1.update_layout(yaxis=dict(range=[120, 205]), **dark_layout)

fig2 = px.scatter(df, x='運算時間 (s)', y='總距離 (km)', color='演算法', size=[20]*len(df), hover_name='演算法', title='⏱️ 運算時間 vs 總距離')
fig2.add_vrect(x0=-0.2, x1=1.8, fillcolor="#2ecc71", opacity=0.15, line_width=0, annotation_text="理想區", annotation_font_color="white")
fig2.update_layout(**dark_layout)

fig3 = go.Figure()
# ★ 補上 text 參數，將確切數字印在柱狀圖上 ★
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊一 (間)'], name='車隊一', marker_color='#f39c12', text=df['車隊一 (間)'], textposition='auto'))
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊二 (間)'], name='車隊二', marker_color='#3498db', text=df['車隊二 (間)'], textposition='auto'))
fig3.update_layout(barmode='stack', title='⚖️ 工作量分配 (血汗指數)', yaxis_title='宮廟數量', **dark_layout)
fig3.add_hline(y=8.5, line_dash="dash", line_color="#e74c3c", annotation_text="平均線", annotation_font_color="white")

html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
html_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False)
html_fig3 = fig3.to_html(full_html=False, include_plotlyjs=False)

# ==========================================
# 4. 組合最終暗黑版 HTML 網頁 (補上 KPI 數據卡)
# ==========================================
final_html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>大台中 18 間宮廟排程：智慧調度中心</title>
    <style>
        /* 暗黑模式 CSS 設定 */
        body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; background-color: #0e1117; color: #fafafa; margin: 0; padding: 30px; }}
        h1 {{ text-align: left; color: #ffffff; font-size: 36px; margin-bottom: 5px; }}
        p.subtitle {{ text-align: left; color: #a3a8b8; font-size: 16px; margin-bottom: 30px; }}
        
        /* KPI 數據卡佈局 */
        .kpi-container {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
        .kpi-card {{ flex: 1; background: #262730; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); min-width: 200px; border: 1px solid #333; }}
        .kpi-title {{ font-size: 14px; color: #a3a8b8; font-weight: 600; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }}
        .kpi-desc {{ font-size: 13px; color: #00fa9a; }} /* 亮綠色字體 */
        .kpi-desc.gray {{ color: #a3a8b8; }}

        /* 圖表卡片佈局 */
        .card {{ background: #262730; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; border: 1px solid #333; }}
        .grid-container {{ display: flex; gap: 20px; flex-wrap: wrap; }}
        .grid-item {{ flex: 1; min-width: 400px; }}
        
        /* 隱藏 Folium 地圖周圍預設的白色邊框 */
        iframe {{ background: transparent; }}
    </style>
</head>
<body>
    <h1>🚀 大台中 18 間宮廟排程：智慧調度與演算法評估中心</h1>
    <p class="subtitle">本系統整合了真實地理空間資訊與演算法效能數據，呈現車輛途程問題 (VRP) 在實務與數學最佳化間的權衡。</p>

    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">🌍 總任務點</div>
            <div class="kpi-value">18 間宮廟</div>
            <div class="kpi-desc gray">📍 大台中地區</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">🏆 最短總距離</div>
            <div class="kpi-value">137.36 km</div>
            <div class="kpi-desc">↑ ALNS 演算法</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">⚡ 最快耗時</div>
            <div class="kpi-value">0.001 秒</div>
            <div class="kpi-desc">↑ Savings 節約法</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">⚖️ 最佳排班平衡</div>
            <div class="kpi-value">10 間 / 7 間</div>
            <div class="kpi-desc">↑ SA 模擬退火</div>
        </div>
    </div>

    <div class="card">
        <h3 style="margin-top:0; color:#fafafa; font-size: 20px;">📍 即時路線模擬地圖 <span style="font-size:14px; color:#a3a8b8; font-weight:normal;">(請點擊地圖右上角 📚 圖示切換演算法)</span></h3>
        <iframe src="{iframe_src}" width="100%" height="550px" style="border:none; border-radius: 8px;"></iframe>
    </div>

    <div class="card">
        {html_fig1}
    </div>

    <div class="grid-container">
        <div class="card grid-item">
            {html_fig2}
        </div>
        <div class="card grid-item">
            {html_fig3}
        </div>
    </div>
</body>
</html>
"""

# ==========================================
# 5. 將結果寫入實體 HTML 檔案
# ==========================================
output_filename = "VRP_Final_Dashboard_Dark.html"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"✅ 暗黑版打包完成！已成功生成：{output_filename}")