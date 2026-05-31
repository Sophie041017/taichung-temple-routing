import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import time

# ==========================================
# 1. 讀取距離矩陣
# ==========================================
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)

print("正在執行初始解：交替貪婪演算法...")
start_time_greedy = time.time()

# ==========================================
# 2. 生成初始解 (全域貪婪 - 無平衡限制)
# ==========================================
unvisited = set(range(1, n))
routes = [[0], [0]]

while unvisited:
    curr_0 = routes[0][-1]
    nearest_0 = min(unvisited, key=lambda x: dist[curr_0][x])
    min_dist_0 = dist[curr_0][nearest_0]
    
    curr_1 = routes[1][-1]
    nearest_1 = min(unvisited, key=lambda x: dist[curr_1][x])
    min_dist_1 = dist[curr_1][nearest_1]
    
    if min_dist_0 <= min_dist_1:
        routes[0].append(nearest_0)
        unvisited.remove(nearest_0)
    else:
        routes[1].append(nearest_1)
        unvisited.remove(nearest_1)

# 加回起終點
for i in range(2):
    routes[i].append(0)

def calc_route_dist(route):
    return sum(dist[route[k]][route[k+1]] for k in range(len(route)-1))

greedy_dist_1 = calc_route_dist(routes[0])
greedy_dist_2 = calc_route_dist(routes[1])
greedy_total = greedy_dist_1 + greedy_dist_2
greedy_time = time.time() - start_time_greedy

print(f"貪婪法總距離: {greedy_total:.2f} 公里 (車隊一: {greedy_dist_1:.2f} | 車隊二: {greedy_dist_2:.2f})")

# ==========================================
# ★ 準備記錄 2-Opt 歷史軌跡 ★
# ==========================================
history_log = []
step_count = [0] # 用 list 包裝以便在函數內修改
current_routes = [routes[0][:], routes[1][:]]

# Step 0: 記錄 Greedy 剛跑完，還沒開始解結的「超亂狀態」
history_log.append({
    "iteration": 0,
    "cost": round(greedy_total, 2),
    "route1": current_routes[0][:],
    "route2": current_routes[1][:]
})

# ==========================================
# 3. 2-Opt 局部搜尋演算法 (加入動態軌跡記錄)
# ==========================================
print("\n啟動 2-Opt 演算法，解開交叉路線...")
start_time_2opt = time.time()

def two_opt_with_history(car_idx, dist_matrix):
    best_route = current_routes[car_idx][:]
    best_dist = calc_route_dist(best_route)
    improved = True
    
    while improved:
        improved = False
        for i in range(1, len(best_route) - 2):
            for j in range(i + 2, len(best_route)):
                # 反轉 i 到 j-1 的路線段
                new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                new_dist = calc_route_dist(new_route)
                
                # 如果解開了交叉，距離變短了
                if new_dist < best_dist - 0.0001: 
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    
                    # ★ 動態記錄：更新全域狀態並存入 history_log ★
                    current_routes[car_idx] = best_route[:]
                    step_count[0] += 1
                    total_cost = calc_route_dist(current_routes[0]) + calc_route_dist(current_routes[1])
                    
                    history_log.append({
                        "iteration": step_count[0],
                        "cost": round(total_cost, 2),
                        "route1": current_routes[0][:],
                        "route2": current_routes[1][:]
                    })
                    break # 跳出內圈，重新掃描
            if improved:
                break # 跳出外圈，重新掃描
    return best_route, best_dist

# 依序幫車隊一、車隊二解開打結
optimized_route_1, opt_dist_1 = two_opt_with_history(0, dist)
optimized_route_2, opt_dist_2 = two_opt_with_history(1, dist)

opt_total = opt_dist_1 + opt_dist_2
opt_time = (time.time() - start_time_2opt) + greedy_time

# ==========================================
# 4. 輸出最終比較結果
# ==========================================
print("\n" + "="*50)
print("🏆 2-Opt 演算法優化結果")
print("="*50)
print(f"總耗時: {opt_time:.6f} 秒")
print(f"優化後總距離: {opt_total:.2f} 公里 (成功縮減了 {greedy_total - opt_total:.2f} 公里的冤枉路！)")

print("\n📍 【2-Opt 優化後 - 車隊一 路線】")
for idx in optimized_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {opt_dist_1:.2f} 公里 | 負責 {len(optimized_route_1)-2} 間宮廟)")

print("\n📍 【2-Opt 優化後 - 車隊二 路線】")
for idx in optimized_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {opt_dist_2:.2f} 公里 | 負責 {len(optimized_route_2)-2} 間宮廟)")


# ==========================================
# ★ 自動化管線：將運算結果儲存至 JSON ★
# ==========================================
import json
import os

algo_name = "2-Opt" 

algo_result = {
    algo_name: {
        "distance": round(opt_total, 2),          
        "time": round(opt_time, 4),               
        "car1_count": len(optimized_route_1) - 2, 
        "car2_count": len(optimized_route_2) - 2 if len(optimized_route_2) > 2 else 0, 
        "route1": optimized_route_1,                      
        "route2": optimized_route_2 if len(optimized_route_2) > 2 else [],
        "history": history_log  # ★ 將解結過程交接給 JSON！
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