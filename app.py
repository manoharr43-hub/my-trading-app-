import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io, os
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V51.2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V51.2 - TIME LOCKED ENGINE")

# =============================
# STOCK LIST (NSE)
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC",
    "POWERGRID","TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT",
    "ADANIPORTS","ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND",
    "BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL","IOC","BHARTIARTL","TITAN",
    "M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA","HAVELLS",
    "SIEMENS","PIDILITIND","BEL","DLF","INDUSINDBK","PNB","BANKBARODA",
    "CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    if df is None or len(df) < 50:
        return None
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df.dropna()

# =============================
# FETCH
# =============================
@st.cache_data(ttl=300)
def fetch():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)

data = fetch()

# =============================
# SIGNAL ENGINE
# =============================
def analyze(row):
    try:
        dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
        trend_up = row['EMA20'] > row['EMA50']
        trend_down = row['EMA20'] < row['EMA50']
        signal = None
        if dist < 0.004:
            if row['Close'] > row['VWAP'] and trend_up:
                signal = "BUY"
            elif row['Close'] < row['VWAP'] and trend_down:
                signal = "SELL"
        big_player = (row['Volume'] > row['VolAvg'] * 2 and abs(row['Close'] - row['Open']) > row['ATR'] * 0.5)
        big_move   = (row['Volume'] > row['VolAvg'] * 2 and abs(row['Close'] - row['Open']) > row['ATR'] * 0.7)
        return signal, big_player, big_move
    except:
        return None, False, False

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE", "📊 BACKTEST"])

# =============================
# LIVE SCAN
# =============================
with tab1:
    if st.button("RUN LIVE"):
        results = []
        for s in stocks:
            try:
                df = data.get(s + ".NS")
                df = add_indicators(df)
                if df is None: continue
                row = df.iloc[-1]
                signal, bp, bm = analyze(row)
                if signal:
                    atr = row['ATR']
                    results.append({
                        "TIME": df.index[-1].tz_localize("UTC").tz_convert(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "BIG PLAYER": "🔥" if bp else "-",
                        "BIG MOVE": "🚀" if bm else "-",
                        "ENTRY": round(row['Close'],2),
                        "SL": round(row['Close'] - atr*1.5 if signal=="BUY" else row['Close'] + atr*1.5,2),
                        "TARGET": round(row['Close'] + atr*3 if signal=="BUY" else row['Close'] - atr*3,2)
                    })
            except: continue
        st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# BACKTEST (TIME LOCKED)
# =============================
with tab2:
    bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))
    if st.button("RUN BACKTEST"):
        logs, last_time = [], {}
        cooldown = timedelta(minutes=45)
        for s in stocks:
            try:
                df = data.get(s + ".NS")
                if df is None: continue
                # ✅ TIME FIX
                df.index = df.index.tz_localize("UTC").tz_convert(IST) if df.index.tz is None else df.index.tz_convert(IST)
                # ✅ MARKET HOURS
                df = df.between_time("09:15", "15:30")
                # ✅ DATE FILTER
                df = df[df.index.normalize() == pd.to_datetime(bt_date)]
                df = add_indicators(df)
                if df is None: continue
                for i in range(20, len(df)):
                    row, prev, t = df.iloc[i], df.iloc[i-1], df.index[i]
                    signal, bp, bm = analyze(row)
                    if signal:
                        if abs(row['Close'] - prev['Close']) < row['ATR'] * 0.2: continue
                        if s in last_time and t - last_time[s] < cooldown: continue
                        atr = row['ATR']
                        logs.append({
                            "TIME": t.strftime('%H:%M'),
                            "STOCK": s,
                            "TYPE": signal,
                            "BIG PLAYER": "🔥" if bp else "-",
                            "BIG MOVE": "🚀" if bm else "-",
                            "PRICE": round(row['Close'],2),
                            "SL": round(row['Close'] - atr*1.5 if signal=="BUY" else row['Close'] + atr*1.5,2),
                            "TARGET": round(row['Close'] + atr*3 if signal=="BUY" else row['Close'] - atr*3,2)
                        })
                        last_time[s] = t
            except: continue
        df_bt = pd.DataFrame(logs)
        if not df_bt.empty:
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("Download Excel", to_excel(df_bt), "Backtest.xlsx")
        else:
            st.warning("No signals found")
