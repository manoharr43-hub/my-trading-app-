# --------------------------------------------------
# CHOCH & BOS Detection
# --------------------------------------------------
def detect_structure(df):
    highs = df["High"].rolling(5).max()
    lows = df["Low"].rolling(5).min()

    choch = None
    bos = None

    # CHOCH: Change of Character
    if df["Close"].iloc[-1] > highs.iloc[-2] and df["Close"].iloc[-2] < lows.iloc[-3]:
        choch = "Bullish CHoCH"
    elif df["Close"].iloc[-1] < lows.iloc[-2] and df["Close"].iloc[-2] > highs.iloc[-3]:
        choch = "Bearish CHoCH"

    # BOS: Break of Structure
    if df["Close"].iloc[-1] > highs.iloc[-2]:
        bos = "Bullish BOS"
    elif df["Close"].iloc[-1] < lows.iloc[-2]:
        bos = "Bearish BOS"

    return choch, bos


# --------------------------------------------------
# Updated Scan with CHOCH + BOS
# --------------------------------------------------
def scan_stock(symbol):
    try:
        df = yf.download(symbol, period=period, interval=timeframe, progress=False, auto_adjust=True)
        if df.empty or len(df) < 50:
            return None

        close = float(df["Close"].iloc[-1])
        rsi = calculate_rsi(df)
        vwap = calculate_vwap(df)
        atr = calculate_atr(df)
        rvol = calculate_rvol(df)
        ema20 = float(ema(df["Close"],20).iloc[-1])
        ema50 = float(ema(df["Close"],50).iloc[-1])
        atr_pct = (atr / close) * 100

        ai_score = calculate_ai_score(close, ema20, ema50, rsi, rvol, vwap, atr_pct)

        choch, bos = detect_structure(df)

        if ai_score >= min_ai_score and rvol >= min_rvol:
            signal = "BUY"
            if rsi > 70:
                signal = "STRONG BUY"
            if choch or bos:
                signal = f"{signal} | {choch or ''} {bos or ''}"

            return {
                "Symbol": symbol,
                "Price": round(close,2),
                "RSI": round(rsi,2),
                "RVOL": round(rvol,2),
                "ATR%": round(atr_pct,2),
                "VWAP": round(vwap,2),
                "AI Score": ai_score,
                "CHOCH": choch,
                "BOS": bos,
                "Signal": signal.strip()
            }
    except:
        return None
    return None
