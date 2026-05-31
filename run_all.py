import sys
# ★ 加上這行防護罩，解決 Windows 終端機無法印出 Emoji 的報錯！
sys.stdout.reconfigure(encoding='utf-8') 
import subprocess
import time

# 這是你的 10 大演算法清單
scripts_to_run = [
    "0530_milp.py",
    "0530_heuristic.py",
    "0601_2opt.py",
    "0601_aco.py",
    "0601_alns.py",
    "0601_sa.py",
    "0601_savings.py",
    "0601_ga.py",
    "0601_ma.py",
    "0601_tabu.py",         
    "0601_dynamic_html.py"  # ⚠️ 對齊你實際命名的動態網頁生成器檔名
]

print("🚀 [系統啟動] 大台中宮廟排程：全自動化運算管線準備就緒！\n" + "="*50)
total_start_time = time.time()

for script in scripts_to_run:
    print(f"\n⏳ 正在啟動運算模組：{script} ...")
    try:
        # 呼叫 Python 執行該檔案
        subprocess.run([sys.executable, script], check=True)
        print(f"✅ {script} 執行完畢！")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [錯誤] 執行 {script} 時發生問題，管線已中止。")
        sys.exit(1) 
    except FileNotFoundError:
        print(f"\n❌ [找不到檔案] 請確認 {script} 是否在這個資料夾裡！")
        sys.exit(1)

total_time = time.time() - total_start_time
print("\n" + "="*50)
print(f"🎉 [管線執行成功] 10 大演算法大亂鬥已結束！總耗時: {total_time:.2f} 秒")
print("👉 最新鮮的【VRP_Live_Dashboard.html】已經生成，請直接在資料夾點擊打開吧！")