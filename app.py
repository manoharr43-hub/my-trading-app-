def analyze_intraday(df, ticker):
    try:
        d = df[ticker] if isinstance(df.columns, pd.MultiIndex) else df
        if d is None or len(d) < 30:
            return None

        # ✅ Only TODAY data filter
        d['Date'] = d.index.date
        today = d['Date'].iloc[-1]
        d = d[d['Date'] == today]

        if len(d) < 20:
            return None

        close = d['Close']
        high = d['High']
        low = d['Low']
        vol = d['Volume']

        ltp = close.iloc[-1]

        # ✅ Intraday VWAP
        d['VWAP'] = (close * vol).cumsum() / vol.cumsum()

        # Indicators
        d['RSI'] = rsi(close)
        d['EMA20'] = ema(close, 20)
        d['EMA50'] = ema(close, 50)

        # =========================
        # 🔥 Opening Range Breakout (ORB)
        # =========================
        opening_high = high.iloc[:6].max()   # first 30 min (5min candles)
        opening_low = low.iloc[:6].min()

        # =========================
        # 🔥 Volume Spike
        # =========================
        avg_vol = vol.rolling(20).mean().iloc[-1]
        vol_spike = vol.iloc[-1] > avg_vol * 1.5

        # =========================
        # 🔥 VWAP Trend
        # =========================
        vwap_trend_up = d['VWAP'].iloc[-1] > d['VWAP'].iloc[-5]
        vwap_trend_down = d['VWAP'].iloc[-1] < d['VWAP'].iloc[-5]

        signal = "WAIT"
        color = "#ffffff"
        entry = target = sl = 0

        # =========================
        # 🚀 STRONG BUY (Intraday)
        # =========================
        if (
            ltp > opening_high and
            ltp > d['VWAP'].iloc[-1] and
            d['RSI'].iloc[-1] > 55 and
            vol_spike and
            vwap_trend_up
        ):
            signal = "
