# -----------------------------
# TAB 1: LIVE SCANNER + EXCEL
# -----------------------------
with tab1:
    if st.button("RUN LIVE NSE 200 SCAN"):
        results = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None or df_raw.empty: continue
                
                df = add_indicators(df_raw.dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    signal = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: signal = "BUY PULLBACK 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: signal = "SELL PULLBACK 🔴"
                    
                    if signal != "None":
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": signal,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > l['VolAvg']*2.5 else "-",
                            "ENTRY": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in signal else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in signal else entry - (l['ATR']*3), 2)
                        })
            except: continue
        
        if results:
            df_live = pd.DataFrame(results)
            # ✅ Table replaced with DataFrame view
            st.dataframe(df_live, use_container_width=True)
            st.download_button(
                "📥 Download Live Scan Excel",
                data=to_excel(df_live),
                file_name=f"LiveScan_{now.strftime('%Y%m%d_%H%M')}.xlsx"
            )
        else:
            st.info("No pullback signals found in NSE 200 right now.")
