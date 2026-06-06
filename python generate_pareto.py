import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import math
import json
import time

# 1. 讀取距離矩陣
df_dist = pd.read_csv('google_distance_matrix.csv', index_col=0)
dist = df_dist.values
n = len(df_dist.columns)

pareto_results = []
print("開始生成帕雷托前沿數據 (Pareto Frontier)... 這可能需要幾秒鐘")

# 2. 測試不同的「最大不平衡度」(兩車任務數的差值)
# 16間廟，差值可能是 0(8v8), 2(9v7), 4(10v6), 6, 8, 10, 12, 14(15v1)
for max_diff in range(0, 15, 2): 
    best_cost = float('inf')
    
    # 用 SA 快速尋優 10 次取最佳
    for _ in range(10):
        state = list(range(1, n))
        random.shuffle(state)
        
        def get_cost(s):
            min_c = float('inf')
            for k in range(1, n-1): # 確保兩車都有出發
                r1 = [0] + s[:k] + [0]
                r2 = [0] + s[k:] + [0]
                c1 = sum(dist[r1[i]][r1[i+1]] for i in range(len(r1)-1))
                c2 = sum(dist[r2[i]][r2[i+1]] for i in range(len(r2)-1))
                diff = abs((len(r1)-2) - (len(r2)-2))
                cost = c1 + c2
                
                # 核心：加入動態懲罰函數
                if diff > max_diff:
                    cost += 10000 
                if cost < min_c:
                    min_c = cost
            return min_c

        curr_cost = get_cost(state)
        T = 100.0
        while T > 0.1:
            for _ in range(20): # 內部探索
                i, j = random.sample(range(len(state)), 2)
                new_state = state[:]
                new_state[i], new_state[j] = new_state[j], new_state[i]
                nc = get_cost(new_state)
                
                if nc < curr_cost or random.random() < math.exp((curr_cost - nc) / T):
                    state = new_state
                    curr_cost = nc
                if curr_cost < best_cost:
                    best_cost = curr_cost
            T *= 0.95
            
    print(f"最大不平衡度限制 {max_diff} -> 最短距離: {best_cost:.2f} km")
    if best_cost < 10000:
        pareto_results.append({
            "任務差值上限": max_diff,
            "總行駛距離 (km)": round(best_cost, 2)
        })

# 3. 存檔給網頁讀取
with open('pareto_data.json', 'w', encoding='utf-8') as f:
    json.dump(pareto_results, f, ensure_ascii=False, indent=4)
print("\n🎉 生成完畢！已儲存至 pareto_data.json")