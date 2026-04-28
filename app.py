import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V45", layout="wide")

AUTO_REFRESH = st.sidebar.toggle("🔁 AUTO LIVE SCAN", True)
if AUTO_REFRESH:
    st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - SMART PULLBACK SYSTEM")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# MARKET TIME FILTER
# =============================
market_open = time(9, 15)
market_close = time(15, 30)
is_market_open = market_open <= now.time() <= market_close

# =============================
# STOCKS + SECTORS
# =============================
stocks = {
    "RELIANCE":"ENERGY","TCS":"IT","INFY":"IT","HDFCBANK":"BANK","ICICIBANK":"BANK",
    "SBIN":"BANK","AXISBANK":"BANK","KOTAKBANK":"BANK","LT":"INFRA","ITC":"FMCG",
    "HINDUNILVR":"FMCG","ASIANPAINT":"FMCG","MARUTI":"AUTO","TATAMOTORS":"AUTO",
    "M&M":"AUTO","SUNPHARMA":"PHARMA","CIPLA":"PHARMA","DRREDDY":"PHARMA",
    "ONGC":"ENERGY","NTPC":"ENERGY","POWERGRID":"ENERGY","TATASTEEL":"METAL",
    "JSWSTEEL":"METAL","BAJFINANCE":"FINANCE","BAJAJFINSV":"FINANCE",
    "ADANIENT":"INFRA","ADANIPORTS":"INFRA","ULTRACEMCO":"CEMENT",
    "GRASIM":"CEMENT","TECHM":"IT","WIPRO":"IT","HCLTECH":"IT",
    "NESTLEIND":"FMCG","BRITANNIA":"FMCG","BPCL":"ENERGY","IOC":"ENERGY",
    "BHARTIARTL":"TELCO","TITAN":"CONSUMER","HEROMOTOCO":"AUTO",
    "EICHERMOT":"AUTO","COALINDIA":"ENERGY","HAVELLS":"ELECTRICAL",
    "SIEMENS":"INDUSTRIAL","PIDILITIND":"CHEMICAL","BEL":"DEFENSE",
    "DLF":"REALTY","INDUSINDBK":"BANK","PNB":"BANK","BANKBARODA":"BANK",
    "CANBK":"BANK","FEDERALBNK":"BANK","IDFCFIRSTB":"BANK","YESBANK":"BANK",
    "ZOMATO":"TECH","ZEEL":"MEDIA"
}

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

@st.cache_data(ttl=60)
def fetch():
    tickers = [s + ".NS" for s in stocks.keys()]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

data = fetch()

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# SIGNAL ENGINE
# =============================
def get_signal(row):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

    trend_up = row['EMA20'] > row['EMA50']
    trend_down = row['EMA20'] < row['EMA50']

    if dist < 0.004:
        if row['Close'] > row['VWAP'] and trend_up:
            return "BUY 🟢"
        elif row['Close'] < row['VWAP'] and trend_down:
            return "SELL 🔴"
    return None

# =============================
# LIVE SCAN
# =============================
st.subheader("🔍 LIVE SCANNER")

if st.button("🚀 RUN SCAN"):

    if not is_market_open:
        st.warning("⛔ Market Closed (9:15–15:30 మాత్రమే)")
    else:
        results = []

        for s, sector in stocks.items():
            try:
                df = data.get(s + ".NS")
                if df is None or df.empty: continue

                df = add_indicators(df.dropna())
                row = df.iloc[-1]

                signal = get_signal(row)

                if signal:
                    entry = row['Close']
                    atr = row['ATR']

                    big_player = (row['Volume'] > row['VolAvg']*2) and (abs(row['Close']-row['Open']) > atr*0.5)

                    results.append({
                        "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SECTOR": sector,
                        "SIGNAL": signal,
                        "BIG PLAYER": "🔥 STRONG" if big_player else "-",
                        "ENTRY": round(entry,2),
                        "SL": round(entry - atr*1.5 if "BUY" in signal else entry + atr*1.5,2),
                        "TARGET": round(entry + atr*3 if "BUY" in signal else entry - atr*3,2)
                    })
            except:
                continue

        if results:
            df_live = pd.DataFrame(results).sort_values(by="SECTOR")
            st.dataframe(df_live, use_container_width=True)

            st.download_button("📥 Download Excel", to_excel(df_live), "LiveScan.xlsx")
        else:
            st.info("No signals found")

# =============================
# BACKTEST
# =============================
st.subheader("📊 BACKTEST")

bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))

if st.button("▶️ RUN BACKTEST"):
    logs = []

    for s, sector in stocks.items():
        try:
            df = data.get(s + ".NS")
            if df is None: continue

            df = df.dropna()
            df.index = df.index.tz_convert(IST)
            df = add_indicators(df[df.index.date == bt_date])

            for i in range(20, len(df)):
                row = df.iloc[i]
                signal = get_signal(row)

                if signal:
                    entry = row['Close']
                    atr = row['ATR']

                    logs.append({
                        "TIME": df.index[i].strftime('%H:%M'),
                        "STOCK": s,
                        "SECTOR": sector,
                        "TYPE": signal,
                        "PRICE": round(entry,2),
                        "SL": round(entry - atr*1.5 if "BUY" in signal else entry + atr*1.5,2),
                        "TARGET": round(entry + atr*3 if "BUY" in signal else entry - atr*3,2)
                    })
        except:
            continue

    if logs:
        df_bt = pd.DataFrame(logs)
        st.dataframe(df_bt, use_container_width=True)
        st.download_button("📥 Download Backtest", to_excel(df_bt), "Backtest.xlsx")
    else:
        st.warning("No signals")
