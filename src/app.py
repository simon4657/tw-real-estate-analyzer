import streamlit as st
import pandas as pd

st.set_page_config(page_title="台灣實價登錄分析系統", layout="wide")
st.title("📈 台灣實價登錄房價分析系統")
st.markdown("本系統自動抓取內政部實價登錄資料，並分析各地區之房價漲跌趨勢。")

st.sidebar.header("條件篩選")
city = st.sidebar.selectbox("選擇縣市", ["台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市"])
district = st.sidebar.text_input("輸入鄉鎮市區 (例如: 信義區)")

st.subheader("📊 趨勢分析指標")
col1, col2, col3 = st.columns(3)
col1.metric("當前平均單價 (萬/坪)", "待載入", "待載入")
col2.metric("年增率 (YoY)", "待載入", "待載入")
col3.metric("月增率 (MoM)", "待載入", "待載入")

st.info("資料自動抓取與視覺化圖表模組正在建置中...")
