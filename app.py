import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz, os
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V43.5", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V43.5 - ULTIMATE SNAPSHOT")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# SECTOR-WISE STOCKS
# =============================
sectors = {
    "BANKING":["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","PNB","BANKBARODA","CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK"],
    "IT":["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM"],
    "AUTO":["MARUTI","M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS"],
    "PHARMA":["SUNPHARMA","CIPLA","DIVISLAB","DRREDDY","TORNTPHARM"],
    "METALS":["TATASTEEL","JSWSTEEL","COALINDIA"],
    "FMCG":["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","ASIANPAINT","PIDILITIND"],
    "ENERGY":["RELIANCE","ONGC","NTPC","POWERGRID","BPCL","IOC"],
    "OTHERS":["LT","ADANIENT","ADANIPORTS","ULTRACEMCO","GRASIM","BHARTIARTL","TITAN","SHREECEM","HAVELLS","SIEMENS","BEL","DLF","INDUSINDBK","ZEEL","ZOMATO"]
}
sector_choice = st.sidebar.selectbox("📂 Select Sector", ["ALL"] + list(sectors.keys()))

# =============================
# SETTINGS
# =============================
gap = st.sidebar.slider("Signal Gap (minutes)", 30, 120, 45)
vol_mult = st.sidebar.slider("Big Player Volume Multiplier", 2.0, 4.0, 2.5)

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

with st.spinner("🚀 Loading NSE Data..."):
    stocks = []
    if sector_choice == "ALL":
        for v in sectors.values(): stocks += v
    else:
        stocks = sectors[sector_choice]
    data_5m = fetch_data(stocks, "5m", "5d")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

def save_csv(df, name):
    os.makedirs("reports", exist_ok=True)
    df.to_csv(f"reports/{name}.csv", index=False)

# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCAN", "📊 BACKTEST"])

# -----------------------------
# TAB 1: LIVE SCAN
# -----------------------------
with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None or df_raw.empty: continue
                df_raw.index = df_raw.index.tz_localize("UTC").tz_convert(IST)
                df = add_indicators(df_raw.dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                if dist < 0.004:
                    sig = None
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: sig = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: sig = "SELL 🔴"
                    if sig:
                        entry = round(l['Close'], 2)
                        results.append({
                            "TIME": df.index[-1].strftime('%H:%M'),
                            "STOCK": s, "ACTION": sig,
                            "BIG PLAYER": "🔥 YES" if l['Volume'] > l['VolAvg']*vol_mult else "-",
                            "ENTRY": entry,
                            "SL": round(entry - (l['ATR']*1.5) if "BUY" in sig else entry + (l['ATR']*1.5), 2),
                            "TGT": round(entry + (l['ATR']*3) if "BUY" in sig else entry - (l['ATR']*3), 2)
                        })
            except: continue
        if results:
            df_live = pd.DataFrame(results)
            st.dataframe(df_live, use_container_width=True)
            st.download_button("📥 Download Excel", data=to_excel(df_live), file_name=f"Live_{now.strftime('%Y%m%d_%H%M')}.xlsx")
            save_csv(df_live, f"Live_{now.strftime('%Y%m%d_%H%M')}")
        else:
            st.info("No signals found.")

# -----------------------------
# TAB 2: BACKTEST
# -----------------------------
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST"):
        bt_logs = []
        for s in stocks:
            try:
                df_raw = data_5m.get(s + ".NS")
                if df_raw is None or df_raw.empty: continue
                df_raw.index = df_raw.index.tz_localize("UTC").tz_convert(IST)
                df_day = add_indicators(df_raw[df_raw.index.date == bt_date])
                if df_day is None or df_day.empty: continue
                last_action, last_time = None, None
                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    if dist < 0.004:
                        sig = None
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']: sig = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']: sig = "SELL 🔴"
                        if sig:
                            if sig != last_action or (last_time and (curr_time - last_time) > timedelta(minutes=gap)):
                                entry = round(row['Close'], 2)
                                bt_logs.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "TYPE": sig, "PRICE": entry,
                                    "BIG PLAYER": "🔥" if row['Volume'] > row['VolAvg']*vol_mult else "-",
                                    "SL": round(entry - (row['ATR']*1.5) if "BUY" in sig else entry + (row['ATR']*1.5), 2),
                                    "TGT": round(entry + (row['ATR']*3) if "BUY" in sig else entry - (row['ATR']*3), 2)
                                })
                                last_action, last_time = sig, curr_time
            except: continue
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.dataframe(bt_df, use_container_width=True
