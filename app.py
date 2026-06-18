import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="NSE PRO INSTITUTIONAL SCANNER V11", page_icon="🚀", layout="wide")

# --------------------------------------------------
# DARK THEME CSS
# --------------------------------------------------
st.markdown("""
<style>
.stApp{background-color:#050816;color:white;}
h1,h2,h3,h4{color:white;}
[data-testid="stSidebar"]{background:#1d1f2b;}
.stButton>button{background:#0f62fe;color:white;border-radius:10px;height:50px;width:100%;font-weight:bold;}
.signal-box{background:#0f172a;padding:15px;border-radius:12px;border:1px solid #334155;}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🚀 NSE PRO INSTITUTIONAL SCANNER V11")
st.caption(f"Live Time : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

# --------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------
st.sidebar.header("⚙ Scanner Settings")

timeframe = st.sidebar.selectbox("Timeframe", ["5m","15m","30m","1h","1d"], index=4)
period = st.sidebar.selectbox("Period", ["5d","1mo","3mo","6mo"], index=1)
min_ai_score = st.sidebar.slider("Minimum AI Score", 0, 100, 10)
min_rvol = st.sidebar.slider("Minimum RVOL", 0.5, 5.0, 1.0, 0.1)

# --------------------------------------------------
# NSE SYMBOLS
# --------------------------------------------------
NSE_SYMBOLS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","LT.NS","ITC.NS",
    "AXISBANK.NS","KOTAKBANK.NS","BAJFINANCE.NS","ASIANPAINT.NS","SUNPHARMA.NS","MARUTI.NS",
    "TITAN.NS","ULTRACEMCO.NS","WIPRO.NS","NTPC.NS","POWERGRID.NS","TATAMOTORS.NS",
    "HINDUNILVR.NS","BHARTIARTL.NS","ADANIGREEN.NS","ADANIPORTS.NS","GRASIM.NS","JSWSTEEL.NS",
    "ONGC.NS","COALINDIA.NS","DIVISLAB.NS","DRREDDY.NS","M&M.NS","HEROMOTOCO.NS","BRITANNIA.NS"
]

# --------------------------------------------------
# INDICATOR FUNCTIONS
# --------------------------------------------------
def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def calculate_vwap(df):
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    vwap = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()
    return float(vwap.iloc[-1])

def calculate_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return float(atr.iloc[-1])

def calculate_rvol(df):
    current_volume = df["Volume"].iloc[-1]
    avg_volume = df["Volume"].rolling(20).mean().iloc[-1]
    if avg_volume == 0:
        return 0
    return float(current_volume / avg_volume)

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# --------------------------------------------------
# AI SCORE
# --------------------------------------------------
def calculate_ai_score(close, ema20, ema50, rsi, rvol, vwap, atr_pct):
    score = 0
    if close > ema20: score += 20
    if close > ema50: score += 20
    if rsi > 50: score += 15
    if rsi > 60: score += 10
    if rvol > 1.0: score += 15
    if rvol > 2: score += 10
    if close > vwap: score += 5
    if atr_pct > 2: score += 5
    return min(score, 100)

# --------------------------------------------------
# CHOCH & BOS Detection
# --------------------------------------------------
def detect_structure(df):
    highs = df["High"].rolling(5).max()
    lows = df["Low"].rolling(5).min()
    choch, bos = None, None

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
# SCAN SINGLE STOCK
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
        ema20 = float(ema(df["Close"], 20).iloc[-1])
        ema50 = float(ema(df["Close"], 50).iloc[-1])
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
                "Price": round(close, 2),
                "RSI": round(rsi, 2),
                "RVOL": round(rvol, 2),
                "ATR%": round(atr_pct, 2),
                "VWAP": round(vwap, 2),
                "AI Score": ai_score,
                "CHOCH": choch,
                "BOS": bos,
                "Signal": signal.strip()
            }
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None
    return None

# --------------------------------------------------
# MULTI THREAD SCANNER
# --------------------------------------------------
def run_scanner():
    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(scan_stock, symbol): symbol for symbol in NSE_SYMBOLS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return results

# --------------------------------------------------
# RUN SCANNER BUTTON
# --------------------------------------------------
st.markdown("---")
scan_button = st.button("🚀 RUN INSTITUTIONAL SCAN", use_container_width=True)

if scan_button:
    start_time = time.time()
    with st.spinner("Scanning NSE Stocks..."):
        results = run_scanner()
    end_time = time.time()
    scan_time = round(end_time - start_time, 2)

    if len(results) > 0:
        df_results = pd.DataFrame(results).sort_values(by="AI Score", ascending=False)
        c1, c2, c3 = st.columns(3)
        c1.metric("Signals Found", len(df_results))
        c2.metric("Top AI Score", int(df_results["AI Score"].max()))
        c3.metric("
