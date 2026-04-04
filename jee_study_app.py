def advanced_scan(stock_list):
    results = []
    status = st.empty()
    
    for s in stock_list:
        status.info(f"Analyzing {s}...")
        try:
            ticker = yf.Ticker(s)
            # 20 days data for Volume Analysis
            df = ticker.history(period="20d", interval="1d")
            
            if not df.empty and len(df) > 1:
                ltp = round(df['Close'].iloc[-1], 2)
                high = df['High'].iloc[-2]
                low = df['Low'].iloc[-2]
                close = df['Close'].iloc[-2]
                
                # --- Volume Analysis ---
                current_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].mean() # Previous 20 days average
                vol_confirmed = current_vol > avg_vol
                
                # --- Pivot Levels ---
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)   # Resistance (Buy Level)
                sup1 = round((2 * pivot) - high, 2)  # Support (Sell Level)
                
                # --- Advanced Signal & Fake Detection Logic ---
                signal = "⏳ NEUTRAL"
                breakout_status = "Waiting"
                color = "#eeeeee"
                
                if ltp > res1:
                    # Breakout condition
                    signal = "🚀 BUY"
                    color = "#d4edda"
                    if vol_confirmed:
                        breakout_status = "✅ REAL BREAKOUT"
                    else:
                        breakout_status = "⚠️ FAKE BREAKOUT (Low Vol)"
                        
                elif ltp < sup1:
                    # Breakdown condition
                    signal = "🔻 SELL"
                    color = "#f8d7da"
                    if vol_confirmed:
                        breakout_status = "✅ REAL BREAKDOWN"
                    else:
                        breakout_status = "⚠️ FAKE BREAKDOWN (Low Vol)"
                
                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Buy Above": f"{res1:.2f}",
                    "Sell Below": f"{sup1:.2f}",
                    "Current Signal": signal,
                    "Breakout Info": breakout_status,
                    "Bg": color
                })
        except: continue
    
    status.empty()
    # Display table (as already implemented in your code)
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
