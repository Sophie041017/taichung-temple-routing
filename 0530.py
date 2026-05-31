import sys
sys.stdout.reconfigure(encoding='utf-8')
import googlemaps
import pandas as pd
import numpy as np
import time
from io import StringIO

# 1. 填入你的 API Key 
API_KEY = 'AIzaSyAMigdYqS3sIQz5z8Gcl_nUhngwHHSGjOM' 
gmaps = googlemaps.Client(key=API_KEY)

# 2. 你的宮廟資料 (字串格式方便讀取)
data = """宮廟名稱,經度,緯度
南屯萬和宮,120.6392433,24.13799911
大甲鎮瀾宮,120.6243132,24.34533413
清水紫雲巖,120.5794621,24.27134078
梧棲浩天宮,120.5403748,24.2462171
豐原慈濟宮,120.7191873,24.25124775
龍井新庄永順宮,120.5759215,24.18286039
東勢東聖宮,120.829003,24.25181803
沙鹿玉皇殿,120.5606378,24.23645762
大肚瑞安宮,120.5737941,24.16312737
社口萬興宮,120.6836654,24.24551875
西屯福壽宮,120.6560832,24.16419225
南區醒修宮,120.6771312,24.13011993
北屯紫微宮,120.6667453,24.18265568
太平聖和宮,120.7506812,24.12647904
北區明德宮天聖堂,120.6690326,24.16450056
潭子潭水亭觀音廟,120.7076912,24.21042808
中區順天宮輔順將軍廟,120.6765799,24.14437118
大里杙福興宮,120.6776287,24.09821228"""

df = pd.read_csv(StringIO(data))
n = len(df)

# Google Maps API 吃 "緯度,經度" (Latitude, Longitude) 的格式
locations = [f"{row['緯度']},{row['經度']}" for _, row in df.iterrows()]
names = df['宮廟名稱'].tolist()

print("開始向 Google Maps API 請求距離資料...")
dist_matrix = np.zeros((n, n))

# 3. 發送 API 請求 (逐行發送避免超過 100 elements 的限制)
for i, origin in enumerate(locations):
    # 發送 API 請求，指定為開車模式 (driving)
    result = gmaps.distance_matrix(origins=origin, 
                                   destinations=locations, 
                                   mode="driving")
    
    # 提取距離 (單位: 公尺，轉為公里)
    elements = result['rows'][0]['elements']
    for j, element in enumerate(elements):
        if element['status'] == 'OK':
            dist_matrix[i][j] = element['distance']['value'] / 1000.0
        else:
            print(f"警告：無法取得 {names[i]} 到 {names[j]} 的距離")
            
    print(f"[{i+1}/{n}] 已完成 {names[i]} 的資料抓取")
    time.sleep(1) # 暫停 1 秒，避免 API 請求過於頻繁被擋

# 4. 強制對稱化矩陣 (因為 mTSP 模型通常需要 D_ij = D_ji)
# 現實中去程跟回程可能因為單行道有差，我們取平均值
symmetric_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if i == j:
            symmetric_matrix[i][j] = 0
        else:
            avg_dist = (dist_matrix[i][j] + dist_matrix[j][i]) / 2.0
            symmetric_matrix[i][j] = avg_dist

# 5. 輸出成 CSV 檔
dist_df = pd.DataFrame(symmetric_matrix, index=names, columns=names)
dist_df.to_csv('google_distance_matrix.csv')

print("\n太棒了！距離矩陣已成功抓取並對稱化，已儲存為 google_distance_matrix.csv。")
print("\n預覽前 3x3 矩陣 (單位: 公里):")
print(dist_df.iloc[:3, :3])