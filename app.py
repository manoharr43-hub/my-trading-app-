def run_live_scan(stock_list):
    results = []
    # కనీసం 5 రోజుల డేటా తీసుకుంటేనే Average Volume సరిగ్గా వస్తుంది
    data = yf.download(stock_list, period="5d", interval="5m", group_by='ticker', progress=False)
    
    for s in stock_list:
        df = data[s] if len(stock_list) > 1 else data
        if not df.empty and len(df) > 10:
            ltp = round(df['Close'].iloc[-1], 2)
            
            # --- 1. Operator Entry Logic (Volume Based) ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1] # 20 క్యాండిల్స్ సగటు
            
            # ఒకవేళ వాల్యూమ్ సగటు కంటే 2.5 రెట్లు ఎక్కువ ఉంటే అది ఆపరేటర్ ఎంట్రీ
            is_operator = "⚠️ BIG MOVE" if curr_vol > (avg_vol * 2.5) else "Normal"
            
            # --- 2. Buy/Sell Logic ---
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res1 = round((2 * pivot) - low, 2)
            sup1 = round((2 * pivot) - high, 2)
            
            sig = "⏳ NEUTRAL"
            color = "#ffffff"
            if ltp > res1:
                sig = "🚀 BUY"
                color = "#d4edda" # Green
            elif ltp < sup1:
                sig = "🔻 SELL"
                color = "#f8d7da" # Red

            # --- 3. Results లో కాలమ్స్ యాడ్ చేయడం ---
            results.append({
                "Stock": s.replace(".NS",""),
                "LTP": ltp,
                "Operator Entry": is_operator, # ఇక్కడ కొత్త కాలమ్ యాడ్ చేశాం
                "Buy Above": res1,
                "Sell Below": sup1,
                "Signal": sig,
                "Volume": int(curr_vol),
                "Bg": color
            })
    
    if results:
        df_final = pd.DataFrame(results)
        # టేబుల్ లో కాలమ్స్ ఆర్డర్ మార్చడం
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
