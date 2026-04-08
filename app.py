def run_scanner(tickers):
    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="5d", interval="5m", progress=False, threads=False)

            if df.empty:
                continue

            # 🔥 VERY IMPORTANT FIX
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna()

            result = analyze_stock(df)
            if result is None:
                continue

            df, res, sup, vol_ratio, ai_view = result
            breakout = check_breakout(df)

            last = df.iloc[-1]

            # 🔥 FORCE FLOAT (FINAL FIX)
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            vwap = float(last['VWAP'])
            ema20 = float(last['EMA20'])
            ema50 = float(last['EMA50'])

            trend = "UPTREND" if ema20 > ema50 else "DOWNTREND"

            signal = "WAIT"

            if (ltp > vwap and trend == "UPTREND" and ai_view == "🚀 BULLISH"):
                signal = "BUY"

            elif (ltp < vwap and trend == "DOWNTREND" and ai_view == "📉 BEARISH"):
                signal = "SELL"

            if breakout == "🚀 BREAKOUT" and vol_ratio > 1.5:
                signal = "STRONG BUY"

            elif breakout == "📉 BREAKDOWN" and vol_ratio > 1.5:
                signal = "STRONG SELL"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "RSI": rsi,
                "Trend": trend,
                "Volume": round(vol_ratio,2),
                "AI": ai_view,
                "Breakout": breakout,
                "Signal": signal
            })

        except Exception as e:
            st.warning(f"{t} error: {e}")

    return pd.DataFrame(results)
