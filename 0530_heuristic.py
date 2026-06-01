import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import time

# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
temples = df_dist.columns.tolist()
dist = df_dist.values
n = len(temples)

print("開始執行啟發式演算法 (交替貪婪最近鄰)...")
start_time = time.time()

# 2. 初始化變數
unvisited = set(range(1, n)) # 尚未拜訪的宮廟清單 (不含起點 0)
routes = [[0], [0]]          # 兩台車都從起點 0 (萬和宮) 出發
distances = [0.0, 0.0]       # 紀錄兩台車目前的行駛距離

# 準備記錄歷史軌跡 (Step 0: 還沒出發)
history_log = []
step = 0
history_log.append({
    "iteration": step,
    "cost": 0.0,
    "route1": routes[0][:],
    "route2": routes[1][:]
})

# 3. 啟發式：全域貪婪 (無平衡限制)
while unvisited:
    step += 1
    # 找車隊一離哪個未拜訪宮廟最近
    curr_0 = routes[0][-1]
    nearest_0 = min(unvisited, key=lambda x: dist[curr_0][x])
    min_dist_0 = dist[curr_0][nearest_0]
    
    # 找車隊二離哪個未拜訪宮廟最近
    curr_1 = routes[1][-1]
    nearest_1 = min(unvisited, key=lambda x: dist[curr_1][x])
    min_dist_1 = dist[curr_1][nearest_1]
    
    if min_dist_0 <= min_dist_1:
        routes[0].append(nearest_0)
        distances[0] += min_dist_0
        unvisited.remove(nearest_0)
    else:
        routes[1].append(nearest_1)
        distances[1] += min_dist_1
        unvisited.remove(nearest_1)
        
    history_log.append({
        "iteration": step,
        "cost": round(sum(distances), 2),
        "route1": routes[0][:],
        "route2": routes[1][:]
    })

# 4. 全部跑完後，兩台車都要回到起點 0
step += 1
for i in range(2):
    last_node = routes[i][-1]
    distances[i] += dist[last_node][0]
    routes[i].append(0)

# 記錄最終回到起點的完整軌跡
history_log.append({
    "iteration": step,
    "cost": round(sum(distances), 2),
    "route1": routes[0][:],
    "route2": routes[1][:]
})

end_time = time.time()
solve_time = end_time - start_time
total_distance = sum(distances)

# 5. 輸出比較結果
print("-" * 30)
print(f"耗時: {solve_time:.6f} 秒")
print(f"啟發式總距離: {total_distance:.2f} 公里")

print("\n【全域貪婪 - 車隊一 路線】")
for idx in routes[0]:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {distances[0]:.2f} 公里 | 負責 {len(routes[0])-2} 間宮廟)")

print("\n【全域貪婪 - 車隊二 路線】")
for idx in routes[1]:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(此車行駛距離: {distances[1]:.2f} 公里 | 負責 {len(routes[1])-2} 間宮廟)")


# 將運算結果儲存至 JSON
import json
import os

# 1. 定義這支演算法的名稱
algo_name = "Greedy" 

# 2. 統整
algo_result = {
    algo_name: {
        "distance": round(total_distance, 2),
        "time": round(solve_time, 4),
        "car1_count": len(routes[0]) - 2,
        "car2_count": len(routes[1]) - 2 if len(routes[1]) > 2 else 0,
        "route1": routes[0],
        "route2": routes[1] if len(routes[1]) > 2 else [],
        "history": history_log
    }
}

# 3. 讀取 results.json
json_file = "results.json"
if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        try:
            all_results = json.load(f)
        except json.JSONDecodeError:
            all_results = {}
else:
    all_results = {}

# 4. 將這支演算法更新進去，並覆蓋存檔
all_results.update(algo_result)

with open(json_file, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

print(f"\n【{algo_name}】的運算結果已成功寫入 {json_file}")
