import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 準備實驗數據資料庫
# ==========================================
data = {
    '演算法': ['ALNS', 'MILP', 'MA', 'ACO', 'Savings', 'TS', '2-Opt', 'SA', 'GA', 'Greedy'],
    '總距離 (km)': [137.36, 143.13, 143.13, 144.74, 144.87, 146.07, 156.44, 163.89, 167.03, 199.69],
    '運算時間 (s)': [1.01, 1.58, 3.17, 0.57, 0.001, 3.55, 0.003, 0.89, 4.80, 0.001],
    '車隊一 (間)': [17, 13, 13, 13, 13, 11, 15, 10, 6, 15],
    '車隊二 (間)': [0, 4, 4, 4, 4, 6, 2, 7, 11, 2]
}
df = pd.DataFrame(data)

# 依照總距離由小到大排序
df = df.sort_values(by='總距離 (km)').reset_index(drop=True)

# ==========================================
# 2. 繪製圖表一：總距離比較 (Bar Chart)
# ==========================================
# 設定前三名為紅色，其餘為藍色
colors = ['#e74c3c' if val <= 143.13 else '#3498db' for val in df['總距離 (km)']]

fig1 = px.bar(
    df, x='演算法', y='總距離 (km)', 
    text='總距離 (km)', 
    title='🏆 各演算法最佳總距離比較 (越低越好)',
    hover_data={'運算時間 (s)': True} # 滑鼠移上去會額外顯示運算時間
)
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
fig1.update_layout(yaxis=dict(range=[120, 205]), template='plotly_white')

# ==========================================
# 3. 繪製圖表二：勞逸平衡分析 (Stacked Bar Chart)
# ==========================================
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=df['演算法'], y=df['車隊一 (間)'], 
    name='車隊一負責間數', marker_color='#f39c12', text=df['車隊一 (間)'], textposition='auto'
))
fig2.add_trace(go.Bar(
    x=df['演算法'], y=df['車隊二 (間)'], 
    name='車隊二負責間數', marker_color='#2c3e50', text=df['車隊二 (間)'], textposition='auto'
))

fig2.update_layout(
    barmode='stack', 
    title='⚖️ 排班工作量分配 (血汗指數分析)',
    yaxis_title='負責宮廟數量 (間)',
    template='plotly_white'
)
# 畫一條完美的 8.5 間平均線
fig2.add_hline(y=8.5, line_dash="dash", line_color="red", annotation_text="完美平均線 (8.5間)")

# ==========================================
# 4. 繪製圖表三：時間與距離權衡 (Scatter Plot)
# ==========================================
fig3 = px.scatter(
    df, x='運算時間 (s)', y='總距離 (km)', 
    color='演算法', size=[20]*len(df), # 點的大小
    hover_name='演算法', 
    title='⏱️ 運算時間 vs 總距離 權衡分析 (Trade-off)',
    template='plotly_white'
)
fig3.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
# 畫出綠色理想區域
fig3.add_vrect(x0=-0.2, x1=1.8, fillcolor="green", opacity=0.1, line_width=0, annotation_text="最理想甜蜜點")

# ==========================================
# 5. 將所有圖表整合成一個 HTML 網頁檔並輸出
# ==========================================
html_content = f"""
<html>
<head>
    <title>大台中宮廟排程演算法 - 效能評估儀表板</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', sans-serif; background-color: #f8f9fa; padding: 20px; }}
        h1 {{ text-align: center; color: #2c3e50; }}
        .chart-container {{ background-color: white; border-radius: 10px; padding: 20px; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0px,0,0.1); }}
    </style>
</head>
<body>
    <h1>🚀 演算法大亂鬥：效能評估互動儀表板</h1>
    <div class="chart-container">{fig1.to_html(full_html=False, include_plotlyjs='cdn')}</div>
    <div class="chart-container">{fig2.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class="chart-container">{fig3.to_html(full_html=False, include_plotlyjs=False)}</div>
</body>
</html>
"""

with open("Interactive_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ 已成功生成互動式網頁：Interactive_Dashboard.html")
print("👉 請直接在左側檔案總管中對 Interactive_Dashboard.html 按右鍵，選擇『在檔案總管中顯示 / Reveal in File Explorer』，然後用 Chrome 或 Edge 瀏覽器打開它！")