import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="NSE PRO AI SCANNER", layout="wide")

# =============================
# AUTO REFRESH
# =============================
st_autorefresh(interval=20000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))

# =============================
# COLOR FUNCTIONS
# =============================
def color_signal(val):
    if "BUY" in str(val):
        return "background-color: green; color: white"
    elif "SELL" in str(val):
        return "background-color: red; color: white"
    return ""

def color_trend(val):
    if val == "UP":
        return "background-color: green; color: white"
    elif val == "DOWN":
        return "background-color: red; color: white"
    return ""

# =============================
# ANALYSIS
# =============================
def analyze(df):
    try:
        if df is None or df.empty or len(df) < 30:
            return None

        df = df.copy()

        # EMA
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        # VWAP
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)

        # RSI
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain/(loss+1e-9)
        df['RSI'] = 100-(100/(1+rs))

        # Volume
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        vol = df['Volume'].iloc[-1]/(avg_vol+1e-9)

        # AI MODEL
        df['Target'] = np.where(df['Close'].shift(-1)>df['Close'],1,0)
        df = df.dropna()

        if df.empty:
            return None

        X = df[['EMA20','EMA50','RSI','VWAP']]
        y = df['Target']

        model = RandomForestClassifier(n_estimators=30)
        model.fit(X,y)

        pred = model.predict([X.iloc[-1]])[0]
        acc = round(model.score(X,y)*100,2)

        ai = "BUY" if pred==1 else "SELL"

        return df, vol, ai, acc

    except:
        return None

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except Exception as e:
        st.error(f"Data error: {e}")
        return pd.DataFrame()

    for s in tickers:
        try:
            # SAFE ACCESS
            if len(tickers) == 1:
                df = data.copy()
            else:
                if s not in data:
                    continue
                df = data[s].copy()

            df = df.dropna()

            if df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            res = analyze(df)
            if res is None:
                continue

            df, vol, ai, acc = res
            last = df.iloc[-1]

            ltp = float(last['Close'])
            ema20 = float(last['EMA20'])
            ema50 = float(last['EMA50'])
            rsi = float(last['RSI'])
            vwap = float(last['VWAP'])

            trend = "UP" if ema20 > ema50 else "DOWN"

            signal = "WAIT"

            # RELAXED CONDITIONS (signals రావడానికి)
            if (ltp > vwap and trend=="UP" and rsi>48 and ai=="BUY"):
                signal = "🔥 BUY"

            elif (ltp < vwap and trend=="DOWN" and rsi<52 and ai=="SELL"):
                signal = "🔥 SELL"

            results.append({
                "Stock": s.replace(".NS",""),
                "Price": round(ltp,2),
                "Trend": trend,
                "RSI": round(rsi,1),
                "Volume": round(vol,2),
                "AI": ai,
                "Accuracy": acc,
                "Signal": signal
            })

        except Exception as e:
            continue

    return pd.DataFrame(results)

# =============================
# UI
# =============================
st.title("🔥 NSE PRO AI SCANNER (FINAL FIXED)")

st.write(f"📊 Sector: {sector_name}")

df = run_scanner(sectors[sector_name])

if not df.empty:

    st.subheader("🚀 Live Signals")

    styled_df = df.style.map(color_signal, subset=['Signal']) \
                         .map(color_trend, subset=['Trend'])

    st.dataframe(styled_df, use_container_width=True)

    if st.button("🔄 Refresh Data"):
        st.rerun()

    selected = st.selectbox("📈 Select Stock", df['Stock'])

    chart = yf.download(selected+".NS", period="1d", interval="5m", progress=False)

    if not chart.empty:
        st.line_chart(chart['Close'])
    else:
        st.warning("Chart not available")

else:
    st.warning("No signals found now")
