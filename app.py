import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V52", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V52 - PRO FILTER SYSTEM")
st.write(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# STOCK LIST (ADD FULL NSE200 HERE)
# ==========================================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]

# ==========================================
# INDICATORS
# ==========================================
def add_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA20'] = df['Close'].ewm(span=20).mean()

    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date').apply(
        lambda x: (x['Close']*x['Volume']).cumsum() / x['Volume'].cumsum()
    ).reset_index(level=0, drop=True)

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# ==========================================
# BIG PLAYER
# ==========================================
def is_big_player(row):
    return row['Volume'] > row['VolAvg'] * 2.5 and abs(row['Close'] - row['Open']) > row['ATR']

# ==========================================
# SIGNAL
# ==========================================
def get_signal(row):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

    if dist < 0.008 and row['Close'] > row['EMA20'] and row['Close'] > row['VWAP']:
        return "BUY"
    if dist < 0.008 and row['Close'] < row['EMA20'] and row['Close'] < row['VWAP']:
        return "SELL"
    return None

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=120)
def get_data():
    return yf.download([s+".NS" for s in stocks],
                       period="5d", interval="5m", group_by="ticker", threads=True)

def to_excel(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["📊 LIVE", "📜 BACKTEST"])

data = get_data()

# ==========================================
# LIVE
# ==========================================
with tab1:
    if st.button("🚀 SCAN MARKET"):
        results = []

        for s in stocks:
            try:
                df = data[s+".NS"].dropna()
                df = add_indicators(df)

                if len(df) < 30:
                    continue

                row = df.iloc[-1]

                # ⏰ TIME FILTER
                market_time = df.index[-1].tz_convert(IST).time()
                if market_time < datetime.strptime("09:30","%H:%M").time():
                    continue

                signal = get_signal(row)
                if not signal:
                    continue

                # 🔥 ATR FILTER
                if row['ATR'] < row['Close'] * 0.0015:
                    continue

                # 🎯 TARGET FILTER
                if abs((row['ATR']*3) / row['Close']) < 0.005:
                    continue

                entry = round(row['Close'], 2)

                results.append({
                    "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": signal,
                    "ENTRY": entry,
                    "SL": round(entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5, 2),
                    "TGT": round(entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3, 2),
                    "BIG PLAYER": "🔥 YES" if is_big_player(row) else "NO"
                })

            except:
                continue

        if results:
            df_out = pd.DataFrame(results)

            # 🔝 BEST TRADES ON TOP
            df_out = df_out.sort_values(by="TGT", ascending=False)

            st.success(f"Found {len(df_out)} Best Trades")
            st.dataframe(df_out, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_out), "signals_v52.xlsx")
        else:
            st.warning("No high-quality trades found")

# ==========================================
# BACKTEST
# ==========================================
with tab2:
    d = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("🔄 RUN BACKTEST"):
        logs = []

        for s in stocks:
            try:
                df_all = data[s+".NS"].dropna()
                df_all.index = df_all.index.tz_convert(IST)

                df = add_indicators(df_all[df_all.index.date == d])

                for i in range(20, len(df)):
                    row = df.iloc[i]

                    signal = get_signal(row)
                    if not signal:
                        continue

                    if row['ATR'] < row['Close'] * 0.0015:
                        continue

                    entry = round(row['Close'], 2)

                    logs.append({
                        "TIME": df.index[i].strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "ENTRY": entry,
                        "SL": round(entry - row['ATR']*1.5 if signal=="BUY" else entry + row['ATR']*1.5, 2),
                        "TGT": round(entry + row['ATR']*3 if signal=="BUY" else entry - row['ATR']*3, 2),
                        "BIG PLAYER": "🔥 YES" if is_big_player(row) else "NO"
                    })

            except:
                continue

        if logs:
            df_log = pd.DataFrame(logs)
            st.dataframe(df_log, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_log), "backtest_v52.xlsx")
        else:
            st.info("No backtest signals")
