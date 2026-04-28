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
st.set_page_config(page_title="🚀 NSE AI PRO V48", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V48 - NSE 200 FULL SCANNER")

# =============================
# MARKET TIME
# =============================
market_open = time(9,15)
market_close = time(15,30)
is_market_open = market_open <= now.time() <= market_close

# =============================
# NSE 200 STOCK LIST (FULL)
# =============================
stocks = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
"LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC",
"POWERGRID","TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT",
"ADANIPORTS","ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND",
"BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL","IOC","BHARTIARTL","TITAN",
"M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA","SHREECEM","HAVELLS",
"SIEMENS","TORNTPHARM","PIDILITIND","LTIM","BEL","DLF","INDUSINDBK","PNB",
"BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    if len(df) < 50:
        return df

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    df['VWAP'] = (df['Close']*df['Volume']).cumsum()/(df['Volume'].cumsum()+1e-9)

    tr = pd.concat([
        df['High']-df['Low'],
        abs(df['High']-df['Close'].shift()),
        abs(df['Low']-df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# FETCH OPTIMIZED
# =============================
@st.cache_data(ttl=60)
def fetch():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

data = fetch()

# =============================
# SIGNAL
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
# TABS
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE SCAN", "📊 BACKTEST"])

# =============================
# LIVE SCAN
# =============================
with tab1:
    if not is_market_open:
        st.warning("⛔ Market Closed")
    else:
        if st.button("🚀 RUN LIVE NSE 200 SCAN"):

            results = []

            for s in stocks:
                try:
                    df = data.get(s + ".NS")
                    if df is None or df.empty:
                        continue

                    df = add_indicators(df.dropna())
                    row = df.iloc[-1]

                    signal = get_signal(row)

                    if signal:
                        atr = row['ATR']

                        big_player = (row['Volume'] > row['VolAvg']*2) and \
                                     (abs(row['Close']-row['Open']) > atr*0.5)

                        results.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s,
                            "SIGNAL": signal,
                            "BIG PLAYER": "🔥 YES" if big_player else "-",
                            "ENTRY": round(row['Close'],2),
                            "SL": round(row['Close'] - atr*1.5 if "BUY" in signal else row['Close'] + atr*1.5,2),
                            "TARGET": round(row['Close'] + atr*3 if "BUY" in signal else row['Close'] - atr*3,2)
                        })
                except:
                    continue

            if results:
                df_live = pd.DataFrame(results)
                st.dataframe(df_live, use_container_width=True)
                st.download_button("📥 Download Excel", to_excel(df_live), "LiveScan.xlsx")
            else:
                st.info("No signals")

# =============================
# BACKTEST
# =============================
with tab2:
    bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))

    if st.button("▶️ RUN BACKTEST"):

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

                for i in range(20, len(df)):
                    row = df.iloc[i]
                    prev = df.iloc[i-1]
                    curr_time = df.index[i]

                    signal = get_signal(row)

                    if signal:

                        # noise filter
                        if abs(row['Close'] - prev['Close']) < (row['ATR'] * 0.2):
                            continue

                        # duplicate control
                        if s in last_signal_time:
                            if curr_time - last_signal_time[s] < cooldown:
                                continue

                        atr = row['ATR']

                        big_player = (row['Volume'] > row['VolAvg']*2) and \
                                     (abs(row['Close']-row['Open']) > atr*0.5)

                        logs.append({
                            "TIME": curr_time.strftime('%H:%M'),
                            "STOCK": s,
                            "TYPE": signal,
                            "BIG PLAYER": "🔥 YES" if big_player else "-",
                            "PRICE": round(row['Close'],2),
                            "SL": round(row['Close'] - atr*1.5 if "BUY" in signal else row['Close'] + atr*1.5,2),
                            "TARGET": round(row['Close'] + atr*3 if "BUY" in signal else row['Close'] - atr*3,2)
                        })

                        last_signal_time[s] = curr_time

            except:
                continue

        if logs:
            df_bt = pd.DataFrame(logs)
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("📥 Download Backtest", to_excel(df_bt), "Backtest.xlsx")
            st.success(f"✅ Signals: {len(df_bt)}")
        else:
            st.warning("No signals found")
