import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import base64

print("⏳ 正在將地圖與演算法圖表打包成單一 HTML 網頁檔...")

# ==========================================
# 1. 準備資料庫 (同之前的數據與軌跡)
# ==========================================
data = {
    '演算法': ['ALNS', 'MILP', 'MA', 'ACO', 'Savings', 'TS', '2-Opt', 'SA', 'GA', 'Greedy'],
    '總距離 (km)': [137.36, 143.13, 143.13, 144.74, 144.87, 146.07, 156.44, 163.89, 167.03, 199.69],
    '運算時間 (s)': [1.01, 1.58, 3.17, 0.57, 0.001, 3.55, 0.003, 0.89, 4.80, 0.001],
    '車隊一 (間)': [17, 13, 13, 13, 13, 11, 15, 10, 6, 15],
    '車隊二 (間)': [0, 4, 4, 4, 4, 6, 2, 7, 11, 2]
}
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
    "🦅 Savings (144.87 km | 13 間 vs 4 間)": {"route1": [0, 14, 15, 16, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 1, 3, 2, 17, 0]},
    "🔥 SA (163.89 km | 10 間 vs 7 間)": {"route1": [0, 15, 16, 6, 7, 8, 9, 10, 11, 12, 13, 0], "route2": [0, 14, 17, 1, 3, 5, 4, 2, 0]},
    "🤡 Greedy (199.69 km | 15 間 vs 2 間)": {"route1": [0, 14, 17, 2, 1, 3, 4, 6, 5, 7, 9, 11, 10, 12, 13, 8, 0], "route2": [0, 15, 16, 0]}
}

# ==========================================
# 2. 建立含有「圖層控制」的 Folium 地圖
# ==========================================
m = folium.Map(location=[24.22, 120.65], zoom_start=11, tiles="CartoDB positron")

# 標示宮廟 (放在基礎圖層，永遠顯示)
for idx, info in temple_coords.items():
    name, lat, lon = info
    if idx == 0:
        folium.Marker([lat, lon], tooltip=f"⭐ 總部：{name}", icon=folium.Icon(color="red", icon="home")).add_to(m)
    else:
        folium.CircleMarker([lat, lon], radius=5, color="gray", fill=True, fill_opacity=0.7, tooltip=name).add_to(m)

# 將每一種演算法做成一個「圖層 (FeatureGroup)」
for algo_name, routes in routes_data.items():
    # 預設只顯示 ALNS 的路線，其他先隱藏，讓畫面不會太亂
    is_active = "ALNS" in algo_name 
    fg = folium.FeatureGroup(name=algo_name, show=is_active)
    
    r1, r2 = routes["route1"], routes["route2"]
    if len(r1) > 0:
        folium.PolyLine([[temple_coords[i][1], temple_coords[i][2]] for i in r1], color="#e74c3c", weight=4, opacity=0.8).add_to(fg)
    if len(r2) > 0:
        folium.PolyLine([[temple_coords[i][1], temple_coords[i][2]] for i in r2], color="#3498db", weight=4, opacity=0.8).add_to(fg)
    
    fg.add_to(m)

# ★ 關鍵：加入圖層控制器 (讓使用者可以在地圖右上角打勾切換) ★
folium.LayerControl(collapsed=False).add_to(m)

# 為了包進單一 HTML，將地圖轉為 Base64 格式的 iframe
map_html_string = m.get_root().render()
map_b64 = base64.b64encode(map_html_string.encode('utf-8')).decode('utf-8')
iframe_src = f"data:text/html;base64,{map_b64}"

# ==========================================
# 3. 生成 Plotly 互動圖表的 HTML
# ==========================================
colors = ['#e74c3c' if val <= 143.13 else '#3498db' for val in df['總距離 (km)']]

fig1 = px.bar(df, x='演算法', y='總距離 (km)', text='總距離 (km)', title='🏆 最佳總距離比較', hover_data={'運算時間 (s)': True})
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
fig1.update_layout(yaxis=dict(range=[120, 205]), template='plotly_white')

fig2 = px.scatter(df, x='運算時間 (s)', y='總距離 (km)', color='演算法', size=[20]*len(df), hover_name='演算法', title='⏱️ 運算時間 vs 總距離')
fig2.add_vrect(x0=-0.2, x1=1.8, fillcolor="green", opacity=0.1, line_width=0, annotation_text="理想區")
fig2.update_layout(template='plotly_white')

fig3 = go.Figure()
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊一 (間)'], name='車隊一', marker_color='#f39c12'))
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊二 (間)'], name='車隊二', marker_color='#2c3e50'))
fig3.update_layout(barmode='stack', title='⚖️ 工作量分配 (血汗指數)', yaxis_title='宮廟數量', template='plotly_white')
fig3.add_hline(y=8.5, line_dash="dash", line_color="red", annotation_text="平均線")

# 將 Plotly 轉為 HTML div (只在第一個圖表引入 js 函式庫，減少檔案體積)
html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
html_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False)
html_fig3 = fig3.to_html(full_html=False, include_plotlyjs=False)

# ==========================================
# 4. 組合最終的獨立 HTML 網頁
# ==========================================
dashboard_html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>大台中 18 間宮廟排程：最佳化決策儀表板</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }}
        h1 {{ text-align: center; color: #2c3e50; font-size: 32px; margin-bottom: 5px; }}
        p.subtitle {{ text-align: center; color: #7f8c8d; font-size: 16px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .grid-container {{ display: flex; gap: 20px; }}
        .grid-item {{ flex: 1; min-width: 0; }} 
    </style>
</head>
<body>
    <h1>🚀 大台中宮廟排程：最佳化決策儀表板</h1>
    <p class="subtitle">將純粹的數學最佳化與實務營運限制進行視覺化對比</p>

    <div class="card">
        <h2 style="margin-top:0; color:#34495e;">🗺️ 空間路線疊圖 (請利用右上角圖層選單切換演算法)</h2>
        <iframe src="{iframe_src}" width="100%" height="600px" style="border:none; border-radius: 8px;"></iframe>
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

# 將結果寫入實體檔案
with open("Final_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print("✅ 打包完成！已生成 Final_Dashboard.html")
print("👉 這是一個完全獨立的網頁檔案，你可以直接點擊兩下打開它，或把它用 Email 寄給教授！")