import sys
sys.stdout.reconfigure(encoding='utf-8') 
import subprocess
import time


scripts_to_run = [
    "MILP.py",
    "greedy.py",
    "2opt.py",
    "aco.py",
    "alns.py",
    "sa.py",
    "savings.py",
    "ga.py",
    "ma.py",
    "ts.py",         
]


total_start_time = time.time()

for script in scripts_to_run:
    try:
        # 呼叫 Python 執行該檔案
        subprocess.run([sys.executable, script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[錯誤] 執行 {script} 時發生問題，管線已中止。")
        sys.exit(1) 
    except FileNotFoundError:
        print(f"\n[找不到檔案] 請確認 {script} 是否在這個資料夾裡")
        sys.exit(1)

total_time = time.time() - total_start_time
