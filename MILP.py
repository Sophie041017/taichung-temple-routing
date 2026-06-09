import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import pulp
import time
import datetime
import json
import os

# 1. 讀取生成的距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
df_dist = df_dist.loc[df_dist.columns, :]

temples = df_dist.columns.tolist()
n = len(temples)
dist = df_dist.values

# 起始點
start_time = time.time()

# 2. 建立 mTSP 數學模型 (最小化總距離)
prob = pulp.LpProblem("mTSP_Temple_Tour", pulp.LpMinimize)

# 3. 決策變數
x = pulp.LpVariable.dicts("x", ((i, j) for i in range(n) for j in range(n)), cat='Binary')
u = pulp.LpVariable.dicts("u", (i for i in range(1, n)), lowBound=1, upBound=n-1, cat='Continuous')

# 4. 目標函數：總距離最短
prob += pulp.lpSum(dist[i][j] * x[i, j] for i in range(n) for j in range(n))

# 5. 限制式
for i in range(n):
    prob += x[i, i] == 0
for i in range(1, n):
    prob += pulp.lpSum(x[j, i] for j in range(n)) == 1
    prob += pulp.lpSum(x[i, j] for j in range(n)) == 1
prob += pulp.lpSum(x[0, j] for j in range(1, n)) == 2
prob += pulp.lpSum(x[j, 0] for j in range(1, n)) == 2
Q = n
for i in range(1, n):
    for j in range(1, n):
        if i != j:
            prob += u[i] - u[j] + Q * x[i, j] <= Q - 1

# 6. 求解模型
prob.solve(pulp.PULP_CBC_CMD(msg=False))

# 求解耗時
solve_time = time.time() - start_time
best_distance = pulp.value(prob.objective)

# 7. 輸出結果
print(f"最佳總距離: {best_distance:.2f} 公里")
print(f"總耗時: {solve_time:.4f} 秒")

# 提取兩條路線
routes = []
for j in range(1, n):
    if pulp.value(x[0, j]) > 0.5:
        route = [0, j]
        current = j
        while True:
            for next_node in range(n):
                if pulp.value(x[current, next_node]) > 0.5:
                    route.append(next_node)
                    current = next_node
                    break
            if current == 0:
                break
        routes.append(route)

print("\n【車隊一 最佳路線】")
for idx in routes[0]:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")

print("\n【車隊二 最佳路線】")
for idx in routes[1]:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")


history_log = []
current_r1 = [0]
current_r2 = [0]

# Step 0: 還沒出發
history_log.append({
    "iteration": 0,
    "cost": 0.0,
    "route1": current_r1[:],
    "route2": current_r2[:]
})

# 找出比較長的那條路線長度，作為回放的總步數
max_steps = max(len(routes[0]), len(routes[1]))

for step in range(1, max_steps):
    # 如果車隊一還有下一站，就加進去
    if step < len(routes[0]):
        current_r1.append(routes[0][step])
    # 如果車隊二還有下一站，就加進去
    if step < len(routes[1]):
        current_r2.append(routes[1][step])
        
    # 計算當下走到一半的距離成本
    c1 = sum(dist[current_r1[k]][current_r1[k+1]] for k in range(len(current_r1)-1))
    c2 = sum(dist[current_r2[k]][current_r2[k+1]] for k in range(len(current_r2)-1))
    
    history_log.append({
        "iteration": step,
        "cost": round(c1 + c2, 2),
        "route1": current_r1[:],
        "route2": current_r2[:]
    })


start_dt = datetime.datetime(2026, 1, 1, 9, 0, 0)
speed_km_per_min = 45.0 / 60.0
stay_time = datetime.timedelta(minutes=30)

for r_idx, route in enumerate(routes):
    print(f"\n【車隊 {r_idx + 1} 時程表】")
    current_time = start_dt
    for i in range(len(route) - 1):
        curr_node = route[i]
        next_node = route[i+1]
        if i == 0:
            print(f"[{current_time.strftime('%H:%M')}] 從 {temples[curr_node]} 出發")
        else:
            leave_time = current_time + stay_time
            print(f"  預計 [{leave_time.strftime('%H:%M')}] 離開")
            current_time = leave_time 
            dist_km = df_dist.loc[temples[curr_node], temples[next_node]]
        travel_mins = dist_km / speed_km_per_min
        current_time += datetime.timedelta(minutes=travel_mins)
        print(f"  駛往 {temples[next_node]}  約 {dist_km:.2f} 公里 ({int(travel_mins)} 分鐘)")
        if i + 1 == len(route) - 1:
            print(f"[{current_time.strftime('%H:%M')}] 回到 {temples[next_node]} (行程結束)")
        else:
            print(f"[{current_time.strftime('%H:%M')}] 抵達 {temples[next_node]}", end="")


# 將運算結果儲存至 JSON
algo_name = "MILP" 

algo_result = {
    algo_name: {
        "distance": round(best_distance, 2),
        "time": round(solve_time, 4),
        "car1_count": len(routes[0]) - 2,
        "car2_count": len(routes[1]) - 2 if len(routes[1]) > 2 else 0,
        "route1": routes[0],
        "route2": routes[1] if len(routes[1]) > 2 else [],
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

print(f"\n\n【{algo_name}】的運算結果已成功寫入 {json_file}")
