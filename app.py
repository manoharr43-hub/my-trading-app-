import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import io, os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V45", layout="wide")
st_autorefresh(interval=180000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - BIG MOVE SCANNER + BACKTEST")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# NSE 200 LIST
# =============================
@st.cache_data(ttl=86400)
def load_nse200():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
        df = pd.read_csv(url)
        return df['Symbol'].tolist()
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK"]

stocks = load_nse200()

# =============================
# INDICATORS FIXED
# =============================
def add_indicators(df):
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # FIXED RSI (REAL RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def fetch_data(symbols):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

with st.spinner("🚀 Loading NSE Data..."):
    data = fetch_data(stocks)

# =============================
# SAVE + EXCEL
# =============================
def save_csv(df, filename):
    os.makedirs("signals", exist_ok=True)
    df.to_csv(f"signals/{filename}", index=False)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='REPORT')
    return output.getvalue()

# =============================
# LIVE SCAN
# =============================
if st.button("🔥 RUN BIG MOVE SCAN"):
    results = []

    for s in stocks:
        try:
            df_raw = data.get(s + ".NS")
            if df_raw is None or df_raw.empty:
                continue

            df = add_indicators(df_raw.dropna())
            if len(df) < 60:
                continue

            last = df.iloc[-1]

            dist = abs(last['Close'] - last['EMA20']) / last['EMA20']
            big_vol = last['Volume'] > last['VolAvg'] * 3
            trend_up = last['EMA20'] > last['EMA50']
            trend_down = last['EMA20'] < last['EMA50']

            signal = None

            if dist < 0.004 and big_vol:
                if last['Close'] > last['VWAP'] and last['RSI'] > 55 and trend_up:
                    signal = "BIG BUY 🟢🔥"
                elif last['Close'] < last['VWAP'] and last['RSI'] < 45 and trend_down:
                    signal = "BIG SELL 🔴🔥"

            if signal:
                entry = round(last['Close'], 2)

                results.append({
                    "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                    "STOCK": s,
                    "ACTION": signal,
                    "ENTRY": entry,
                    "SL": round(entry * 0.99 if "BUY" in signal else entry * 1.01, 2),
                    "TARGET": round(entry * 1.02 if "BUY" in signal else entry * 0.98, 2)
                })

        except:
            continue

    if results:
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True)

        save_csv(df_res, f"BIGMOVE_{now.strftime('%Y%m%d_%H%M')}.csv")

        st.download_button(
            "📥 Download Excel",
            data=to_excel(df_res),
            file_name=f"BIGMOVE_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        )
    else:
        st.warning("No BIG MOVE signals found.")
