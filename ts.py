import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import numpy as np
import time
import json
import os


# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
df_dist = df_dist.loc[df_dist.columns, :]
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)


# 2. 定義狀態解碼 & 成本函數
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


# 3. 設定禁忌搜尋參數
MAX_ITER = 300       # 最大迭代次數
TABU_TENURE = 15     # 禁忌期限

# 產生初始解
current_state = list(range(1, n))
random.shuffle(current_state)

current_cost, _, _, init_r1, init_r2 = calc_total_dist(current_state)
best_state = current_state[:]
best_cost = current_cost

# 禁忌名單字典
tabu_list = {} 

start_time = time.time()

# Step 0: 初始亂數狀態
history_log = []
history_log.append({
    "iteration": 0,
    "cost": round(best_cost, 2),
    "route1": init_r1[:],
    "route2": init_r2[:]
})


# 4. 禁忌搜尋主迴圈
for iteration in range(MAX_ITER):
    best_neighbor = None
    best_neighbor_cost = float('inf')
    best_move = None
    
    # 探索所有可能的鄰居
    for i in range(len(current_state)):
        for j in range(i + 1, len(current_state)):
            neighbor = current_state[:]
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            
            cost, _, _, _, _ = calc_total_dist(neighbor)
            
            v1, v2 = current_state[i], current_state[j]
            move = (min(v1, v2), max(v1, v2))
            
            is_tabu = move in tabu_list and tabu_list[move] > iteration
            
            # 特赦條件
            if is_tabu and cost < best_cost:
                is_tabu = False
                
            if not is_tabu:
                if cost < best_neighbor_cost:
                    best_neighbor_cost = cost
                    best_neighbor = neighbor
                    best_move = move

    if best_neighbor is not None:
        current_state = best_neighbor[:]
        current_cost = best_neighbor_cost
        
        tabu_list[best_move] = iteration + TABU_TENURE
        
        # 如果超越了歷史最佳紀錄，更新最佳解
        if current_cost < best_cost:
            best_cost = current_cost
            best_state = current_state[:]
            
            _, _, _, h_r1, h_r2 = calc_total_dist(best_state)
            history_log.append({
                "iteration": iteration + 1,
                "cost": round(best_cost, 2),
                "route1": h_r1[:],
                "route2": h_r2[:]
            })


# 5. 輸出最終結果
_, best_dist_1, best_dist_2, best_route_1, best_route_2 = calc_total_dist(best_state)
solve_time = time.time() - start_time

print(f"總耗時: {solve_time:.6f} 秒 (共迭代 {MAX_ITER} 次，每次評估 136 個鄰居)")
print(f"最佳總距離: {best_cost:.2f} 公里")

print("\n【Tabu Search - 車隊一 路線】")
for idx in best_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_1:.2f} 公里 | 負責 {len(best_route_1)-2} 間宮廟)")

print("\n【Tabu Search - 車隊二 路線】")
for idx in best_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_2:.2f} 公里 | 負責 {len(best_route_2)-2} 間宮廟)")


# 將運算結果儲存至 JSON
algo_name = "TS"
json_file = "results.json"

# 1. 先讀取目前的歷史紀錄
if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            all_results = json.load(f)
        except json.JSONDecodeError:
            all_results = {}
else:
    all_results = {}

# 2. 找出舊的歷史最佳距離
old_best_dist = float('inf')
if algo_name in all_results and "distance" in all_results[algo_name]:
    old_best_dist = all_results[algo_name]["distance"]

if best_cost < old_best_dist:
    print(f"\n[{algo_name}] 最佳里程紀錄為 {best_cost:.2f} km")
    
    # 準備要寫入的新資料
    all_results[algo_name] = {
        "distance": round(best_cost, 2),
        "time": round(solve_time, 4),
        "car1_count": len(best_route_1) - 2,
        "car2_count": len(best_route_2) - 2 if len(best_route_2) > 2 else 0,
        "route1": best_route_1,
        "route2": best_route_2 if len(best_route_2) > 2 else [],
        "history": history_log 
    }
    
    # 執行存檔覆蓋
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
        
else:
    print(f"[{algo_name}] 這次距離 ({best_cost:.2f} km) 未打破歷史紀錄 ({old_best_dist:.2f} km)，保持原結果。")
