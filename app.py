def run_scanner(tickers):
    results = []
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()

    for s in tickers:
        try:
            df = data.copy() if len(tickers) == 1 else data[s].copy()
            df = df.dropna()
            if df.empty:
                continue   # <-- safe indentation
            analysis = analyze(df)
            if analysis:
                df, vol_ratio, ai_signal, acc = analysis
                trend = "UP" if ai_signal == "BUY" else "DOWN"
                results.append({
                    "Stock": s,
                    "Signal": ai_signal,
                    "Trend": trend,
                    "Vol Ratio": round(vol_ratio, 2),
                    "AI Acc": acc
                })
        except Exception as e:
            continue

    return pd.DataFrame(results)
