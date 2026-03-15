import requests
import zipfile
import io
import pandas as pd
import os
import streamlit as st

@st.cache_data(ttl=86400)
def fetch_and_clean_data(season="113S4", city_code="a"):
    """
    從內政部實價登錄下載特定季度的交易資料
    season: 如 113S4 代表 113年第4季
    city_code: a=台北市, f=新北市, h=桃園市, b=台中市, d=台南市, e=高雄市
    """
    # 內政部API歷年資料格式，fileName皆為lvr_landcsv.zip
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
            
        target_filename = f"{city_code}_lvr_land_a.csv"
        
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # 檢查目標檔案是否存在壓縮檔中
                if target_filename in z.namelist():
                    with z.open(target_filename) as f:
                        df = pd.read_csv(f)
                        
                        if df.empty:
                            return pd.DataFrame()
                        
                        # 第一列通常為英文欄位名，需要跳過
                        df = df.iloc[1:].copy()
                        
                        # 處理需要的欄位
                        cols = ['鄉鎮市區', '交易年月日', '總價元', '單價元平方公尺', '建物移轉總面積平方公尺']
                        df = df[[c for c in cols if c in df.columns]]
                        
                        df['總價元'] = pd.to_numeric(df['總價元'], errors='coerce')
                        df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                        
                        # 換算為「單價 (萬/坪)」 (1平方公尺 = 0.3025坪)
                        df['單價萬坪'] = (df['單價元平方公尺'] / 0.3025) / 10000
                        
                        # 清理空值
                        df = df.dropna(subset=['單價萬坪'])
                        df['單價萬坪'] = df['單價萬坪'].round(1)
                        
                        return df
                else:
                    return pd.DataFrame()
        except zipfile.BadZipFile:
            print(f"Error: 伺服器回傳的不是有效的ZIP檔。可能該季度資料尚未釋出或發生錯誤。")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()
