import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==========================================
# 0. 設定支援繁體中文的字型 (Windows 預設使用微軟正黑體)
# ==========================================
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 建立實驗數據資料庫 (依照總距離由短到長排序)
# ==========================================
data = {
    '演算法': ['ALNS', 'MILP', 'MA', 'ACO', 'Savings', 'TS', '2-Opt', 'SA', 'GA', 'Greedy'],
    '總距離 (km)': [137.36, 143.13, 143.13, 144.74, 144.87, 146.07, 156.44, 163.89, 167.03, 199.69],
    '運算時間 (s)': [1.01, 1.58, 3.17, 0.57, 0.001, 3.55, 0.003, 0.89, 4.80, 0.001],
    '車隊一 (間)': [17, 13, 13, 13, 13, 11, 15, 10, 6, 15],
    '車隊二 (間)': [0, 4, 4, 4, 4, 6, 2, 7, 11, 2]
}
df = pd.DataFrame(data)

# 設定統一的視覺風格
sns.set_theme(style="whitegrid", font="Microsoft JhengHei")

# ==========================================
# 圖表一：最佳總距離比較 (Bar Chart)
# ==========================================
plt.figure(figsize=(12, 6))
# 凸顯前三名 (ALNS, MILP, MA) 的顏色
colors = ['#e74c3c' if x <= 143.13 else '#3498db' for x in df['總距離 (km)']]

ax = sns.barplot(x='演算法', y='總距離 (km)', data=df, palette=colors)
plt.title('各演算法最佳總距離比較 (無平衡限制)', fontsize=18, fontweight='bold', pad=15)
plt.xlabel('演算法名稱', fontsize=14)
plt.ylabel('總行駛距離 (公里)', fontsize=14)
plt.ylim(120, 210) # 縮小 Y 軸範圍讓差異更明顯

# 在長條圖上標示數值
for p in ax.patches:
    ax.annotate(f'{p.get_height():.2f}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='black', xytext=(0, 5), 
                textcoords='offset points')

plt.tight_layout()
plt.savefig('Chart_1_Distance.png', dpi=300)
print("✅ 已生成: Chart_1_Distance.png (總距離比較圖)")

# ==========================================
# 圖表二：運算時間與距離的權衡 (Scatter Plot)
# ==========================================
plt.figure(figsize=(10, 6))

sns.scatterplot(x='運算時間 (s)', y='總距離 (km)', data=df, s=200, color='#9b59b6', edgecolor='black', zorder=5)
plt.title('運算時間 vs 總距離 權衡分析 (Trade-off)', fontsize=18, fontweight='bold', pad=15)
plt.xlabel('運算耗時 (秒)', fontsize=14)
plt.ylabel('總行駛距離 (公里)', fontsize=14)

# 標上每個點的演算法名稱
for i in range(df.shape[0]):
    plt.text(df['運算時間 (s)'][i] + 0.08, df['總距離 (km)'][i] + 0.5, 
             df['演算法'][i], fontsize=11, fontweight='bold')

# 畫出「理想區域 (又快又短)」的綠色虛線框
plt.axvspan(-0.2, 1.8, ymin=0, ymax=0.35, color='green', alpha=0.1)
plt.text(0.8, 139, '最佳甜蜜點\n(快且距離短)', color='green', fontsize=12, fontweight='bold', ha='center')

plt.tight_layout()
plt.savefig('Chart_2_Tradeoff.png', dpi=300)
print("✅ 已生成: Chart_2_Tradeoff.png (時間與距離權衡圖)")

# ==========================================
# 圖表三：勞逸平衡分析 - 工作量分配 (Stacked Bar Chart)
# ==========================================
plt.figure(figsize=(12, 6))

x = np.arange(len(df['演算法']))
width = 0.6

# 畫出堆疊長條圖
p1 = plt.bar(x, df['車隊一 (間)'], width, label='車隊一 (間)', color='#f39c12', edgecolor='white')
p2 = plt.bar(x, df['車隊二 (間)'], width, bottom=df['車隊一 (間)'], label='車隊二 (間)', color='#2c3e50', edgecolor='white')

plt.title('各演算法排班工作量分配 (血汗指數分析)', fontsize=18, fontweight='bold', pad=15)
plt.xlabel('演算法名稱', fontsize=14)
plt.ylabel('負責宮廟數量 (間)', fontsize=14)
plt.xticks(x, df['演算法'], fontsize=12)
plt.ylim(0, 20)

# 畫一條 8.5 的虛線代表「完美平均」
plt.axhline(y=8.5, color='red', linestyle='--', linewidth=2, label='完美平均線 (8.5間)')

plt.legend(loc='upper right', fontsize=12)

# 在色塊中間標示數量
for r1, r2 in zip(p1, p2):
    h1 = r1.get_height()
    h2 = r2.get_height()
    if h1 > 0:
        plt.text(r1.get_x() + r1.get_width() / 2., h1 / 2., f'{int(h1)}', ha='center', va='center', color='white', fontweight='bold', fontsize=12)
    if h2 > 0:
        plt.text(r2.get_x() + r2.get_width() / 2., h1 + h2 / 2., f'{int(h2)}', ha='center', va='center', color='white', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig('Chart_3_Workload.png', dpi=300)
print("✅ 已生成: Chart_3_Workload.png (工作量分配堆疊圖)")