import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="NSE SMART AI SCANNER", layout="wide")

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
# ANALYSIS
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 50:
        return None

    df = df.copy()

    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    vol_ratio = last_vol / (avg_vol + 1e-9)

    # Breakout
    high = df['High'].iloc[-20:-1].max()
    low = df['Low'].iloc[-20:-1].min()
    last_close = df['Close'].iloc[-1]

    breakout = "NONE"
    if last_close > high:
        breakout = "🚀 BREAKOUT"
    elif last_close < low:
        breakout = "📉 BREAKDOWN"

    # AI MODEL (SMART)
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    df = df.dropna()

    features = df[['EMA20','EMA50','RSI','VWAP']]
    target = df['Target']

    model = RandomForestClassifier()
    model.fit(features, target)

    prediction = model.predict([features.iloc[-1]])[0]
    ai_view = "🚀 BULLISH" if prediction == 1 else "📉 BEARISH"

    # Accuracy estimate (simple)
    accuracy = round(model.score(features, target)*100, 2)

    return df, vol_ratio, breakout, ai_view, accuracy

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="5d", interval="5m", progress=False, threads=False)

            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna()

            result = analyze_stock(df)
            if result is None:
                continue

            df, vol_ratio, breakout, ai_view, accuracy = result
            last = df.iloc[-1]

            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            ema20 = float(last['EMA20'])
            ema50 = float(last['EMA50'])
            vwap = float(last['VWAP'])

            trend = "UPTREND" if ema20 > ema50 else "DOWNTREND"

            # =============================
            # SMART SIGNAL
            # =============================
            signal = "WAIT"

            if (
                ltp > vwap and
                trend == "UPTREND" and
                rsi > 55 and
                vol_ratio > 1.5 and
                breakout == "🚀 BREAKOUT" and
                ai_view == "🚀 BULLISH" and
                accuracy > 60
            ):
                signal = "🔥 STRONG BUY"

            elif (
                ltp < vwap and
                trend == "DOWNTREND" and
                rsi < 45 and
                vol_ratio > 1.5 and
                breakout == "📉 BREAKDOWN" and
                ai_view == "📉 BEARISH" and
                accuracy > 60
            ):
                signal = "🔥 STRONG SELL"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "RSI": rsi,
                "Trend": trend,
                "Volume": round(vol_ratio,2),
                "AI": ai_view,
                "Accuracy %": accuracy,
                "Breakout": breakout,
                "Signal": signal
            })

        except Exception as e:
            st.warning(f"{t} error: {e}")

    return pd.DataFrame(results)

# =============================
# MAIN
# =============================
st.title("🔥 NSE SMART AI SCANNER")

st.write(f"📊 Sector: {sector_name}")

df = run_scanner(sectors[sector_name])

if not df.empty:
    st.dataframe(df, use_container_width=True)

    selected = st.selectbox("Select Stock", df['Stock'])

    st.subheader(f"📈 {selected} Chart")

    st.components.v1.html(f"""
    <div id="tv_chart"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
      "width": "100%",
      "height": 500,
      "symbol": "NSE:{selected}",
      "interval": "5",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "container_id": "tv_chart"
    }});
    </script>
    """, height=520)

else:
    st.warning("No strong signals found")
