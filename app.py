import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io, os

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V43.4", layout="wide")
st_autorefresh(interval=180000, key="refresh")  # auto-refresh every 3 min

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V43.4 - NSE 200 BIG MOVE SCANNER")
st.write(f"🕒 Market Time (IST): {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 STOCK LIST
# =============================
@st.cache_data(ttl=86400)
def load_nse200():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","LT","ITC"]

stocks = load_nse200()

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 50: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).apply(
        lambda x: (x[x>0].mean() / abs(x[x<0].mean())) if abs(x[x<0].mean())>0 else 0)))
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("🚀 Loading NSE 200 Data..."):
    data_5m = fetch_data(stocks, "5m", "5d")

def save_csv(df, filename):
    os.makedirs("signals", exist_ok=True)
    df.to_csv(f"signals/{filename}", index=False)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='BigMove_Report')
    return output.getvalue()

# =============================
# LIVE BIG MOVE SCAN
# =============================
if st.button("RUN BIG MOVE SCAN"):
    results = []
    for s in stocks:
        try:
            df_raw = data_5m.get(s + ".NS")
            if df_raw is None or df_raw.empty: continue
            df = add_indicators(df_raw.dropna())
            l = df.iloc[-1]

            dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
            big_vol = l['Volume'] > l['VolAvg']*3
            trend_up = l['EMA20'] > l['EMA50']
            trend_down = l['EMA20'] < l['EMA50']

            signal = "None"
            if dist < 0.004 and big_vol:
                if l['Close'] > l['VWAP'] and l['RSI'] > 55 and trend_up:
                    signal = "BIG BUY MOVE 🟢🔥"
                elif l['Close'] < l['VWAP'] and l['RSI'] < 45 and trend_down:
                    signal = "BIG SELL MOVE 🔴🔥"

            if signal != "None":
                entry = round(l['Close'], 2)
                results.append({
                    "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                    "STOCK": s, "ACTION": signal,
                    "ENTRY": entry,
                    "SL": round(entry - (l['Close']*0.01) if "BUY" in signal else entry + (l['Close']*0.01), 2),
                    "TGT": round(entry + (l['Close']*0.02) if "BUY" in signal else entry - (l['Close']*0.02), 2)
                })
        except: continue

    if results:
        df_live = pd.DataFrame(results)
        st.dataframe(df_live, use_container_width=True)
        save_csv(df_live, f"BigMove_{now.strftime('%Y%m%d_%H%M')}.csv")
        st.download_button("📥 Download Big Move Excel", data=to_excel(df_live),
                           file_name=f"BigMove_{now.strftime('%Y%m%d_%H%M')}.xlsx")
    else:
        st.info("No BIG MOVE signals right now.")
