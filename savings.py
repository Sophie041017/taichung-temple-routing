import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import time
import json
import os

# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
df_dist = df_dist.loc[df_dist.columns, :]

temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)


start_time = time.time()


# 2. 初始化：每間宮廟都先各自成一條路線 (總部 -> 宮廟 -> 總部)
# routes 裡面存放 17 條獨立路線 (不包含起終點 0，方便後續串接)
routes = [[i] for i in range(1, n)]

def calc_dist(route):
    if not route or len(route) < 2: return 0
    return sum(dist[route[k]][route[k+1]] for k in range(len(route)-1))

def calc_current_total(current_routes):
    total = 0
    for r in current_routes:
        total += calc_dist([0] + r + [0])
    return total

# Step 0: 最原始放射狀的狀態
history_log = []
step_count = 0

def log_history(current_routes, step):
    # 要塞兩台車給 JSON，但現在路線可能有 17 條
    # 策略：把最長的那條當車隊一，其他碎路線全部暫時接在一起當車隊二
    sorted_r = sorted(current_routes, key=len, reverse=True)
    r1 = [0] + sorted_r[0] + [0] if len(sorted_r) > 0 else []
    
    r2_core = []
    for r in sorted_r[1:]:
        r2_core.extend(r)
    r2 = [0] + r2_core + [0] if r2_core else []
    
    cost = calc_current_total(current_routes)
    
    history_log.append({
        "iteration": step,
        "cost": round(cost, 2),
        "route1": r1[:],
        "route2": r2[:]
    })

# 記錄第 0 步
log_history(routes, step_count)


# 3. 計算所有節點對的 Savings 值
savings = []
for i in range(1, n):
    for j in range(i + 1, n):
        s = dist[0][i] + dist[0][j] - dist[i][j]
        savings.append((s, i, j))

savings.sort(key=lambda x: x[0], reverse=True)


# 4. 合併主迴圈
for s, i, j in savings:
    if len(routes) == 2:
        break 

    route_i = next((r for r in routes if i in r), None)
    route_j = next((r for r in routes if j in r), None)

    if route_i != route_j:
        if (route_i[0] == i or route_i[-1] == i) and (route_j[0] == j or route_j[-1] == j):
            
            if route_i[0] == i:
                route_i.reverse()
            if route_j[-1] == j:
                route_j.reverse()
            
            new_route = route_i + route_j
            routes.remove(route_i)
            routes.remove(route_j)
            routes.append(new_route)
            
            step_count += 1
            log_history(routes, step_count)

while len(routes) > 2:
    routes.sort(key=len)
    routes[0] = routes[0] + routes[1]
    routes.pop(1)
    step_count += 1
    log_history(routes, step_count)

final_routes = [[0] + r + [0] for r in routes]


# 5. 加上 2-Opt 局部優化
def two_opt(route):
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

opt_route_1 = two_opt(final_routes[0])
opt_route_2 = two_opt(final_routes[1])
opt_dist_1 = calc_dist(opt_route_1)
opt_dist_2 = calc_dist(opt_route_2)
opt_total = opt_dist_1 + opt_dist_2
solve_time = time.time() - start_time


history_log.append({
    "iteration": "Final 2-Opt", 
    "cost": round(opt_total, 2),
    "route1": opt_route_1[:],
    "route2": opt_route_2[:]
})


# 6. 輸出最終結果
print(f"總耗時: {solve_time:.6f} 秒")
print(f"最佳總距離: {opt_total:.2f} 公里")

print("\n【 Savings - 車隊一 路線】")
for idx in opt_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {opt_dist_1:.2f} 公里 | 負責 {len(opt_route_1)-2} 間宮廟)")

print("\n【 Savings - 車隊二 路線】")
for idx in opt_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {opt_dist_2:.2f} 公里 | 負責 {len(opt_route_2)-2} 間宮廟)")


# 將運算結果儲存至 JSON 
algo_name = "Savings" 

algo_result = {
    algo_name: {
        "distance": round(opt_total, 2),          
        "time": round(solve_time, 4),             
        "car1_count": len(opt_route_1) - 2,       
        "car2_count": len(opt_route_2) - 2 if len(opt_route_2) > 2 else 0,
        "route1": opt_route_1,
        "route2": opt_route_2 if len(opt_route_2) > 2 else [],
        "history": history_log 
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

print(f"\n【{algo_name}】的運算結果已成功寫入 {json_file}")
