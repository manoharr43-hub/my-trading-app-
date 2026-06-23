import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 1️⃣ PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="NSE AI PRO V11.12", layout="wide", page_icon="🚀")
st.title("🚀 NSE AI PRO V11.12 – Institutional Hybrid Scanner")
st.markdown("**AI Momentum | VWAP Bounce | RVOL System | CISD Signals | Supertrend Analytics**")
st.markdown("---")

# ==========================================
# 2️⃣ SIDEBAR SETTINGS
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings & Controls")
    auto_refresh = st.checkbox("🔄 Auto Refresh (Every 3 Mins)")
    interval = st.selectbox("Interval", ["5m","15m","30m","1h","1d"], index=1)
    period = st.selectbox("Period", ["5d","1mo","3mo","6mo","1y"], index=2)
    sector_stocks = {
        "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
        "IT": ["TCS","INFY","WIPRO","HCLTECH","TECHM"],
        "Pharma": ["SUNPHARMA","CIPLA","DIVISLAB","DRREDDY"],
        "Energy": ["RELIANCE","ONGC","BPCL","NTPC"],
        "Auto": ["TATAMOTORS","M&M","EICHERMOT","HEROMOTOCO"],
        "FMCG": ["ITC","HINDUNILVR","BRITANNIA","DABUR"]
    }
    sector = st.selectbox("Sector", ["All NSE500"] + list(sector_stocks.keys()))
    run_button = st.button("🚀 RUN SCANNER", type="primary", use_container_width=True)

# ==========================================
# 3️⃣ CORE FUNCTIONS
# ==========================================
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        import requests
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(io.StringIO(requests.get(url, headers=headers, timeout=5).text))
        return sorted(df["Symbol"].dropna().unique().tolist())
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","TATAMOTORS"]

stocks = load_nse500()

@st.cache_data(ttl=120)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS" if "^" not in symbol else symbol, interval=interval, period=period, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

def predict_trend_ai(prices):
    if len(prices) < 20: return "Neutral", 0
    y = prices[-20:].values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    corr = np.corrcoef(x, y)[0,1]
    conf = min(round(abs(corr)*100,2),99)
    if slope > 0 and conf > 50: return "UP 🚀", conf
    elif slope < 0 and conf > 50: return "DOWN 🔻", conf
    else: return "SIDEWAYS ➖", conf

def calculate_supertrend(df, period=10, multiplier=3):
    high, low, close = df['High'], df['Low'], df['Close']
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    atr = tr.rolling(window=period).mean()
    hl2 = (high + low) / 2
    upperband, lowerband = hl2 + (multiplier * atr), hl2 - (multiplier * atr)
    supertrend, direction = np.zeros(len(df)), np.zeros(len(df))
    for i in range(1, len(df)):
        if close.iloc[i] > upperband.iloc[i-1]: direction[i] = 1
        elif close.iloc[i] < lowerband.iloc[i-1]: direction[i] = -1
        else: direction[i] = direction[i-1]
        supertrend[i] = lowerband.iloc[i] if direction[i]==1 else upperband.iloc[i]
    df['Supertrend'], df['ST_Direction'] = supertrend, direction
    return df

def add_indicators(df, interval):
    if len(df) < 60: return df
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    delta = df["Close"].diff()
    df["RSI"] = 100 - (100 / (1 + (delta.clip(lower=0).ewm(com=13).mean() / -delta.clip(upper=0).ewm(com=13).mean())))
    df["MACD_Line"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["Signal_Line"] = df["MACD_Line"].ewm(span=9).mean()
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    if 'd' not in interval and 'wk' not in interval and 'mo' not in interval:
        df['Date'] = df.index.date
        df['VWAP'] = (df['Volume'] * tp).groupby(df['Date']).cumsum() / df['Volume'].groupby(df['Date']).cumsum()
    else:
        df['VWAP'] = (df['Volume'] * tp).rolling(20).sum() / df['Volume'].rolling(20).sum()
    df = calculate_supertrend(df)
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    return df

# ==========================================
# 4️⃣ PROCESSOR THREAD
# ==========================================
def process_stock(symbol, interval, period):
    df = get_data(symbol, interval, period)
    if df.empty or len(df) < 60: return None
    df = add_indicators(df, interval)
    close = float(df["Close"].iloc[-1])
    ai_trend, ai_conf = predict_trend_ai(df["Close"])
    macd_val = "BULLISH" if df["MACD_Line"].iloc[-1] > df["Signal_Line"].iloc[-1] else "BEARISH"
    st_dir = "UP" if df["ST_Direction"].iloc[-1] == 1 else "DOWN"
    vwap_sig = "ABOVE" if close > float(df["VWAP"].iloc[-1]) else "BELOW"
    score = sum([
        1 if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1] else -1,
        1 if macd_val=="BULLISH" else -1,
        1 if st_dir=="UP" else -1,
        1 if vwap_sig=="ABOVE" else -1
    ])
    signal = "STRONG BUY" if score>=3 else "BUY" if score>=1 else "SELL" if score<=-1 else "WAIT"
    return [symbol, round(close,2), ai_trend, f"{ai_conf}%", macd_val, st_dir, vwap_sig, score, signal]

# ==========================================
# 5️⃣ EXECUTION & DISPLAY
# ==========================================
tab1, tab2 = st.tabs(["🚀 V11.12 Dashboard", "🔍 Custom Search"])
with tab1:
    if run_button or auto_refresh:
        selected_stocks = stocks if sector=="All NSE500" else sector_stocks[sector]
        progress = st.progress(0)
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_stock, s, interval, period): s for s in selected_stocks}
            for i, f in enumerate(as_completed(futures)):
                res = f.result()
                if res: results.append(res)
                progress.progress((i+1)/len(selected_stocks))
        if results:
            df_res = pd.DataFrame(results, columns=["Stock","LTP","AI Trend","Conf %","MACD","Supertrend","VWAP","Score","Signal"])
            df_res = df_res.sort_values(by="Score", ascending=False)
            st.dataframe(df
