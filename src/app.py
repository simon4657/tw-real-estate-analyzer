import streamlit as st
import pandas as pd
import plotly.express as px
from data_pipeline import load_real_estate_data_v2, load_rent_data_v2

st.set_page_config(page_title="包租代管 實價登錄分析系統", layout="wide")
st.title("🏢 包租代管 房價與租金投報分析系統")
st.markdown("專為包租代管業者設計，協助挖掘 **高投報率區域**、**高租賃需求地段**，以及評估 **最佳物件坪數配置**。")

st.sidebar.header("條件篩選")
city_mapping = {
    "台北市": "a", "新北市": "f", "桃園市": "h", "台中市": "b", 
    "台南市": "d", "高雄市": "e", "新竹市": "o", "新竹縣": "j",
    "彰化縣": "n", "嘉義市": "i", "嘉義縣": "q"
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
    df_buy_raw = load_real_estate_data_v2(season=season, city_code=city_code)
    df_rent_raw = load_rent_data_v2(season=season, city_code=city_code)

if df_buy_raw is None or df_buy_raw.empty:
    st.error(f"⚠️ 無法獲取 {season} 的資料。伺服器可能維護中或資料尚未發布。")
else:
    districts = ["全部"] + list(df_buy_raw['鄉鎮市區'].dropna().unique())
    selected_district = st.sidebar.selectbox("選擇鄉鎮市區 (區域過濾)", districts)
    
    # 買賣與租賃 主要用途篩選
    all_usages_buy = sorted(list(set(df_buy_raw['主要用途'].dropna().unique())))
    usage_options_buy = ["全部", "住家用", "商業用", "工業用"] + [u for u in all_usages_buy if u not in ["住家用", "商業用", "工業用", "全部"]]
    selected_usage_buy = st.sidebar.selectbox("買賣主要用途篩選", usage_options_buy)
    
    all_usages_rent = sorted(list(set(df_rent_raw['主要用途'].dropna().unique() if not df_rent_raw.empty else [])))
    usage_options_rent = ["全部", "住家用", "商業用", "工業用"] + [u for u in all_usages_rent if u not in ["住家用", "商業用", "工業用", "全部"]]
    selected_usage_rent = st.sidebar.selectbox("租賃主要用途篩選", usage_options_rent)
    
    # 建立過濾函數
    def apply_filters(df, is_rent=False):
        res = df.copy()
        if selected_district != "全部":
            res = res[res['鄉鎮市區'] == selected_district]
        usage = selected_usage_rent if is_rent else selected_usage_buy
        if usage != "全部":
            res = res[res['主要用途'].str.contains(usage, na=False)]
        return res

    df_buy = apply_filters(df_buy_raw, is_rent=False)
    df_rent = apply_filters(df_rent_raw, is_rent=True)

    # 建立頁籤
    tab1, tab2, tab3, tab_calc, tab4 = st.tabs([
        "📊 市場總覽與歷史趨勢", 
        "🎯 投資熱區雷達 (投報率)", 
        "📐 產品定位分析 (坪數)", 
        "💼 包租代管 實戰投報算盤", 
        "📄 原始資料明細"
    ])

    # ---------------- TAB 1: 市場總覽 ----------------
    with tab1:
        st.subheader("📊 當季市場概況")
        avg_price = df_buy['單價萬坪'].mean() if not df_buy.empty else 0
        total_buy_vol = len(df_buy)
        avg_rent = df_rent['租金單價坪'].mean() if not df_rent.empty else 0
        total_rent_vol = len(df_rent)
        
        yield_rate = (avg_rent * 12) / (avg_price * 10000) * 100 if avg_price > 0 and avg_rent > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("取得成本均價 (萬/坪)", f"{avg_price:.1f}" if avg_price > 0 else "無", f"買賣 {total_buy_vol} 筆")
        col2.metric("租金行情均價 (元/坪/月)", f"{avg_rent:.0f}" if avg_rent > 0 else "無", f"租賃 {total_rent_vol} 筆")
        col3.metric("本區平均 毛投報率", f"{yield_rate:.2f}%" if yield_rate > 0 else "無資料", "")
        col4.metric("最高租金單價 (元/坪)", f"{df_rent['租金單價坪'].max():.0f}" if not df_rent.empty else "無", "")

        st.markdown("---")
        with st.spinner("正在載入歷史趨勢資料..."):
            trend_dfs = []
            for s in reversed(all_seasons_list):
                t_buy = load_real_estate_data_v2(season=s, city_code=city_code)
                t_rent = load_rent_data_v2(season=s, city_code=city_code)
                
                if t_buy is not None and not t_buy.empty:
                    t_buy = apply_filters(t_buy, is_rent=False)
                    if not t_buy.empty:
                        avg_p = t_buy['單價萬坪'].mean()
                        trend_dfs.append({'季度': s, '指標': '買賣單價(萬/坪)', '數值': avg_p})
                        
                if t_rent is not None and not t_rent.empty:
                    t_rent = apply_filters(t_rent, is_rent=True)
                    if not t_rent.empty:
                        avg_r = t_rent['租金單價坪'].mean()
                        trend_dfs.append({'季度': s, '指標': '租金單價(元/坪)', '數值': avg_r})
                        
                        if t_buy is not None and not t_buy.empty and avg_p > 0:
                            y = (avg_r * 12) / (avg_p * 10000) * 100
                            trend_dfs.append({'季度': s, '指標': '毛投報率(%)', '數值': y})
                            
            if trend_dfs:
                history_df = pd.DataFrame(trend_dfs)
                
                st.subheader(f"📈 {city} {selected_district if selected_district != '全部' else '全市'} - 歷史推移分析")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    price_trend = history_df[history_df['指標'] == '買賣單價(萬/坪)']
                    if not price_trend.empty:
                        fig_p = px.line(price_trend, x='季度', y='數值', markers=True, title="取得成本走勢 (萬/坪)", text='數值')
                        fig_p.update_traces(texttemplate='%{text:.1f}', textposition="bottom right")
                        st.plotly_chart(fig_p, use_container_width=True)
                with c2:
                    rent_trend = history_df[history_df['指標'] == '租金單價(元/坪)']
                    if not rent_trend.empty:
                        fig_r = px.line(rent_trend, x='季度', y='數值', markers=True, title="租金行情走勢 (元/坪/月)", text='數值')
                        fig_r.update_traces(line_color='#2ca02c', texttemplate='%{text:.0f}', textposition="bottom right")
                        st.plotly_chart(fig_r, use_container_width=True)
                with c3:
                    yield_trend = history_df[history_df['指標'] == '毛投報率(%)']
                    if not yield_trend.empty:
                        fig_y = px.line(yield_trend, x='季度', y='數值', markers=True, title="毛投報率走勢 (%)", text='數值')
                        fig_y.update_traces(line_color='#d62728', texttemplate='%{text:.2f}', textposition="bottom right")
                        st.plotly_chart(fig_y, use_container_width=True)

    # ---------------- TAB 2: 投資熱區雷達 ----------------
    with tab2:
        st.subheader("🎯 尋找潛力利潤區塊 (跨區比較)")
        st.markdown("比較各行政區的 **買賣成本、租金收益與租賃熱度**，尋找「低房價、高租金、高需求」的藍海市場。")
        
        if df_buy_raw.empty or df_rent_raw.empty:
            st.warning("資料不足，無法進行跨區比較。")
        else:
            full_buy = df_buy_raw.copy()
            full_rent = df_rent_raw.copy()
            if selected_usage_buy != "全部": full_buy = full_buy[full_buy['主要用途'].str.contains(selected_usage_buy, na=False)]
            if selected_usage_rent != "全部": full_rent = full_rent[full_rent['主要用途'].str.contains(selected_usage_rent, na=False)]
            
            dist_buy = full_buy.groupby('鄉鎮市區').agg(買賣單價萬坪=('單價萬坪','mean'), 買賣交易量=('單價萬坪','count')).reset_index()
            dist_rent = full_rent.groupby('鄉鎮市區').agg(租金單價坪=('租金單價坪','mean'), 租賃交易量=('租金單價坪','count')).reset_index()
            
            merged_dist = pd.merge(dist_buy, dist_rent, on='鄉鎮市區', how='inner')
            merged_dist['毛投報率(%)'] = (merged_dist['租金單價坪'] * 12) / (merged_dist['買賣單價萬坪'] * 10000) * 100
            merged_dist = merged_dist.round(2)
            
            col_chartA, col_chartB = st.columns(2)
            with col_chartA:
                st.markdown("**🏆 各行政區 毛投報率排行榜**")
                merged_dist_sorted = merged_dist.sort_values(by='毛投報率(%)', ascending=False)
                fig_bar = px.bar(merged_dist_sorted, x='鄉鎮市區', y='毛投報率(%)', text_auto='.2f', color='毛投報率(%)', color_continuous_scale='Reds')
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col_chartB:
                st.markdown("**🌟 租金 vs 房價 價值發現矩陣**")
                st.info("💡 位於 **左上角** 的氣泡代表：房價取得成本低，但租金收益高。氣泡越大代表租屋需求越高！")
                fig_scatter = px.scatter(merged_dist, x='買賣單價萬坪', y='租金單價坪', size='租賃交易量', color='鄉鎮市區',
                                         hover_name='鄉鎮市區', size_max=40,
                                         labels={'買賣單價萬坪': "平均取得成本 (萬/坪)", '租金單價坪': "平均租金行情 (元/坪)"})
                fig_scatter.add_vline(x=merged_dist['買賣單價萬坪'].mean(), line_dash="dash", line_color="gray", opacity=0.5)
                fig_scatter.add_hline(y=merged_dist['租金單價坪'].mean(), line_dash="dash", line_color="gray", opacity=0.5)
                st.plotly_chart(fig_scatter, use_container_width=True)

    # ---------------- TAB 3: 產品定位分析 ----------------
    with tab3:
        st.subheader("📐 物件坪數配置與收益分析")
        st.markdown("分析不同坪數級距（如小套房、兩房、大坪數）的租金行情與投報表現，決定進場標的類型。")
        
        def categorize_ping(p):
            if pd.isna(p): return "未知"
            if p <= 15: return "1_套房 (≤15坪)"
            elif p <= 30: return "2_兩房 (15-30坪)"
            elif p <= 50: return "3_三房 (30-50坪)"
            else: return "4_大坪數 (>50坪)"
            
        df_buy_ping = df_buy.copy()
        df_rent_ping = df_rent.copy()
        
        if '總坪數' in df_buy_ping.columns and '租賃坪數' in df_rent_ping.columns:
            df_buy_ping['坪數級距'] = df_buy_ping['總坪數'].apply(categorize_ping)
            df_rent_ping['坪數級距'] = df_rent_ping['租賃坪數'].apply(categorize_ping)
            
            ping_buy_stat = df_buy_ping.groupby('坪數級距').agg(買賣均價=('單價萬坪','mean')).reset_index()
            ping_rent_stat = df_rent_ping.groupby('坪數級距').agg(租金均價=('租金單價坪','mean'), 租賃需求=('租金單價坪','count')).reset_index()
            
            ping_merged = pd.merge(ping_buy_stat, ping_rent_stat, on='坪數級距', how='inner')
            ping_merged = ping_merged[ping_merged['坪數級距'] != "未知"]
            ping_merged['毛投報率(%)'] = (ping_merged['租金均價'] * 12) / (ping_merged['買賣均價'] * 10000) * 100
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("**各坪數級距 - 租賃需求量**")
                fig_pie = px.pie(ping_merged, values='租賃需求', names='坪數級距', hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_p2:
                st.markdown("**各坪數級距 - 租金行情 (元/坪)**")
                fig_bar_rent = px.bar(ping_merged.sort_values('坪數級距'), x='坪數級距', y='租金均價', text_auto='.0f', color='租金均價', color_continuous_scale='Greens')
                st.plotly_chart(fig_bar_rent, use_container_width=True)
                
            st.markdown("**各坪數級距 - 估算毛投報率**")
            fig_bar_ping = px.bar(ping_merged.sort_values('坪數級距'), x='坪數級距', y='毛投報率(%)', text_auto='.2f', color='毛投報率(%)', color_continuous_scale='Blues')
            st.plotly_chart(fig_bar_ping, use_container_width=True)
        else:
            st.warning("資料缺乏坪數資訊，無法進行分析。")

    # ---------------- TAB CALC: 包租代管實戰投報算盤 ----------------
    with tab_calc:
        st.subheader("💼 第一層：低租金收房雷達 (Acquisition Radar)")
        st.markdown("比對潛在案源開價與區域標準均價，自動偵測「租金折價物件」。")
        
        # 使用目前條件（區、用途）計算基準均價
        base_rent_price = df_rent['租金單價坪'].mean() if not df_rent.empty else 0
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            target_ping = st.number_input("輸入潛在物件坪數 (坪)", value=25.0, min_value=1.0)
            target_rent = st.number_input("輸入屋主開出之每月總租金 (元)", value=30000, min_value=0, step=1000)
            
        with col_r2:
            st.info(f"📍 **當前市場基準：**\n\n根據實價登錄，{city} {selected_district if selected_district != '全部' else '全市'} ({selected_usage_rent}) 平均租金為 **{base_rent_price:.0f} 元/坪**。")
            if target_ping > 0 and target_rent > 0 and base_rent_price > 0:
                target_unit_rent = target_rent / target_ping
                discount_rate = ((base_rent_price - target_unit_rent) / base_rent_price) * 100
                st.metric("潛在案源 單價", f"{target_unit_rent:.0f} 元/坪")
                
                if discount_rate >= 15:
                    st.success(f"🔥 **強烈建議收房！** 此物件單價低於區域均價 **{discount_rate:.1f}%**。")
                elif discount_rate > 0:
                    st.warning(f"✅ **具備潛力：** 此物件低於區域均價 **{discount_rate:.1f}%**，可進一步談判。")
                else:
                    st.error(f"❌ **溢價物件：** 此物件高於區域均價 **{abs(discount_rate):.1f}%**，收房利潤空間極小。")
                    
        st.markdown("**🔍 目標特徵鎖定建議：** 優先尋找「長期無實價登錄租賃紀錄的空屋」或「無附屬設備的毛胚/簡裝屋」，這類屋主通常怕麻煩，容易談出 15%~20% 的折價空間。")

        st.markdown("---")
        st.subheader("🚀 第二層：高毛利利基市場溢價分析 (Niche Premium Calculator)")
        st.markdown("收房後，計算套用不同「利基型態」策略所能創造的極大化租金收益與價差。")
        
        niche_strategy = st.radio("選擇改裝與運營策略", ["寵物友善精裝 (+15% 溢價)", "高階商務/外商配置 (+25% 溢價)", "風格共生公寓/分租 (+30% 溢價)", "自訂溢價"])
        
        premium_pct = 0
        if "15%" in niche_strategy: premium_pct = 15
        elif "25%" in niche_strategy: premium_pct = 25
        elif "30%" in niche_strategy: premium_pct = 30
        else: premium_pct = st.number_input("自訂溢價幅度 (%)", value=20.0)
        
        expected_premium_rent = base_rent_price * (1 + premium_pct/100) * target_ping if base_rent_price > 0 else 0
        monthly_spread = expected_premium_rent - target_rent
        
        col_n1, col_n2, col_n3 = st.columns(3)
        col_n1.metric("利基市場 預估出租價", f"{expected_premium_rent:,.0f} 元/月")
        col_n2.metric("收房成本", f"{target_rent:,.0f} 元/月")
        col_n3.metric("💎 每月創造淨價差", f"{monthly_spread:,.0f} 元/月" if monthly_spread > 0 else "虧損", "利潤池成型")

        st.markdown("---")
        st.subheader("💰 第三層：現金回收期與真實 ROI 試算 (Financial Simulation)")
        st.markdown("賺價差是一回事，**「錢多久能回本」**才是擴張的關鍵！動態調整成本端參數來進行壓力測試。")

        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**成本端參數 (投入)**")
            capex = st.slider("預估前期總投入 (軟裝、油漆、家電、行銷) [萬元]", 0, 200, 30, step=1) * 10000
            deposit_months = st.slider("押金成本 (押給原屋主的月數)", 0, 3, 2)
            deposit_cost = deposit_months * target_rent
            contract_years = st.slider("包租合約期 (年)", 1, 10, 5)
            vacancy_days_per_year = st.slider("每年預估空窗期 (天)", 0, 60, 15)
            
        with cc2:
            st.markdown("**決策端輸出 (回報)**")
            if monthly_spread > 0:
                # 計算回收期 (不含押金，因為押金會退)
                months_to_breakeven = capex / monthly_spread
                st.metric("⏳ 資金回收期 (不含押金)", f"{months_to_breakeven:.1f} 個月")
                
                # 計算合約期內總淨利
                total_months = contract_years * 12
                vacancy_months_total = (vacancy_days_per_year / 30) * contract_years
                effective_rent_months = total_months - vacancy_months_total
                
                total_net_profit = (expected_premium_rent * effective_rent_months) - (target_rent * total_months) - capex
                st.metric("💵 合約期內總淨利", f"{total_net_profit:,.0f} 元")
                
                # 現金投資報酬率 Cash-on-Cash Return (年化)
                # 每年的平均淨現金流 / 前期總流出現金 (Capex + 押金)
                annual_cash_flow = total_net_profit / contract_years
                total_cash_out = capex + deposit_cost
                cash_on_cash_roi = (annual_cash_flow / total_cash_out) * 100 if total_cash_out > 0 else 0
                
                st.metric("📈 真實現金投資報酬率 (CoC ROI)", f"{cash_on_cash_roi:.1f} % / 年")
            else:
                st.error("每月淨價差為負，此專案不可行！請重新評估收房成本或提升溢價策略。")

    # ---------------- TAB 4: 原始資料明細 ----------------
    with tab4:
        st.subheader("📄 原始交易明細 (節錄前 50 筆)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**買賣交易**")
            if not df_buy.empty:
                cols_buy = ['鄉鎮市區', '主要用途', '交易年月日', '單價萬坪']
                if '總坪數' in df_buy.columns: cols_buy.append('總坪數')
                cols_buy.append('總價元')
                st.dataframe(df_buy[cols_buy].head(50), use_container_width=True)
            else:
                st.info("無資料")
        with c2:
            st.markdown("**租賃交易**")
            if not df_rent.empty:
                cols_rent = ['鄉鎮市區', '主要用途', '租賃年月日', '租金單價坪']
                if '租賃坪數' in df_rent.columns: cols_rent.append('租賃坪數')
                if '建物現況格局-房' in df_rent.columns: cols_rent.append('建物現況格局-房')
                cols_rent.append('總額元')
                cols_rent = [c for c in cols_rent if c in df_rent.columns]
                st.dataframe(df_rent[cols_rent].head(50), use_container_width=True)
            else:
                st.info("無資料")
