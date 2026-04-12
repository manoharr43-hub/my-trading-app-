def get_intraday_movers(all_sectors):
    movers = []
    for tickers in all_sectors.values():
        for stock in tickers:
            try:
                df = yf.download(stock, period="1d", interval="15m", progress=False)
                if df is None or df.empty or len(df) < 2:
                    continue
                pct = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                movers.append({
                    "Stock": stock.replace(".NS",""),
                    "Change %": float(round(pct,2))
                })
            except Exception:
                continue
    
    # ✅ Safe check before sorting
    if not movers:
        return pd.DataFrame(columns=["Stock","Change %"])
    
    df_movers = pd.DataFrame(movers)
    
    # ✅ Ensure column exists and is numeric
    if "Change %" not in df_movers.columns:
        return df_movers
    
    df_movers["Change %"] = pd.to_numeric(df_movers["Change %"], errors="coerce")
    df_movers = df_movers.dropna(subset=["Change %"])
    
    if df_movers.empty:
        return pd.DataFrame(columns=["Stock","Change %"])
    
    return df_movers.sort_values(by="Change %", ascending=False).head(10)
