import requests
import zipfile
import io
import pandas as pd
import os
import streamlit as st

@st.cache_data(ttl=86400)
def fetch_and_clean_data(season="113S1", city_code="a"):
    """
    從內政部實價登錄下載特定季度的交易資料
    season: 如 113S1 代表 113年第1季
    city_code: a=台北市, f=新北市, h=桃園市, b=台中市, d=台南市, e=高雄市
    """
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 尋找對應的 CSV 檔案 (例如：a_lvr_land_a.csv 台北市買賣)
        target_filename = f"{city_code}_lvr_land_a.csv"
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if target_filename in z.namelist():
                with z.open(target_filename) as f:
                    df = pd.read_csv(f)
                    
                    # 移除第一行的英文標題
                    df = df.iloc[1:].copy()
                    
                    # 篩選主要欄位並轉換型別
                    cols = ['鄉鎮市區', '交易年月日', '總價元', '單價元平方公尺', '建物移轉總面積平方公尺']
                    df = df[[c for c in cols if c in df.columns]]
                    
                    # 數值轉換
                    df['總價元'] = pd.to_numeric(df['總價元'], errors='coerce')
                    df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                    
                    # 換算為「單價 (萬/坪)」 (1平方公尺 = 0.3025坪)
                    # 單價/坪 = 單價/平方公尺 / 0.3025
                    df['單價萬坪'] = (df['單價元平方公尺'] / 0.3025) / 10000
                    
                    # 清理無效資料
                    df = df.dropna(subset=['單價萬坪'])
                    df['單價萬坪'] = df['單價萬坪'].round(1)
                    
                    return df
            else:
                return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()
