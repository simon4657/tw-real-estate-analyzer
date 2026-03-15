import streamlit as st
import pandas as pd
import plotly.express as px
from data_pipeline import load_real_estate_data, load_rent_data

st.set_page_config(page_title="台灣實價登錄分析系統", layout="wide")
st.title("📈 台灣實價登錄房價與租金分析系統")
st.markdown("自動抓取內政部實價登錄買賣與租賃資料，協助分析各區房價趨勢與潛力投資投報率。")

st.sidebar.header("條件篩選")
city_mapping = {
    "台北市": "a", "新北市": "f", "桃園市": "h",
    "台中市": "b", "台南市": "d", "高雄市": "e"
}
city = st.sidebar.selectbox("選擇縣市", list(city_mapping.keys()))

all_seasons_list = [
    "115S1", "114S4", "114S3", "114S2", "114S1",
    "113S4", "113S3", "113S2", "113S1", "112S4"
]
season = st.sidebar.selectbox("資料季度 (主要分析標的)", all_seasons_list)

if st.sidebar.button("清除資料快取"):
    st.cache_data.clear()
    st.success("快取已清除！")

city_code = city_mapping[city]
with st.spinner(f"正在抓取 {city} {season} 的實價登錄(買賣/租賃)資料..."):
    df = load_real_estate_data(season=season, city_code=city_code)
    rent_df = load_rent_data(season=season, city_code=city_code)

if df is None or df.empty:
    st.error(f"⚠️ 無法獲取 {season} 的買賣資料，可能內政部伺服器維護中。")
else:
    # 建立多重篩選
    districts = ["全部"] + list(df['鄉鎮市區'].dropna().unique())
    selected_district = st.sidebar.selectbox("選擇鄉鎮市區", districts)
    
    # 主要用途篩選 (過濾出買賣與租賃共有的主要用途，並加入關鍵字簡化選項)
    all_usages = sorted(list(set(df['主要用途'].dropna().unique()) | set(rent_df['主要用途'].dropna().unique())))
    # 我們可以將一些常見用途特別標出
    usage_options = ["全部", "住家用", "商業用", "工業用"] + [u for u in all_usages if u not in ["住家用", "商業用", "工業用", "全部"]]
    
    selected_usage = st.sidebar.selectbox("主要用途篩選", usage_options)
    
    # 執行篩選邏輯
    if selected_district != "全部":
        df = df[df['鄉鎮市區'] == selected_district]
        if not rent_df.empty:
            rent_df = rent_df[rent_df['鄉鎮市區'] == selected_district]
            
    if selected_usage != "全部":
        # 由於實價登錄文字有時含有「住家用」、「見其他登記事項」等模糊字眼，使用包含關鍵字搜尋
        df = df[df['主要用途'].str.contains(selected_usage, na=False)]
        if not rent_df.empty:
            rent_df = rent_df[rent_df['主要用途'].str.contains(selected_usage, na=False)]

    if df.empty:
        st.warning("⚠️ 在您選擇的條件下，該季度沒有任何買賣交易紀錄。")
    else:
        st.subheader("📊 當季趨勢與投資指標")
        
        avg_price = df['單價萬坪'].mean()
        total_volume = len(df)
        
        avg_rent = rent_df['租金單價坪'].mean() if not rent_df.empty else 0
        total_rent_volume = len(rent_df) if not rent_df.empty else 0
        yield_rate = (avg_rent * 12) / (avg_price * 10000) * 100 if avg_price > 0 and avg_rent > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("買賣均價 (萬/坪)", f"{avg_price:.1f}" if pd.notna(avg_price) else "無", f"{total_volume}筆")
        col2.metric("租金均價 (元/坪/月)", f"{avg_rent:.0f}" if avg_rent > 0 else "無", f"{total_rent_volume}筆")
        col3.metric("估算毛投報率", f"{yield_rate:.2f}%" if yield_rate > 0 else "無資料", "")
        col4.metric("最高買賣單價 (萬/坪)", f"{df['單價萬坪'].max():.1f}" if not df.empty else "無", "")

        st.markdown("---")
        
        # 歷史趨勢
        with st.spinner("正在載入歷史趨勢資料..."):
            trend_dfs = []
            rent_trend_dfs = []
            for s in reversed(all_seasons_list):
                temp_df = load_real_estate_data(season=s, city_code=city_code)
                temp_rent = load_rent_data(season=s, city_code=city_code)
                
                if temp_df is not None and not temp_df.empty:
                    if selected_district != "全部":
                        temp_df = temp_df[temp_df['鄉鎮市區'] == selected_district]
                    if selected_usage != "全部":
                        temp_df = temp_df[temp_df['主要用途'].str.contains(selected_usage, na=False)]
                        
                    if not temp_df.empty:
                        temp_df['季度'] = s
                        trend_dfs.append(temp_df)
                    
                if temp_rent is not None and not temp_rent.empty:
                    if selected_district != "全部":
                        temp_rent = temp_rent[temp_rent['鄉鎮市區'] == selected_district]
                    if selected_usage != "全部":
                        temp_rent = temp_rent[temp_rent['主要用途'].str.contains(selected_usage, na=False)]
                        
                    if not temp_rent.empty:
                        temp_rent['季度'] = s
                        rent_trend_dfs.append(temp_rent)
                    
            if trend_dfs:
                history_df = pd.concat(trend_dfs, ignore_index=True)
                trend_avg = history_df.groupby('季度')['單價萬坪'].mean().reset_index()
                
                st.subheader(f"📈 {city} {selected_district if selected_district != '全部' else '全市'} ({selected_usage}) - 歷史平均單價推移")
                fig_trend = px.line(trend_avg, x='季度', y='單價萬坪', markers=True, text='單價萬坪')
                fig_trend.update_traces(textposition="bottom right", texttemplate='%{text:.1f}')
                st.plotly_chart(fig_trend, use_container_width=True)
                
            if rent_trend_dfs:
                rent_history_df = pd.concat(rent_trend_dfs, ignore_index=True)
                rent_trend_avg = rent_history_df.groupby('季度')['租金單價坪'].mean().reset_index()
                
                st.subheader(f"📉 {city} {selected_district if selected_district != '全部' else '全市'} ({selected_usage}) - 歷史租金單價推移 (元/坪/月)")
                fig_rent_trend = px.line(rent_trend_avg, x='季度', y='租金單價坪', markers=True, text='租金單價坪')
                fig_rent_trend.update_traces(textposition="bottom right", texttemplate='%{text:.0f}')
                fig_rent_trend.update_traces(line_color='#2ca02c')
                st.plotly_chart(fig_rent_trend, use_container_width=True)

        st.markdown("---")
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("各行政區買賣均價 (萬/坪)")
            if selected_district == "全部":
                full_df = load_real_estate_data(season=season, city_code=city_code)
                if full_df is not None and not full_df.empty:
                    if selected_usage != "全部":
                        full_df = full_df[full_df['主要用途'].str.contains(selected_usage, na=False)]
                    if not full_df.empty:
                        district_avg = full_df.groupby('鄉鎮市區')['單價萬坪'].mean().reset_index()
                        district_avg = district_avg.sort_values(by='單價萬坪', ascending=False)
                        fig1 = px.bar(district_avg, x='鄉鎮市區', y='單價萬坪', text_auto='.1f')
                        st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("已選擇單一行政區，不顯示跨區比較。")

        with col_chart2:
            st.subheader("各行政區估算毛投報率 (%)")
            if selected_district == "全部" and not rent_df.empty:
                full_rent = load_rent_data(season=season, city_code=city_code)
                if not full_rent.empty:
                    if selected_usage != "全部":
                        full_rent = full_rent[full_rent['主要用途'].str.contains(selected_usage, na=False)]
                        
                    if not full_rent.empty and not full_df.empty:
                        dist_rent = full_rent.groupby('鄉鎮市區')['租金單價坪'].mean()
                        dist_price = full_df.groupby('鄉鎮市區')['單價萬坪'].mean()
                        
                        yield_data = []
                        for d in dist_price.index:
                            if d in dist_rent.index and pd.notna(dist_price[d]) and pd.notna(dist_rent[d]):
                                y = (dist_rent[d] * 12) / (dist_price[d] * 10000) * 100
                                yield_data.append({'鄉鎮市區': d, '投報率': y})
                                
                        if yield_data:
                            ydf = pd.DataFrame(yield_data).sort_values(by='投報率', ascending=False)
                            fig_yield = px.bar(ydf, x='鄉鎮市區', y='投報率', text_auto='.2f')
                            fig_yield.update_traces(marker_color='#d62728')
                            st.plotly_chart(fig_yield, use_container_width=True)
                        else:
                            st.warning("資料不足以計算各區投報率")
            else:
                st.info("已選擇單一行政區，不顯示跨區比較。")
                
        st.subheader(f"📄 最新買賣交易明細 ({selected_usage} 節錄)")
        st.dataframe(df.head(10), use_container_width=True)
        if not rent_df.empty:
            st.subheader(f"📄 最新租賃交易明細 ({selected_usage} 節錄)")
            st.dataframe(rent_df.head(10), use_container_width=True)
