import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="NSE SUPER FAST SCANNER", layout="wide")

# =============================
# FULL NSE SECTORS (MORE ADDED)
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"],
    "Adani": ["ADANIENT.NS","ADANIPORTS.NS","ADANIGREEN.NS","ADANIPOWER.NS"]
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
def analyze(df):
    if df.empty or len(df) < 30:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain/(loss+1e-9)
    df['RSI'] = 100-(100/(1+rs))

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol = df['Volume'].iloc[-1]/(avg_vol+1e-9)

    df['Target'] = np.where(df['Close'].shift(-1)>df['Close'],1,0)
    df = df.dropna()

    X = df[['EMA20','EMA50','RSI','VWAP']]
    y = df['Target']

    model = RandomForestClassifier(n_estimators=30)
    model.fit(X,y)

    pred = model.predict([X.iloc[-1]])[0]
    acc = round(model.score(X,y)*100,2)

    ai = "BUY" if pred==1 else "SELL"

    return df, vol, ai, acc

# =============================
# SCANNER
# =============================
def run_scanner(tickers):
    results = []

    data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

    for s in tickers:
        try:
            df = data[s].dropna()

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

            # 🔥 EASY SIGNAL (MORE RESULTS)
            signal = "WAIT"

            if (ltp > vwap and trend=="UP" and rsi>48 and ai=="BUY"):
                signal = "BUY"

            elif (ltp < vwap and trend=="DOWN" and rsi<52 and ai=="SELL"):
                signal = "SELL"

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

        except:
            continue

    return pd.DataFrame(results)

# =============================
# UI
# =============================
st.title("⚡ NSE SUPER FAST SCANNER (FIXED)")

st.write(f"📊 Sector: {sector_name}")

df = run_scanner(sectors[sector_name])

if not df.empty:
    st.dataframe(df)

    selected = st.selectbox("Select Stock", df['Stock'])

    chart = yf.download(selected+".NS", period="1d", interval="5m")

    if not chart.empty:
        st.line_chart(chart['Close'])
else:
    st.warning("Market slow / no signals now")
