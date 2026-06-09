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
    best_r1, best_r2 = None, None
    
    for k in range(1, n - 1):
        r1 = [0] + state[:k] + [0]
        r2 = [0] + state[k:] + [0]
        
        c1 = sum(dist[r1[i]][r1[i+1]] for i in range(len(r1)-1))
        c2 = sum(dist[r2[i]][r2[i+1]] for i in range(len(r2)-1))
        
        if c1 + c2 < best_split_cost:
            best_split_cost = c1 + c2
            best_r1 = r1
            best_r2 = r2
            
    return best_split_cost, best_r1, best_r2


# 3. 模因核心 (Local Search)
def calc_dist_single(route):
    return sum(dist[route[k]][route[k+1]] for k in range(len(route)-1))

def two_opt_single(route):
    best_route = route[:]
    best_dist = calc_dist_single(best_route)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_route) - 2):
            for j in range(i + 2, len(best_route)):
                new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                new_dist = calc_dist_single(new_route)
                if new_dist < best_dist - 0.0001: 
                    best_route = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved: break
    return best_route

def memetic_education(state):
    _, r1, r2 = calc_total_dist(state)
    opt_r1 = two_opt_single(r1)
    opt_r2 = two_opt_single(r2)
    new_state = opt_r1[1:-1] + opt_r2[1:-1]
    cost, final_r1, final_r2 = calc_total_dist(new_state)
    return (cost, calc_dist_single(final_r1), calc_dist_single(final_r2), final_r1, final_r2), new_state


# 4. MA 參數設定
POP_SIZE = 50       
GENERATIONS = 100   
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

def selection_fast(eval_pop):
    competitors = random.sample(eval_pop, TOURNAMENT_SIZE)
    return min(competitors, key=lambda x: x[0][0])[1][:]

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


# 5. MA 演算法主迴圈
population = init_population()
eval_population = [memetic_education(ind) for ind in population]

best_overall_info = None
best_dist = float('inf')

history_log = []

for gen in range(GENERATIONS):
    new_population = []
    
    current_best_info, current_best_ind = min(eval_population, key=lambda x: x[0][0])
    new_population.append(current_best_ind[:])
    
    while len(new_population) < POP_SIZE:
        p1 = selection_fast(eval_population)
        p2 = selection_fast(eval_population)
        child = crossover(p1, p2)
        child = mutate(child)
        new_population.append(child)
        
    eval_population = [memetic_education(ind) for ind in new_population]
    
    current_best_info, current_best_ind = min(eval_population, key=lambda x: x[0][0])
    
    # 更新歷史紀錄
    if current_best_info[0] < best_dist:
        best_dist = current_best_info[0]
        best_overall_info = current_best_info
        
        _, _, _, h_route1, h_route2 = best_overall_info
        history_log.append({
            "iteration": gen + 1,  
            "cost": round(best_dist, 2),
            "route1": h_route1[:],
            "route2": h_route2[:]
        })


# 6. 輸出最終結果
_, best_dist_1, best_dist_2, best_route_1, best_route_2 = best_overall_info
solve_time = time.time() - start_time


print(f"總耗時: {solve_time:.6f} 秒 (繁衍 {GENERATIONS} 代，族群大小 {POP_SIZE})")
print(f"最佳總距離: {best_dist:.2f} 公里")

print("\n【MA - 車隊一 路線】")
for idx in best_route_1:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_1:.2f} 公里 | 負責 {len(best_route_1)-2} 間宮廟)")

print("\n【MA - 車隊二 路線】")
for idx in best_route_2:
    print(f"{temples[idx]} -> ", end="")
print("回到起點")
print(f"(行駛距離: {best_dist_2:.2f} 公里 | 負責 {len(best_route_2)-2} 間宮廟)")


# 將運算結果儲存至 JSON
algo_name = "MA"
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
    print(f"[{algo_name}] 這次距離 ({best_dist:.2f} km) 未打破歷史紀錄 ({old_best_dist:.2f} km)，保持原結果。")
