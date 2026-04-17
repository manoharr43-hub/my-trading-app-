# =============================
# BACKTEST PANEL (Selected Date Data)
# =============================
st.markdown("---")
st.subheader(f"📅 Backtest Report - {bt_date}")

# ✅ Sector select for Backtest
selected_bt_sector = st.sidebar.selectbox("📂 Select Sector for Backtest", list(all_sectors.keys()))
bt_stocks = all_sectors[selected_bt_sector]

if st.sidebar.button("📊 RUN BACKTEST"):

    bt_results = []
    breakout_bt_list = []
    target_list = [bt_stock_input] if bt_stock_input else bt_stocks   # ✅ FIXED

    with st.spinner("Running Backtest..."):
        for s in target_list:
            try:
                df_hist = yf.Ticker(s + ".NS").history(
                    start=bt_date,
                    end=bt_date + timedelta(days=1),
                    interval="15m"
                )
                df_hist = df_hist.between_time("09:15", "15:30")

                if not df_hist.empty:
                    # 🔍 Normal Backtest Signals
                    for i in range(5, len(df_hist)):
                        sub_df = df_hist.iloc[:i+1]
                        res = analyze_data(sub_df)
                        if res:
                            signal = res[1]
                            bt_results.append({
                                "Time": sub_df.index[-1].strftime('%H:%M'),
                                "Stock": s,
                                "Signal": signal,
                                "Big Player": res[2],
                                "Entry": res[3],
                                "SL": res[4],
                                "Target": res[5],
                                "Trend Score": res[6],
                                "Direction": get_direction(signal)
                            })

                    # 🔥 Breakout Logic (Backtest)
                    opening_data = df_hist.between_time("09:15", "09:30")
                    if not opening_data.empty:
                        opening_high = opening_data['High'].max()
                        opening_low = opening_data['Low'].min()

                        for i in range(1, len(df_hist)-3):
                            prev = df_hist.iloc[i-1]
                            curr = df_hist.iloc[i]
                            time = df_hist.index[i]
                            price = curr['Close']

                            if prev['Close'] <= opening_high and curr['Close'] > opening_high:
                                future = df_hist.iloc[i+1:i+4]
                                up = sum(future['Close'] > curr['Close'])
                                down = sum(future['Close'] <= curr['Close'])
                                signal_type = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"

                                breakout_bt_list.append({
                                    "Stock": s,
                                    "Price": round(price, 2),
                                    "Type": signal_type,
                                    "Time": time.strftime('%H:%M'),
                                    "Entry": round(price, 2),
                                    "Stoploss": round(price - (price * 0.01), 2),
                                    "Exit": round(price + (price * 0.02), 2)
                                })
                                break

                            elif prev['Close'] >= opening_low and curr['Close'] < opening_low:
                                future = df_hist.iloc[i+1:i+4]
                                down = sum(future['Close'] < curr['Close'])
                                up = sum(future['Close'] >= curr['Close'])
                                signal_type = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"

                                breakout_bt_list.append({
                                    "Stock": s,
                                    "Price": round(price, 2),
                                    "Type": signal_type,
                                    "Time": time.strftime('%H:%M'),
                                    "Entry": round(price, 2),
                                    "Stoploss": round(price + (price * 0.01), 2),
                                    "Exit": round(price - (price * 0.02), 2)
                                })
                                break
            except:
                continue

    # =============================
    # OUTPUT TABLES
    # =============================
    if bt_results:
        st.dataframe(pd.DataFrame(bt_results), use_container_width=True)
    else:
        st.warning("No Signals Found")

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT STOCKS (Backtest Direction Confirmed)")
    if breakout_bt_list:
        st.dataframe(pd.DataFrame(breakout_bt_list), use_container_width=True)
    else:
        st.info("No Breakout Stocks")
