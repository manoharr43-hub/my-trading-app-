import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="NSE SUPER FAST AI SCANNER", layout="wide")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze(df):
    if df.empty or len(df) < 50:
        return None

    df = df.copy()

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain/(loss+1e-9)
    df['RSI'] = 100 - (100/(1+rs))

    # Volume
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1] / (avg_vol + 1e-9)

    # Breakout
    high = df['High'].iloc[-20:-1].max()
    low = df['Low'].iloc[-20:-1].min()

    breakout = "NONE"
    if df['Close'].iloc[-1] > high:
        breakout = "🚀 BREAKOUT"
    elif df['Close'].iloc[-1] < low:
        breakout = "📉 BREAKDOWN"

    # AI MODEL
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'],1,0)
    df = df.dropna()

    X = df[['EMA20','EMA50','RSI','VWAP']]
    y = df['Target']

    model = RandomForestClassifier(n_estimators=50)
    model.fit(X,y)

    pred = model.predict([X.iloc[-1]])[0]
    acc = round(model.score(X,y)*100,2)

    ai = "🚀 BULLISH" if pred==1 else "📉 BEARISH"

    return df, vol_ratio, breakout, ai, acc

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    # ⚡ BULK DOWNLOAD (FAST)
    data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

    for s in tickers:
        try:
            df = data[s].dropna()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            res = analyze(df)
            if res is None:
                continue

            df, vol, breakout, ai, acc = res
            last = df.iloc[-1]

            ltp = float(last['Close'])
            ema20 = float(last['EMA20'])
            ema50 = float(last['EMA50'])
            rsi = float(last['RSI'])
            vwap = float(last['VWAP'])

            trend = "UPTREND" if ema20 > ema50 else "DOWNTREND"

            # =============================
            # SMART SIGNAL (RELAXED)
            # =============================
            signal = "WAIT"
            entry, sl, target = "-", "-", "-"

            # BUY
            if (ltp > vwap and trend == "UPTREND" and rsi > 50 and vol > 1.2 and ai == "🚀 BULLISH"):
                signal = "🔥 BUY"
                entry = round(ltp,2)
                sl = round(df['Low'].iloc[-20:].min(),2)
                target = round(entry + (entry - sl)*2,2)

            # SELL
            elif (ltp < vwap and trend == "DOWNTREND" and rsi < 50 and vol > 1.2 and ai == "📉 BEARISH"):
                signal = "🔥 SELL"
                entry = round(ltp,2)
                sl = round(df['High'].iloc[-20:].max(),2)
                target = round(entry - (sl - entry)*2,2)

            if signal != "WAIT":
                results.append({
                    "Stock": s.replace(".NS",""),
                    "Price": round(ltp,2),
                    "Trend": trend,
                    "RSI": round(rsi,1),
                    "Volume": round(vol,2),
                    "AI": ai,
                    "Accuracy": acc,
                    "Signal": signal,
                    "Entry": entry,
                    "SL": sl,
                    "Target": target
                })

        except:
            continue

    return pd.DataFrame(results)

# =============================
# MAIN UI
# =============================
st.title("⚡ NSE SUPER FAST AI SCANNER")

st.write(f"📊 Selected Sector: {sector_name}")

df = run_scanner(sectors[sector_name])

if not df.empty:
    st.success(f"🔥 {len(df)} Signals Found")
    st.dataframe(df)

    selected = st.selectbox("Select Stock", df['Stock'])

    # =============================
    # CHART (WORKING)
    # =============================
    st.subheader(f"📈 {selected} Chart")

    chart = yf.download(selected + ".NS", period="1d", interval="5m")

    if not chart.empty:
        st.line_chart(chart['Close'])
    else:
        st.warning("Chart not available")

else:
    st.warning("No signals found now (market condition)")
