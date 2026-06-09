import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import numpy as np
import math
import time


# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)

df_dist = df_dist.loc[df_dist.columns, :]
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)

start_time = time.time()

MAX_CAPACITY = 16

def calc_dist(route):
    return sum(dist[route[k]][route[k+1]] for k in range(len(route)-1))

def evaluate(routes):
    return calc_dist([0]+routes[0]+[0]) + calc_dist([0]+routes[1]+[0])

# 2. 定義 Destroy Operators
def destroy_random(routes, q):
    new_routes = [r[:] for r in routes]
    removed = []
    for _ in range(q):
        valid_cars = [i for i in range(2) if len(new_routes[i]) > 0]
        if not valid_cars: break
        car = random.choice(valid_cars)
        idx = random.randrange(len(new_routes[car]))
        removed.append(new_routes[car].pop(idx))
    return new_routes, removed

def destroy_worst(routes, q):
    new_routes = [r[:] for r in routes]
    removed = []
    costs = []
    for r_idx in range(2):
        r = [0] + new_routes[r_idx] + [0]
        for i in range(1, len(r)-1):
            cost = dist[r[i-1]][r[i]] + dist[r[i]][r[i+1]] - dist[r[i-1]][r[i+1]]
            costs.append((cost, r_idx, r[i], i-1))
            
    costs.sort(key=lambda x: x[0], reverse=True)
    to_remove = costs[:q]
    for _, r_idx, node, idx in sorted(to_remove, key=lambda x: x[3], reverse=True):
        removed.append(new_routes[r_idx].pop(idx))
    return new_routes, removed

# 3. 定義 Repair Operator
def repair_greedy(routes, removed):
    new_routes = [r[:] for r in routes]
    random.shuffle(removed) 
    
    for node in removed:
        best_car, best_idx, best_delta = -1, -1, float('inf')
        for r_idx in range(2):
            if len(new_routes[r_idx]) >= MAX_CAPACITY: 
                continue 
            for i in range(len(new_routes[r_idx]) + 1):
                temp = new_routes[r_idx][:]
                temp.insert(i, node)
                delta = calc_dist([0]+temp+[0]) - calc_dist([0]+new_routes[r_idx]+[0])
                
                if delta < best_delta:
                    best_delta = delta
                    best_car = r_idx
                    best_idx = i
        new_routes[best_car].insert(best_idx, node)
    return new_routes

# 4. ALNS 主迴圈 (適應性權重與退火機制)
# 初始解 (隨機切一半)
current_routes = [list(range(1, 10)), list(range(10, n))]
current_cost = evaluate(current_routes)
best_routes = [r[:] for r in current_routes]
best_cost = current_cost

# Step 0: 初始瞎猜狀態
history_log = []
history_log.append({
    "iteration": 0,
    "cost": round(best_cost, 2),
    "route1": [0] + best_routes[0] + [0],
    "route2": [0] + best_routes[1] + [0]
})

weights = [1.0, 1.0]
scores = [0, 0]
use_counts = [0, 0]

ITERATIONS = 2000
T = 1000.0
ALPHA = 0.995

for it in range(ITERATIONS):
    total_w = sum(weights)
    probs = [w / total_w for w in weights]
    op_idx = random.choices([0, 1], weights=probs)[0]
    use_counts[op_idx] += 1
    
    q = random.randint(2, 5)
    
    if op_idx == 0:
        temp_routes, removed = destroy_random(current_routes, q)
    else:
        temp_routes, removed = destroy_worst(current_routes, q)
        
    new_routes = repair_greedy(temp_routes, removed)
    new_cost = evaluate(new_routes)
    
    reward = 0
    if new_cost < best_cost:
        best_cost = new_cost
        best_routes = [r[:] for r in new_routes]
        current_routes = [r[:] for r in new_routes]
        current_cost = new_cost
        reward = 3
     
        history_log.append({
            "iteration": it + 1,
            "cost": round(best_cost, 2),
            "route1": [0] + best_routes[0] + [0],
            "route2": [0] + best_routes[1] + [0]
        })
        
    elif new_cost < current_cost:
        current_routes = [r[:] for r in new_routes]
        current_cost = new_cost
        reward = 2
    else:
        if math.exp(-(new_cost - current_cost) / T) > random.random():
            current_routes = [r[:] for r in new_routes]
            current_cost = new_cost
            reward = 1 
            
    scores[op_idx] += reward
    
    if (it + 1) % 100 == 0:
        for i in range(2):
            if use_counts[i] > 0:
                weights[i] = 0.8 * weights[i] + 0.2 * (scores[i] / use_counts[i])
        scores = [0, 0]
        use_counts = [0, 0]
        
    T *= ALPHA # 降溫


# 5. 加上 2-Opt 局部優化
def two_opt_single(route):
    best_route = route[:]
    best_dist = calc_dist(best_route)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_route) - 2):
            for j in range(i + 2, len(best_route)):
                new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                new_dist = calc_dist(new_route)
                if new_dist < best_dist - 0.0001: 
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved: break
    return best_route

final_route_1 = [0] + best_routes[0] + [0]
final_route_2 = [0] + best_routes[1] + [0]
final_route_1 = two_opt_single(final_route_1)
final_route_2 = two_opt_single(final_route_2)

dist_1 = calc_dist(final_route_1)
dist_2 = calc_dist(final_route_2)
final_total = dist_1 + dist_2
solve_time = time.time() - start_time

# 記錄最後 2-Opt 拋光完的路線
history_log.append({
    "iteration": "Final 2-Opt", 
    "cost": round(final_total, 2),
    "route1": final_route_1[:],
    "route2": final_route_2[:]
})

# 6. 輸出最終結果
print(f"總耗時: {solve_time:.6f} 秒")
print(f"最佳總距離: {final_total:.2f} 公里")

print(f"\n 演算法偏好: [隨機破壞權重: {weights[0]:.2f}] vs [最差破壞權重: {weights[1]:.2f}]")

print("\n【ALNS - 車隊一 路線】")
for idx in final_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {dist_1:.2f} 公里 | 負責 {len(final_route_1)-2} 間宮廟)")

print("\n【ALNS - 車隊二 路線】")
for idx in final_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {dist_2:.2f} 公里 | 負責 {len(final_route_2)-2} 間宮廟)")


# 將運算結果儲存至 JSON
import json
import os

algo_name = "ALNS"
json_file = "results.json"

if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            all_results = json.load(f)
        except json.JSONDecodeError:
            all_results = {}
else:
    all_results = {}

old_best_dist = float('inf')
if algo_name in all_results and "distance" in all_results[algo_name]:
    old_best_dist = all_results[algo_name]["distance"]

if final_total <= old_best_dist:
    print(f"\n[{algo_name}] 最佳里程紀錄為 {final_total:.2f} km")
    
    all_results[algo_name] = {
        "distance": round(final_total, 2),
        "time": round(solve_time, 4),
        "car1_count": len(final_route_1) - 2,
        "car2_count": len(final_route_2) - 2 if len(final_route_2) > 2 else 0,
        "route1": final_route_1,
        "route2": final_route_2 if len(final_route_2) > 2 else [],
        "history": history_log 
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
        
else:
    print(f"[{algo_name}] 這次距離 ({final_total:.2f} km) 未打破歷史紀錄 ({old_best_dist:.2f} km)，保持原結果。")
