def analyze_intraday(df, ticker):
    try:
        d = df[ticker].copy() if isinstance(df.columns, pd.MultiIndex) else df.copy()

        if d is None or len(d) < 50:
            return None

        # 👉 Today data
        d["Date"] = d.index.date
        today = d["Date"].iloc[-1]
        d = d[d["Date"] == today].copy()

        if len(d) < 30:
            return None

        close = d["Close"]
        high = d["High"]
        low = d["Low"]
        vol = d["Volume"]

        ltp = float(close.iloc[-1])

        # =============================
        # VWAP
        # =============================
        d["VWAP"] = (close * vol).cumsum() / vol.cumsum()

        # =============================
        # RSI (5 min)
        # =============================
        d["RSI"] = rsi(close)

        # =============================
        # ORB (rounded)
        # =============================
        orb_high = round(high.iloc[:6].max(), 2)
        orb_low = round(low.iloc[:6].min(), 2)

        # =============================
        # SUPPORT / RESISTANCE
        # =============================
        pivot = (high.iloc[-2] + low.iloc[-2] + close.iloc[-2]) / 3
        resistance = round((2 * pivot) - low.iloc[-2], 2)
        support = round((2 * pivot) - high.iloc[-2], 2)

        # =============================
        # 1 HOUR TREND (EMA)
        # =============================
        d["EMA20"] = ema(close, 20)
        d["EMA50"] = ema(close, 50)

        trend = "SIDEWAYS"
        if d["EMA20"].iloc[-1] > d["EMA50"].iloc[-1]:
            trend = "UPTREND"
        elif d["EMA20"].iloc[-1] < d["EMA50"].iloc[-1]:
            trend = "DOWNTREND"

        # =============================
        # 15 MIN RSI (approx)
        # =============================
        rsi_15 = round(rsi(close.rolling(3).mean()).iloc[-1], 1)

        # =============================
        # ADX (Trend Strength)
        # =============================
        tr = high - low
        atr = tr.rolling(14).mean()
        adx = round((atr / close).iloc[-1] * 100, 1)

        # =============================
        # VOLUME
        # =============================
        avg_vol = vol.rolling(20).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        # =============================
        # FINAL SIGNAL (STRONG)
        # =============================
        signal = "WAIT"
        color = "#ffffff"

        # 🔥 STRONG BUY
        if (
            ltp > resistance and
            ltp > d["VWAP"].iloc[-1] and
            trend == "UPTREND" and
            rsi_15 > 55 and
            adx > 1 and
            vol_spike
        ):
            signal = "STRONG BUY"
            color = "#00ff00"

        # 💀 STRONG SELL
        elif (
            ltp < support and
            ltp < d["VWAP"].iloc[-1] and
            trend == "DOWNTREND" and
            rsi_15 < 45 and
            adx >
