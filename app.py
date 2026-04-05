def run_live_scan(stock_list):
    results = []
    # RSI కోసం కనీసం 14 రోజుల డేటా అవసరం, అందుకే period="20d" తీసుకుంటున్నాం
    data = yf.download(stock_list, period="20d", interval="15m", group_by='ticker', threads=True, progress=False)
    
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 20: continue
            
            # --- Technical Calculations ---
            ltp = round(float(df['Close'].iloc[-1]), 1)
            
            # 1. Support & Resistance (Pivot)
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 1)
            sup = round((2 * pivot) - high, 1)

            # 2. Volume Analysis
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            high_vol = curr_vol > (avg_vol * 1.5)

            # 3. RSI Calculation (Simple 14 period)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1]))

            # --- SM Pro Signal Logic ---
            status = "⏳ Neutral"
            bg_color = "#ffffff" # White
            
            # Strong Buy Logic
            if ltp > res and high_vol and rsi > 60:
                status = "🔥 STRONG BUY"
                bg_color = "#28a745" # Dark Green
            elif ltp > res:
                status = "🚀 Buy Side"
                bg_color = "#d4edda" # Light Green
                
            # Strong Sell Logic
            elif ltp < sup and high_vol and rsi < 40:
                status = "💥 STRONG SELL"
                bg_color = "#dc3545" # Dark Red
            elif ltp < sup:
                status = "🔻 Sell Side"
                bg_color = "#f8d7da" # Light Red

            results.append({
                "Stock (LH)": s.replace(".NS",""),
                "LTP": ltp,
                "Support (Blue)": sup,
                "Resistance (Red)": res,
                "RSI": round(rsi, 1),
                "Signal (SM Pro)": status,
                "Bg": bg_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}; color: {'white' if 'STRONG' in str(df_final.loc[x.name, 'Signal (SM Pro)']) else 'black'}"] * len(x), axis=1)
            .set_properties(subset=['Support (Blue)'], **{'color': 'blue'})
            .set_properties(subset=['Resistance (Red)'], **{'color': 'red'})
        )
