import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
import base64
import json
import os

print("⏳ 正在從 results.json 讀取最新數據，動態生成【暗黑版】網頁檔...")

# ==========================================
# 1. 自動讀取 JSON 成績單並轉換為 DataFrame
# ==========================================
json_file = "results.json"
if not os.path.exists(json_file):
    print("❌ 錯誤：找不到 results.json，請先執行演算法以產生數據！")
    sys.exit()

with open(json_file, "r", encoding="utf-8") as f:
    live_data = json.load(f)

# 準備用來裝數據的空陣列
algos, distances, times, car1_counts, car2_counts = [], [], [], [], []

# 從 JSON 中動態提取資料
for algo_name, result in live_data.items():
    algos.append(algo_name)
    distances.append(result["distance"])
    times.append(result["time"])
    car1_counts.append(result["car1_count"])
    car2_counts.append(result["car2_count"])

# 建立 DataFrame 並依總距離由小到大排序
df = pd.DataFrame({
    '演算法': algos,
    '總距離 (km)': distances,
    '運算時間 (s)': times,
    '車隊一 (間)': car1_counts,
    '車隊二 (間)': car2_counts
}).sort_values(by='總距離 (km)').reset_index(drop=True)

# 動態計算 KPI 指標
best_algo = df.iloc[0]['演算法']
best_dist = df.iloc[0]['總距離 (km)']
fastest_idx = df['運算時間 (s)'].idxmin()
fastest_algo = df.iloc[fastest_idx]['演算法']
fastest_time = df.iloc[fastest_idx]['運算時間 (s)']

# ==========================================
# 2. 宮廟經緯度座標 (固定不變)
# ==========================================
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

# ==========================================
# 3. 建立動態圖層控制的 Folium 地圖
# ==========================================
m = folium.Map(location=[24.22, 120.65], zoom_start=11, tiles="CartoDB dark_matter")

for idx, info in temple_coords.items():
    name, lat, lon = info
    if idx == 0:
        folium.Marker([lat, lon], tooltip=f"⭐ 總部：{name}", icon=folium.Icon(color="red", icon="home")).add_to(m)
    else:
        folium.CircleMarker([lat, lon], radius=5, color="#a3a8b8", fill=True, fill_opacity=0.8, tooltip=name).add_to(m)

# 動態從 JSON 讀取路線並畫上去
for algo_name, result in live_data.items():
    is_active = (algo_name == best_algo) # 預設只顯示冠軍路線，其他可手動勾選
    fg = folium.FeatureGroup(name=algo_name, show=is_active)
    
    r1, r2 = result.get("route1", []), result.get("route2", [])
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
# 4. 生成 Plotly 互動圖表 (套用暗黑主題與防跑位設定)
# ==========================================
colors = ['#e74c3c' if val == best_dist else '#3498db' for val in df['總距離 (km)']]

dark_layout = dict(
    template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#fafafa')
)

# 距離長條圖
fig1 = px.bar(df, x='演算法', y='總距離 (km)', text='總距離 (km)', title='🏆 最新總距離排名 (越低越好)', hover_data={'運算時間 (s)': True})
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
# 動態調整 Y 軸範圍讓柱子看起來差異更明顯
y_min, y_max = max(0, df['總距離 (km)'].min() - 20), df['總距離 (km)'].max() + 25
fig1.update_layout(yaxis=dict(range=[y_min, y_max]), margin=dict(l=40, r=40, t=60, b=40), **dark_layout)

# 運算時間散佈圖
fig2 = px.scatter(df, x='運算時間 (s)', y='總距離 (km)', color='演算法', size=[20]*len(df), hover_name='演算法', title='⏱️ 運算時間 vs 總距離')
fig2.add_vrect(x0=-0.05, x1=fastest_time*5 if fastest_time > 0 else 0.1, fillcolor="#2ecc71", opacity=0.15, line_width=0, annotation_text="快跑區", annotation_font_color="white")
fig2.update_layout(showlegend=False, margin=dict(l=40, r=40, t=60, b=40), **dark_layout)

# 勞逸堆疊圖 (確保不跑位)
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊一 (間)'], name='車隊一', marker_color='#f39c12', text=df['車隊一 (間)'], textposition='auto'))
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊二 (間)'], name='車隊二', marker_color='#3498db', text=df['車隊二 (間)'], textposition='auto'))
fig3.update_layout(
    barmode='stack', title='⚖️ 工作量分配 (動態血汗指數)', yaxis_title='負責數量',
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
    margin=dict(l=40, r=20, t=60, b=40), **dark_layout
)
fig3.add_hline(y=8.5, line_dash="dash", line_color="#e74c3c", annotation_text="完美平均", annotation_font_color="white")

html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
html_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False)
html_fig3 = fig3.to_html(full_html=False, include_plotlyjs=False)

# ==========================================
# 5. 組合最終暗黑版 HTML 網頁 (動態替換 KPI 數據)
# ==========================================
final_html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>大台中 18 間宮廟排程：動態調度中心</title>
    <style>
        body {{ font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif; background-color: #0e1117; color: #fafafa; margin: 0; padding: 30px; }}
        h1 {{ text-align: left; color: #ffffff; font-size: 36px; margin-bottom: 5px; }}
        p.subtitle {{ text-align: left; color: #a3a8b8; font-size: 16px; margin-bottom: 30px; }}
        .kpi-container {{ display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }}
        .kpi-card {{ flex: 1; background: #262730; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); min-width: 200px; border: 1px solid #333; }}
        .kpi-title {{ font-size: 14px; color: #a3a8b8; font-weight: 600; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }}
        .kpi-desc {{ font-size: 13px; color: #00fa9a; }} 
        .kpi-desc.gray {{ color: #a3a8b8; }}
        .card {{ background: #262730; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; border: 1px solid #333; }}
        .grid-container {{ display: flex; gap: 20px; flex-wrap: wrap; width: 100%; }}
        .grid-item {{ flex: 1; min-width: 45%; max-width: 100%; overflow: hidden; }}
        iframe {{ background: transparent; }}
    </style>
</head>
<body>
    <h1>🚀 大台中 18 間宮廟排程：全自動化動態調度中心</h1>
    <p class="subtitle">此網頁的圖表與地圖皆由程式自動讀取 latest results.json 動態生成。</p>

    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">🌍 成功載入演算法</div>
            <div class="kpi-value">{len(algos)} 種</div>
            <div class="kpi-desc gray">📍 來自 results.json</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">🏆 本次最優總距離</div>
            <div class="kpi-value">{best_dist:.2f} km</div>
            <div class="kpi-desc">↑ 由 {best_algo} 奪冠</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">⚡ 本次最快耗時</div>
            <div class="kpi-value">{fastest_time:.5f} 秒</div>
            <div class="kpi-desc">↑ 由 {fastest_algo} 奪冠</div>
        </div>
    </div>

    <div class="card">
        <h3 style="margin-top:0; color:#fafafa; font-size: 20px;">📍 動態路線模擬地圖 <span style="font-size:14px; color:#a3a8b8; font-weight:normal;">(請點擊地圖右上角 📚 圖示切換不同演算法)</span></h3>
        <iframe src="{iframe_src}" width="100%" height="550px" style="border:none; border-radius: 8px;"></iframe>
    </div>

    <div class="card">{html_fig1}</div>
    <div class="grid-container">
        <div class="card grid-item">{html_fig2}</div>
        <div class="card grid-item">{html_fig3}</div>
    </div>
</body>
</html>
"""

output_filename = "VRP_Live_Dashboard.html"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"✅ 動態版儀表板打包完成！請點擊打開：{output_filename}")