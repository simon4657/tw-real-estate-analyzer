import requests
import zipfile
import io
import pandas as pd
import os
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def load_real_estate_data_v2(season="114S1", city_code="a"):
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        target_filename = f"{city_code}_lvr_land_a.csv"
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if target_filename in z.namelist():
                with z.open(target_filename) as f:
                    df = pd.read_csv(f)
                    if df.empty: return pd.DataFrame()
                    df = df.iloc[1:].copy()
                    
                    cols = ['鄉鎮市區', '主要用途', '交易年月日', '總價元', '單價元平方公尺', '建物移轉總面積平方公尺']
                    available_cols = [c for c in cols if c in df.columns]
                    df = df[available_cols]
                    
                    if '主要用途' not in df.columns:
                        df['主要用途'] = '未標示'
                    else:
                        df['主要用途'] = df['主要用途'].fillna('未標示')
                    
                    if '總價元' in df.columns:
                        df['總價元'] = pd.to_numeric(df['總價元'], errors='coerce')
                    if '單價元平方公尺' in df.columns:
                        df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                        df['單價萬坪'] = (df['單價元平方公尺'] / 0.3025) / 10000
                        df = df.dropna(subset=['單價萬坪'])
                        df['單價萬坪'] = df['單價萬坪'].round(1)
                    else:
                        df['單價萬坪'] = pd.Series(dtype=float)
                        
                    if '建物移轉總面積平方公尺' in df.columns:
                        df['建物移轉總面積平方公尺'] = pd.to_numeric(df['建物移轉總面積平方公尺'], errors='coerce')
                        df['總坪數'] = (df['建物移轉總面積平方公尺'] * 0.3025).round(1)
                        
                    return df
            else:
                return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_rent_data_v2(season="114S1", city_code="a"):
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        target_filename = f"{city_code}_lvr_land_c.csv"
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if target_filename in z.namelist():
                with z.open(target_filename) as f:
                    df = pd.read_csv(f)
                    if df.empty: return pd.DataFrame()
                    df = df.iloc[1:].copy()
                    
                    # 租賃資料的面積欄位通常為「建物總面積平方公尺」
                    cols = ['鄉鎮市區', '主要用途', '租賃年月日', '總額元', '單價元平方公尺', '建物總面積平方公尺', '建物現況格局-房', '建物現況格局-廳']
                    available_cols = [c for c in cols if c in df.columns]
                    df = df[available_cols]
                    
                    if '主要用途' not in df.columns:
                        df['主要用途'] = '未標示'
                    else:
                        df['主要用途'] = df['主要用途'].fillna('未標示')
                    
                    if '總額元' in df.columns:
                        df['總額元'] = pd.to_numeric(df['總額元'], errors='coerce') 
                    if '單價元平方公尺' in df.columns:
                        df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                        df['租金單價坪'] = df['單價元平方公尺'] / 0.3025
                        df = df.dropna(subset=['租金單價坪'])
                        df['租金單價坪'] = df['租金單價坪'].round(0)
                    else:
                        df['租金單價坪'] = pd.Series(dtype=float)
                        
                    # 計算租賃坪數
                    if '建物總面積平方公尺' in df.columns:
                        df['建物總面積平方公尺'] = pd.to_numeric(df['建物總面積平方公尺'], errors='coerce')
                        df['租賃坪數'] = (df['建物總面積平方公尺'] * 0.3025).round(1)
                    else:
                        df['租賃坪數'] = pd.Series(dtype=float)
                        
                    return df
            else:
                return pd.DataFrame()
    except Exception as e:
        print("Error fetching rent data:", e)
        return pd.DataFrame()
