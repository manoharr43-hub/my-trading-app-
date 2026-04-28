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
st.set_page_config(page_title="🚀 NSE AI PRO V46", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V46 - CLEAN BACKTEST SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","ITC","LT","MARUTI","TATAMOTORS","WIPRO","HCLTECH","SBIN","PNB","BANKBARODA","YESBANK","ZOMATO"]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 50:
        return df

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

# =============================
# FETCH DATA
# =============================
@st.cache_data(ttl=60)
def fetch():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

data = fetch()

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
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# BACKTEST ENGINE (FIXED)
# =============================
st.subheader("📊 SMART BACKTEST")

bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))

if st.button("🚀 RUN BACKTEST"):

    logs = []
    last_signal_time = {}
    cooldown = timedelta(minutes=45)

    for s in stocks:
        try:
            df = data.get(s + ".NS")
            if df is None or df.empty:
                continue

            df = df.dropna()
            df.index = df.index.tz_convert(IST)

            df = add_indicators(df[df.index.date == bt_date])
            if df is None or df.empty:
                continue

            for i in range(20, len(df)):
                row = df.iloc[i]
                prev = df.iloc[i-1]
                curr_time = df.index[i]

                signal = get_signal(row)

                if signal:

                    # 🔥 NOISE FILTER
                    if abs(row['Close'] - prev['Close']) < (row['ATR'] * 0.2):
                        continue

                    # 🔁 DUPLICATE CONTROL
                    if s in last_signal_time:
                        if curr_time - last_signal_time[s] < cooldown:
                            continue

                    entry = row['Close']
                    atr = row['ATR']

                    logs.append({
                        "TIME": curr_time.strftime('%H:%M'),
                        "STOCK": s,
                        "TYPE": signal,
                        "PRICE": round(entry,2),
                        "SL": round(entry - atr*1.5 if "BUY" in signal else entry + atr*1.5,2),
                        "TARGET": round(entry + atr*3 if "BUY" in signal else entry - atr*3,2)
                    })

                    last_signal_time[s] = curr_time

        except:
            continue

    # =============================
    # OUTPUT
    # =============================
    if logs:
        df_bt = pd.DataFrame(logs)

        # 🔥 SORT CLEAN
        df_bt = df_bt.sort_values(by=["STOCK","TIME"])

        st.dataframe(df_bt, use_container_width=True)

        st.download_button(
            "📥 Download Backtest Excel",
            to_excel(df_bt),
            file_name=f"Backtest_{bt_date}.xlsx"
        )

        st.success(f"✅ Total Signals: {len(df_bt)}")

    else:
        st.warning("❌ No signals found")
