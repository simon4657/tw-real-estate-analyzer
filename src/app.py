import streamlit as st
import pandas as pd
import plotly.express as px
from data_pipeline import fetch_and_clean_data

st.set_page_config(page_title="台灣實價登錄分析系統", layout="wide")
st.title("📈 台灣實價登錄房價分析系統")
st.markdown("本系統自動抓取內政部實價登錄資料，並分析各地區之房價漲跌趨勢。")

st.sidebar.header("條件篩選")
city_mapping = {
    "台北市": "a",
    "新北市": "f",
    "桃園市": "h",
    "台中市": "b",
    "台南市": "d",
    "高雄市": "e"
}
city = st.sidebar.selectbox("選擇縣市", list(city_mapping.keys()))
season = st.sidebar.selectbox("資料季度", ["113S1", "112S4", "112S3"])

# 自動抓取並快取內政部最新一季資料
city_code = city_mapping[city]
with st.spinner(f"正在抓取 {city} {season} 的實價登錄資料..."):
    df = fetch_and_clean_data(season=season, city_code=city_code)

if df.empty:
    st.warning("⚠️ 無法獲取該季度的資料，請確認內政部伺服器狀態或選擇其他季度。")
else:
    # 根據選定的鄉鎮市區進行進階篩選
    districts = ["全部"] + list(df['鄉鎮市區'].dropna().unique())
    selected_district = st.sidebar.selectbox("選擇鄉鎮市區", districts)
    
    if selected_district != "全部":
        df = df[df['鄉鎮市區'] == selected_district]

    st.subheader("📊 趨勢分析指標")
    
    # 計算平均單價與交易量
    avg_price = df['單價萬坪'].mean()
    total_volume = len(df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("當前平均單價 (萬/坪)", f"{avg_price:.1f}" if pd.notna(avg_price) else "無資料", "季變動待計算")
    col2.metric("該季總交易筆數", f"{total_volume} 筆", "分析中...")
    col3.metric("最高單價 (萬/坪)", f"{df['單價萬坪'].max():.1f}" if not df.empty else "無", "")

    st.markdown("---")
    
    # 視覺化圖表
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("各行政區平均單價 (萬/坪)")
        if selected_district == "全部":
            district_avg = df.groupby('鄉鎮市區')['單價萬坪'].mean().reset_index()
            district_avg = district_avg.sort_values(by='單價萬坪', ascending=False)
            fig1 = px.bar(district_avg, x='鄉鎮市區', y='單價萬坪', text_auto='.1f', title=f"{city} 各區平均房價")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("已選擇單一行政區，不顯示跨區比較。")

    with col_chart2:
        st.subheader("單價分佈直方圖")
        fig2 = px.histogram(df, x="單價萬坪", nbins=50, title=f"{city} {selected_district} 房價分佈")
        fig2.update_layout(xaxis_title="單價 (萬/坪)", yaxis_title="交易筆數")
        st.plotly_chart(fig2, use_container_width=True)
        
    st.subheader("📄 最新交易明細 (節錄)")
    st.dataframe(df.head(20), use_container_width=True)
