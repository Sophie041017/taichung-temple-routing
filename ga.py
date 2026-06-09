import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import random
import time
import json
import os

random.seed(42)

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
            
    # 回傳：(總距離, 車一距離, 車二距離, 車一路線, 車二路線)
    return best_split_cost, best_dist1, best_dist2, best_route1, best_route2

# 3. GA 參數設定
POP_SIZE = 100
GENERATIONS = 500
MUTATION_RATE = 0.1
TOURNAMENT_SIZE = 5

def init_population():
    pop = []
    base = list(range(1, n))
    for _ in range(POP_SIZE):
        ind = base[:]
        random.shuffle(ind)
        pop.append(ind)
    return pop

def crossover(parent1, parent2):
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child = [-1] * size
    child[start:end+1] = parent1[start:end+1]
    
    p2_idx = 0
    for i in range(size):
        if child[i] == -1:
            while parent2[p2_idx] in child:
                p2_idx += 1
            child[i] = parent2[p2_idx]
    return child

def mutate(individual):
    if random.random() < MUTATION_RATE:
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
    return individual

start_time = time.time()

# 4. GA 演算法主迴圈
population = init_population()
best_overall_info = None
best_dist = float('inf')

history_log = []

eval_population = [(calc_total_dist(ind), ind) for ind in population]

def selection_fast(eval_pop):
    competitors = random.sample(eval_pop, TOURNAMENT_SIZE)
    best_comp = min(competitors, key=lambda x: x[0][0]) 
    return best_comp[1][:]

for gen in range(GENERATIONS):
    new_population = []
    
    # 尋找當代最強 (菁英保留)
    current_best_info, current_best_ind = min(eval_population, key=lambda x: x[0][0])
    new_population.append(current_best_ind[:])
    
    # 產生剩餘的子代
    while len(new_population) < POP_SIZE:
        p1 = selection_fast(eval_population)
        p2 = selection_fast(eval_population)
        child = crossover(p1, p2)
        child = mutate(child)
        new_population.append(child)
        
    population = new_population
    eval_population = [(calc_total_dist(ind), ind) for ind in population]
    
    # 更新歷史最佳紀錄
    current_best_info, current_best_ind = min(eval_population, key=lambda x: x[0][0])
    
    if current_best_info[0] < best_dist:
        best_dist = current_best_info[0]
        best_overall_info = current_best_info
        
        _, _, _, h_route1, h_route2 = best_overall_info
        history_log.append({
            "iteration": gen + 1,  # 記錄這是在第幾代演化出來的
            "cost": round(best_dist, 2),
            "route1": h_route1[:],
            "route2": h_route2[:]
        })

# 5. 輸出最終結果
_, best_dist_1, best_dist_2, best_route_1, best_route_2 = best_overall_info
solve_time = time.time() - start_time

print(f"總耗時: {solve_time:.6f} 秒 (繁衍 {GENERATIONS} 代)")
print(f"最佳總距離: {best_dist:.2f} 公里")

print("\n【GA - 車隊一 路線】")
for idx in best_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_1:.2f} 公里 | 負責 {len(best_route_1)-2} 間宮廟)")

print("\n【GA - 車隊二 路線】")
for idx in best_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_2:.2f} 公里 | 負責 {len(best_route_2)-2} 間宮廟)")


# 6. 存檔邏輯
algo_name = "GA"
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

if best_dist <= old_best_dist:
    print(f"\n[{algo_name}] 最佳里程紀錄為 {best_dist:.2f} km")
    
    all_results[algo_name] = {
        "distance": round(best_dist, 2),
        "time": round(solve_time, 4),
        "car1_count": len(best_route_1) - 2,
        "car2_count": len(best_route_2) - 2 if len(best_route_2) > 2 else 0,
        "route1": best_route_1,
        "route2": best_route_2 if len(best_route_2) > 2 else [],
        "history": history_log 
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
        
else:
    print(f"\n[{algo_name}] 這次距離 ({best_dist:.2f} km) 未打破歷史紀錄 ({old_best_dist:.2f} km)，保持原結果。")
