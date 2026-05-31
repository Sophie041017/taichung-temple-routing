import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import math
import time

# ==========================================
# 1. 讀取距離矩陣
# ==========================================
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)

# ==========================================
# 2. 定義「狀態解碼」與「成本函數」 (無平衡限制版：最佳切斷點法)
# ==========================================
def calc_total_dist(state):
    best_split_cost = float('inf')
    best_dist1 = 0
    best_dist2 = 0
    best_route1 = None
    best_route2 = None
    
    for k in range(1, n - 1):
        route1 = [0] + state[:k] + [0]
        route2 = [0] + state[k:] + [0]
        
        dist1 = sum(dist[route1[i]][route1[i+1]] for i in range(len(route1)-1))
        dist2 = sum(dist[route2[i]][route2[i+1]] for i in range(len(route2)-1))
        total = dist1 + dist2
        
        if total < best_split_cost:
            best_split_cost = total
            best_dist1 = dist1
            best_dist2 = dist2
            best_route1 = route1
            best_route2 = route2
            
    return best_split_cost, best_dist1, best_dist2, best_route1, best_route2

# ==========================================
# 3. 設定 SA 初始參數
# ==========================================
INITIAL_TEMP = 1000.0   # 初始溫度
FINAL_TEMP = 0.1        # 終止溫度
ALPHA = 0.999           # 降溫速率

# 產生初始解 (隨機洗牌)
current_state = list(range(1, n))
random.shuffle(current_state)

current_cost, _, _, init_r1, init_r2 = calc_total_dist(current_state)
best_state = current_state[:]
best_cost = current_cost

print("🚀 啟動模擬退火法 (Simulated Annealing)...")
start_time = time.time()

# ★ 準備記錄歷史軌跡 (Step 0: 初始亂數狀態) ★
history_log = []
history_log.append({
    "iteration": 0,
    "cost": round(best_cost, 2),
    "route1": init_r1[:],
    "route2": init_r2[:]
})

# ==========================================
# 4. 退火主迴圈
# ==========================================
temp = INITIAL_TEMP
iteration = 0

while temp > FINAL_TEMP:
    # 產生鄰居 (Neighbor)：隨機挑選兩個宮廟「交換順序」
    neighbor_state = current_state[:]
    idx1, idx2 = random.sample(range(len(neighbor_state)), 2)
    neighbor_state[idx1], neighbor_state[idx2] = neighbor_state[idx2], neighbor_state[idx1]
    
    neighbor_cost, _, _, _, _ = calc_total_dist(neighbor_state)
    
    # 計算能量差 (Delta)
    delta = neighbor_cost - current_cost
    
    # 判斷是否接受新解
    if delta < 0:
        # 新路線更短！無條件接受
        current_state = neighbor_state[:]
        current_cost = neighbor_cost
        
        # 看看是不是歷史新低
        if neighbor_cost < best_cost:
            best_state = neighbor_state[:]
            best_cost = neighbor_cost
            
            # ★ 動態記錄：溫度下降過程中，只要破了歷史最佳紀錄就存下來 ★
            _, _, _, h_r1, h_r2 = calc_total_dist(best_state)
            history_log.append({
                "iteration": iteration + 1,
                "cost": round(best_cost, 2),
                "route1": h_r1[:],
                "route2": h_r2[:]
            })
            
    else:
        # 新路線變長了！這時套用 SA 機率公式： P = exp(-delta / T)
        prob = math.exp(-delta / temp)
        if random.random() < prob:
            # 雖然比較爛，但機率過關，我們「勉強接受」以跳出局部最佳解
            current_state = neighbor_state[:]
            current_cost = neighbor_cost
            
    # 降溫
    temp *= ALPHA
    iteration += 1

# ==========================================
# 5. 輸出最終結果
# ==========================================
_, best_dist_1, best_dist_2, best_route_1, best_route_2 = calc_total_dist(best_state)
solve_time = time.time() - start_time

print("\n" + "="*50)
print("🏆 模擬退火法 (SA) 最佳化結果 [無平衡限制版]")
print("="*50)
print(f"總耗時: {solve_time:.6f} 秒 (共迭代 {iteration} 次)")
print(f"最佳總距離: {best_cost:.2f} 公里")

print("\n📍 【SA 優化 - 車隊一 路線】")
for idx in best_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {best_dist_1:.2f} 公里 | 負責 {len(best_route_1)-2} 間宮廟)")

print("\n📍 【SA 優化 - 車隊二 路線】")
for idx in best_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {best_dist_2:.2f} 公里 | 負責 {len(best_route_2)-2} 間宮廟)")


# ==========================================
# ★ 自動化管線：將運算結果儲存至 JSON ★
# ==========================================
import json
import os

algo_name = "SA" 

algo_result = {
    algo_name: {
        "distance": round(best_cost, 2),          
        "time": round(solve_time, 4),             
        "car1_count": len(best_route_1) - 2,      
        "car2_count": len(best_route_2) - 2 if len(best_route_2) > 2 else 0, 
        "route1": best_route_1,
        "route2": best_route_2 if len(best_route_2) > 2 else [],
        "history": history_log  # ★ 將退火收斂過程交接給 JSON！
    }
}

json_file = "results.json"
if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            all_results = json.load(f)
        except json.JSONDecodeError:
            all_results = {}
else:
    all_results = {}

all_results.update(algo_result)

with open(json_file, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

print(f"\n💾 系統提示：【{algo_name}】的運算結果已成功寫入 {json_file}！")