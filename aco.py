import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import numpy as np
import time

# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)

# 2. 參數設定
N_ANTS = 30          # 螞蟻數量 (每回合派 30 隻螞蟻出去找路)
ITERATIONS = 100     # 迭代次數 (讓蟻群找 100 回合)
ALPHA = 1.0          # 費洛蒙 (數值越高，螞蟻越盲從前人的路線)
BETA = 2.0           # 距離可見度 (數值越高，螞蟻越傾向選眼前最近的宮廟)
EVAPORATION = 0.5    # 費洛蒙揮發率 (0.5 代表每回合蒸發 50%，避免卡在局部最佳解)
Q = 100              # 費洛蒙釋放總量常數

# 初始化費洛蒙矩陣 (一開始每條路徑的費洛蒙濃度都設為 0.1)
pheromone = [[0.1 for _ in range(n)] for _ in range(n)]


# 3. 螞蟻挑選下一站 (輪盤法)
def select_next_node(current, unvisited):
    probabilities = []
    
    # 計算前往每個未拜訪宮廟的機率
    for node in unvisited:
        tau = pheromone[current][node] ** ALPHA  # 費洛蒙濃度
        # 距離越短，可見度 eta 越大 (加上 1e-10 避免除以零)
        eta = (1.0 / (dist[current][node] + 1e-10)) ** BETA 
        probabilities.append((node, tau * eta))
        
    # 將機率轉化為輪盤比例，隨機抽取下一站
    total = sum(p[1] for p in probabilities)
    rand = random.uniform(0, total)
    cumulative = 0
    for node, prob in probabilities:
        cumulative += prob
        if cumulative >= rand:
            return node
    return probabilities[-1][0]


# 4. ACO 演算法主迴圈
start_time = time.time()

best_overall_cost = float('inf')
best_route_1 = None
best_route_2 = None
best_dist_1 = 0
best_dist_2 = 0


history_log = []

for iteration in range(ITERATIONS):
    all_routes = []
    all_costs = []
    
    # 步驟一：每隻螞蟻開始建構路線
    for ant in range(N_ANTS):
        unvisited = set(range(1, n))
        
        # 螞蟻一次把 17 間宮廟全部排完 (先不考慮分兩台車)
        route_seq = []
        current = 0
        for _ in range(n - 1): # 總共 17 間
            next_node = select_next_node(current, unvisited)
            route_seq.append(next_node)
            unvisited.remove(next_node)
            current = next_node
            
        # 尋找「最佳切斷點」：測試 1~16 間的所有切法，找出總距離最短的分配
        best_split_cost = float('inf')
        best_r1, best_r2 = None, None
        
        # k 代表車隊一分配到的宮廟數量 (1 到 16)
        for k in range(1, n - 1):
            r1 = [0] + route_seq[:k] + [0]
            r2 = [0] + route_seq[k:] + [0]
            
            c1 = sum(dist[r1[i]][r1[i+1]] for i in range(len(r1)-1))
            c2 = sum(dist[r2[i]][r2[i+1]] for i in range(len(r2)-1))
            
            if c1 + c2 < best_split_cost:
                best_split_cost = c1 + c2
                best_r1, best_r2 = r1, r2
                
        route1, route2 = best_r1, best_r2
        cost1 = sum(dist[route1[i]][route1[i+1]] for i in range(len(route1)-1))
        cost2 = sum(dist[route2[i]][route2[i+1]] for i in range(len(route2)-1))
        total_cost = cost1 + cost2
        
        all_routes.append((route1, route2))
        all_costs.append((total_cost, cost1, cost2))
        
        # 更新歷史最佳紀錄
        if total_cost < best_overall_cost:
            best_overall_cost = total_cost
            best_route_1, best_route_2 = route1[:], route2[:]
            best_dist_1, best_dist_2 = cost1, cost2
            
            # 動態記錄：只要有螞蟻找到更短的路線，就記錄到 history_log 中
            history_log.append({
                "iteration": iteration + 1,  # 記錄這是在第幾回合找到的
                "cost": round(best_overall_cost, 2),
                "route1": best_route_1[:],
                "route2": best_route_2[:]
            })

    # 步驟二：費洛蒙揮發 (蒸發掉一部分舊的費洛蒙)
    for i in range(n):
        for j in range(n):
            pheromone[i][j] *= (1.0 - EVAPORATION)
            
    # 步驟三：螞蟻在走過的路徑上留下新費洛蒙
    for i in range(N_ANTS):
        r1, r2 = all_routes[i]
        total_c = all_costs[i][0]
        deposit = Q / total_c  # 路線越短，留下的費洛蒙越多
        
        # 為車隊一的路徑增加費洛蒙
        for j in range(len(r1)-1):
            pheromone[r1[j]][r1[j+1]] += deposit
            pheromone[r1[j+1]][r1[j]] += deposit
        # 為車隊二的路徑增加費洛蒙
        for j in range(len(r2)-1):
            pheromone[r2[j]][r2[j+1]] += deposit
            pheromone[r2[j+1]][r2[j]] += deposit


# 5. 輸出最終結果
solve_time = time.time() - start_time


print(f"總耗時: {solve_time:.6f} 秒 (螞蟻數: {N_ANTS}, 迭代: {ITERATIONS})")
print(f"最佳總距離: {best_overall_cost:.2f} 公里")

print("\n【ACO - 車隊一 路線】")
for idx in best_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_1:.2f} 公里 | 負責 {len(best_route_1)-2} 間宮廟)")

print("\n【ACO - 車隊二 路線】")
for idx in best_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_2:.2f} 公里 | 負責 {len(best_route_2)-2} 間宮廟)")




import json
import os

algo_name = "ACO"
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

# 2. 找出舊的歷史最佳距離 (如果以前沒跑過，就設定為無限大)
old_best_dist = float('inf')
if algo_name in all_results and "distance" in all_results[algo_name]:
    old_best_dist = all_results[algo_name]["distance"]

# 3.
if best_overall_cost < old_best_dist:
    print(f"[{algo_name}] 發現更佳路線，從 {old_best_dist:.2f} km 變為 {best_overall_cost:.2f} km")
    
    # 準備要寫入的新資料
    all_results[algo_name] = {
        "distance": round(best_overall_cost, 2),
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
    print(f"[{algo_name}] 這次距離 ({best_overall_cost:.2f} km) 未打破歷史紀錄 ({old_best_dist:.2f} km)，保持原結果。")
