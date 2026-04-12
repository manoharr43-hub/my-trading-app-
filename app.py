import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="⚡ NSE Intraday AI Scanner (Final Safe)", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"],  # removed TATAMOTORS.NS
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS"]
}

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_intraday(df):
    if df is None or len(df) < 30:
        return None
    df = df.copy()
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df.dropna(inplace=True)
    if len(df) < 20:
        return None
    features = ['EMA9','EMA21','RSI','VWAP']
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    X = df[features]
    y = df['Target']
    model = RandomForestClassifier(n_estimators=80, max_depth=5)
    model.fit(X[:-1], y[:-1])
    pred = model.predict(X.iloc[[-1]])[0]
    ai_signal = "BUY" if pred == 1 else "SELL"
    avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 1
    return df.iloc[-1], ai_signal, vol_ratio

# =============================
# RUN SCANNER
# =============================
def run_intraday_scanner(tickers):
    results = []
    for stock in tickers:
        try:
            df = yf.download(stock, period="1d", interval="5m", progress=False)
            if df.empty:
                continue
            res = analyze_intraday(df)
            if res is None:
                continue
            last, ai, vol = res
            ltp = last['Close']
            ema9 = last['EMA9']
            ema21 = last['EMA21']
            rsi = last['RSI']
            vwap = last['VWAP']
            trend = "UP" if ema9 > ema21 else "DOWN"
            signal = "WAIT"
            if ltp > vwap and trend == "UP" and rsi > 55 and ai == "BUY":
                signal = "BUY"
                if vol > 2:
                    signal = "🔥 BIG BUYER"
            elif ltp < vwap and trend == "DOWN" and rsi < 45 and ai == "SELL":
                signal = "SELL"
                if vol > 2:
                    signal = "🔥 BIG SELLER"
            results.append({
                "Stock": stock.replace(".NS",""),
                "Price": round(ltp,2),
                "Trend": trend,
                "RSI": round(rsi,1),
                "Volume Spike": round(vol,2),
                "AI": ai,
                "Signal": signal
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# =============================
# TOP INTRADAY MOVERS (SAFE)
# =============================
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
    if not movers:
        return pd.DataFrame(columns=["Stock","Change %"])
    df_movers = pd.DataFrame(movers)
    df_movers["Change %"] = pd.to_numeric(df_movers["Change %"], errors="coerce")
    df_movers = df_movers.dropna(subset=["Change %"])
    if df_movers.empty:
        return pd.DataFrame(columns=["Stock","Change %"])
    return df_movers.sort_values(by="Change %", ascending=False).head(10)

# =============================
# UI
# =============================
st.title("⚡ NSE Intraday AI Scanner (Final Safe Version)")
sector_name = st.sidebar.selectbox("Select Sector", list(sectors.keys()))
show_movers = st.sidebar.checkbox("Show Top Intraday Movers")

st.subheader(f"Sector: {sector_name}")
data = run_intraday_scanner(sectors[sector_name])

if not data.empty:
    st.dataframe(data, use_container_width=True)
    stock = st.selectbox("Select Stock", data['Stock'])
    chart = yf.download(stock+".NS", period="1d", interval="5m", progress=False)
    if not chart.empty:
        st.line_chart(chart['Close'])
else:
    st.warning("Market Closed or No new signals — showing last available signals")

if show_movers:
    st.subheader("🚀 Top Intraday Movers")
    movers = get_intraday_movers(sectors)
    if not movers.empty:
        st.dataframe(movers, use_container_width=True)
    else:
        st.info("No movers data available (Market Closed)")
