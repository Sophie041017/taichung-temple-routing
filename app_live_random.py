import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import json
import os
import datetime
import subprocess

# 頁面基本設定
st.set_page_config(page_title="候選人拜票路線問題", layout="wide", page_icon="⛩️")

# 1. 載入資料 & 計算數據
if not os.path.exists("results.json"):
    st.error("找不到 results.json，請先執行演算法以產生數據")
    st.stop()

with open("results.json", "r", encoding="utf-8") as f:
    live_data = json.load(f)

df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
dist_matrix = df_dist.values
temples = df_dist.columns.tolist()

def calc_route_dist(route):
    if not route or len(route) < 2: return 0
    return sum(dist_matrix[route[k]][route[k+1]] for k in range(len(route)-1))

algos, distances, comp_times, car1_counts, car2_counts = [], [], [], [], []
fleet_max_times, balance_diffs = [], []

for algo_name, result in live_data.items():
    algos.append(algo_name)
    distances.append(result["distance"])
    comp_times.append(result["time"])
    
    c1, c2 = result["car1_count"], result["car2_count"]
    car1_counts.append(c1)
    car2_counts.append(c2)
    balance_diffs.append(abs(c1 - c2))
    
    r1, r2 = result.get("route1", []), result.get("route2", [])
    d1, d2 = calc_route_dist(r1), calc_route_dist(r2)
    
    time1 = (d1 / 0.75) + (c1 * 30)
    time2 = (d2 / 0.75) + (c2 * 30)
    fleet_max_times.append(max(time1, time2))

df = pd.DataFrame({
    '演算法': algos,
    '總距離 (km)': distances,
    '運算時間 (s)': comp_times,
    '車隊一 (間)': car1_counts,
    '車隊二 (間)': car2_counts,
    '車隊耗時 (分)': fleet_max_times,
    '排班差異': balance_diffs
}).sort_values(by='總距離 (km)').reset_index(drop=True)

# KPI 計算
best_dist_val = df['總距離 (km)'].min()
best_dist_algo = df.loc[df['總距離 (km)'].idxmin(), '演算法']

fastest_time_val = df['車隊耗時 (分)'].min()
fastest_time_algo = df.loc[df['車隊耗時 (分)'].idxmin(), '演算法']
fastest_h, fastest_m = int(fastest_time_val // 60), int(fastest_time_val % 60)

start_time_dt = datetime.datetime(2026, 1, 1, 9, 0, 0) 
finish_time_dt = start_time_dt + datetime.timedelta(minutes=fastest_time_val)
finish_time_str = finish_time_dt.strftime('%H:%M')

df_bal = df.sort_values(by=['排班差異', '總距離 (km)'])
best_bal_algo = df_bal.iloc[0]['演算法']
best_bal_str = f"{df_bal.iloc[0]['車隊一 (間)']} 間 / {df_bal.iloc[0]['車隊二 (間)']} 間"

# 2. 側邊欄：選單 & 重新計算
with st.sidebar:
    st.title("候選人拜票路線問題")
    st.markdown("---")
    st.subheader("A. 路線模擬")
    
    if 'last_selected' not in st.session_state:
        st.session_state.last_selected = df['演算法'].iloc[0] 
        
    default_idx = 0
    if st.session_state.last_selected in df['演算法'].values:
        default_idx = int(df[df['演算法'] == st.session_state.last_selected].index[0])
        
    dropdown_options = [f"{row['演算法']} ({row['總距離 (km)']:.2f} km)" for _, row in df.iterrows()]
    
    selected_option = st.selectbox("在地圖上檢視演算法路線：", dropdown_options, index=default_idx)
    selected_algo = selected_option.split(" ")[0]
    
    st.session_state.last_selected = selected_algo
    
    # 後端重新運算
    if st.button(f"重新運算 {selected_algo}", use_container_width=True):
        file_map = {
            "Greedy": "0530_heuristic.py", 
            "MILP": "0530_milp.py",
            "2-Opt": "0601_2opt.py",
            "Savings": "0601_savings.py",
            "SA": "0601_sa.py",
            "GA": "0601_ga.py",
            "ALNS": "0601_alns.py",
            "ACO": "0601_aco.py",
            "MA": "0601_ma.py",
            "TS": "0601_tabu.py"
        }
        
        if selected_algo in file_map:
            target_file = file_map[selected_algo]
            with st.spinner("運算中"):
                my_env = os.environ.copy() 
                result = subprocess.run(
                    [sys.executable, "-u", target_file], 
                    capture_output=True, 
                    text=True,
                    env=my_env
                )
            
            if result.returncode == 0:
                st.rerun() 
            else:
                st.error(f"❌ 演算法執行失敗！請檢查背景錯誤：\n\n{result.stderr}")
        else:
            st.error("系統找不到對應的演算法檔案")
            
    st.markdown("---")
    st.subheader("B. 數據分析")
    st.markdown("- 總距離比較 (油耗)\n- 車隊耗時 vs 總距離\n- 車隊工作分配")

# 3. 頂部儀表板
col1, col2, col3 = st.columns(3)
col1.metric("🏆 最短距離", f"{best_dist_val:.2f} km", f"{best_dist_algo}")
col2.metric("⚡ 車隊耗時最少", f"{fastest_h} 小時 {fastest_m} 分", f"預計 {finish_time_str} 返回目的地")
col3.metric("⚖️ 最佳車隊排班", best_bal_str, f"{best_bal_algo}")

# 4. 路線模擬地圖 (移除時間軸，只顯示最終結果)
st.markdown(f"### 📍 路線模擬地圖：{selected_algo}")

algo_data = live_data[selected_algo]
r1 = algo_data.get("route1", [])
r2 = algo_data.get("route2", [])

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

m = folium.Map(location=[24.22, 120.65], zoom_start=11, tiles="OpenStreetMap")
folium.Marker([temple_coords[0][1], temple_coords[0][2]], tooltip="南屯萬和宮", icon=folium.Icon(color="red", icon="home")).add_to(m)

def draw_route(route, color, car_name):
    if not route or len(route) < 2: return
    points = [[temple_coords[i][1], temple_coords[i][2]] for i in route]
    folium.PolyLine(points, color=color, weight=5, opacity=0.8).add_to(m)
    
    for seq, node_idx in enumerate(route):
        if seq == 0 or seq == len(route) - 1: continue 
        lat, lon = temple_coords[node_idx][1], temple_coords[node_idx][2]
        icon_html = f'''
        <div style="background-color: {color}; color: white; border-radius: 50%;
                    width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
                    font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            {seq}
        </div>
        '''
        folium.Marker(
            [lat, lon],
            tooltip=f"{car_name} - 第 {seq} 站：{temple_coords[node_idx][0]}",
            icon=folium.DivIcon(html=icon_html, icon_size=(22, 22), icon_anchor=(11, 11))
        ).add_to(m)

draw_route(r1, "#f39c12", "車隊一")  
draw_route(r2, "#3498db", "車隊二")  

st_folium(m, width=1200, height=500, returned_objects=[])

# 5. 效能分析圖表
st.markdown("### 📍 演算法比較 ")

colors = ['#e74c3c' if val == best_dist_val else '#3498db' for val in df['總距離 (km)']]

fig1 = px.bar(df, x='演算法', y='總距離 (km)', text='總距離 (km)', title='總距離比較 (油耗成本)')
fig1.update_traces(marker_color=colors, textposition='outside', texttemplate='%{text:.2f}')
fig1.update_layout(yaxis=dict(range=[df['總距離 (km)'].min()-20, df['總距離 (km)'].max()+25]))

fig2 = px.scatter(df, x='車隊耗時 (分)', y='總距離 (km)', color='演算法', size=[20]*len(df), hover_name='演算法', title='車隊耗時 vs 總距離')

# 調整綠色理想區的範圍：從最快耗時往後抓 30 分鐘的容許值作為高效率區間
min_time = df['車隊耗時 (分)'].min()
fig2.add_vrect(x0=min_time - 5, x1=min_time + 30, fillcolor="#2ecc71", opacity=0.15, line_width=0, annotation_text="高效率區", annotation_font_color="white")

fig3 = go.Figure()
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊一 (間)'], name='車隊一', marker_color='#f39c12', text=df['車隊一 (間)'], textposition='auto'))
fig3.add_trace(go.Bar(x=df['演算法'], y=df['車隊二 (間)'], name='車隊二', marker_color='#3498db', text=df['車隊二 (間)'], textposition='auto'))
fig3.update_layout(barmode='stack', title='車隊工作分配', yaxis_title='負責宮廟數量')
fig3.add_hline(y=8.5, line_dash="dash", line_color="#e74c3c", annotation_text="平均線")

st.plotly_chart(fig1, width="stretch")
col_a, col_b = st.columns(2)
with col_a: st.plotly_chart(fig2, width="stretch")
with col_b: st.plotly_chart(fig3, width="stretch")
