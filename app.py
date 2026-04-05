def run_live_scan(stock_list):
    results = []
    # కనీసం 5 రోజుల డేటా తీసుకుంటేనే Average Volume/Pivot లెక్కలు బాగుంటాయి
    data = yf.download(stock_list, period="5d", interval="5m", group_by='ticker', progress=False)
    
    for s in stock_list:
        df = data[s] if len(stock_list) > 1 else data
        if not df.empty and len(df) > 10:
            ltp = round(df['Close'].iloc[-1], 2)
            
            # --- 1. Pivot Point & Levels Calculation ---
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            resistance = round((2 * pivot) - low, 2)  # దీన్నే Resist అంటాం
            support = round((2 * pivot) - high, 2)     # దీన్నే Support అంటాం
            
            # --- 2. Operator Entry (Volume Check) ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
            is_operator = "⚠️ BIG FISH" if curr_vol > (avg_vol * 2.5) else "Normal"
            
            # --- 3. Signal & Row Color Logic ---
            sig = "⏳ NEUTRAL"
            color = "#ffffff" # White
            if ltp > resistance:
                sig = "🚀 BUY"
                color = "#d4edda" # Light Green
            elif ltp < support:
                sig = "🔻 SELL"
                color = "#f8d7da" # Light Red

            # --- 4. Results Table Columns (మీరు అడిగిన మార్పులు ఇక్కడే ఉన్నాయి) ---
            results.append({
                "Stock": s.replace(".NS",""),
                "LTP": ltp,
                "Support": support,      # "Sell Below" బదులు "Support"
                "Resistance": resistance, # "Buy Above" బదులు "Resistance"
                "Operator": is_operator,
                "Signal": sig,
                "Bg": color
            })
    
    if results:
        df_final = pd.DataFrame(results)
        # Bg కాలమ్ ని తీసేసి స్టైలింగ్ అప్లై చేయడం
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"] * len(x), axis=1)
        )
