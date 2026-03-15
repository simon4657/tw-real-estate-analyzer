import requests
import zipfile
import io
import pandas as pd
import os
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def load_real_estate_data(season="114S1", city_code="a"):
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        target_filename = f"{city_code}_lvr_land_a.csv" # a: 買賣
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if target_filename in z.namelist():
                with z.open(target_filename) as f:
                    df = pd.read_csv(f)
                    if df.empty: return pd.DataFrame()
                    df = df.iloc[1:].copy()
                    cols = ['鄉鎮市區', '交易年月日', '總價元', '單價元平方公尺', '建物移轉總面積平方公尺']
                    df = df[[c for c in cols if c in df.columns]]
                    df['總價元'] = pd.to_numeric(df['總價元'], errors='coerce')
                    df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                    df['單價萬坪'] = (df['單價元平方公尺'] / 0.3025) / 10000
                    df = df.dropna(subset=['單價萬坪'])
                    df['單價萬坪'] = df['單價萬坪'].round(1)
                    return df
            else:
                return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def load_rent_data(season="114S1", city_code="a"):
    url = f"https://plvr.land.moi.gov.tw/DownloadSeason?season={season}&type=zip&fileName=lvr_landcsv.zip"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        target_filename = f"{city_code}_lvr_land_c.csv" # c: 租賃
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            if target_filename in z.namelist():
                with z.open(target_filename) as f:
                    df = pd.read_csv(f)
                    if df.empty: return pd.DataFrame()
                    df = df.iloc[1:].copy()
                    cols = ['鄉鎮市區', '交易年月日', '總額元', '單價元平方公尺', '建物移轉總面積平方公尺']
                    df = df[[c for c in cols if c in df.columns]]
                    df['總額元'] = pd.to_numeric(df['總額元'], errors='coerce') # 月租金
                    df['單價元平方公尺'] = pd.to_numeric(df['單價元平方公尺'], errors='coerce')
                    # 租金單價: 元/坪
                    df['租金單價坪'] = df['單價元平方公尺'] / 0.3025
                    df = df.dropna(subset=['租金單價坪'])
                    df['租金單價坪'] = df['租金單價坪'].round(0)
                    return df
            else:
                return pd.DataFrame()
    except Exception:
        return pd.DataFrame()
