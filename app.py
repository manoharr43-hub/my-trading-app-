import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V21 - Excel Ready", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V21 - EXCEL DOWNLOAD ENABLED")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL","SBIN","ITC","LT","BAJFINANCE",
          "AXISBANK","KOTAKBANK","HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS","ULTRACEMCO","ADANIENT","JSWSTEEL"]

# =============================
# CORE FUNCTIONS
# =============================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

@st.cache_data(ttl=60)
def fetch_multi_data(stock_list, interval, period):
    tickers = [s + ".NS" for s in stock_list]
    return yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)

# ఎక్సెల్ ఫైల్ కన్వర్టర్
def convert_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# TABS SETUP
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 1-DAY SCANNER", "🎯 1-DAY PULLBACK", "📊 ACCURACY TEST", "🔥 PB BACKTEST"])

# Fetching Data
data_5m = fetch_multi_data(stocks, "5m", "5d")
data_1d = fetch_multi_data(stocks, "1d", "6mo")

# -----------------------------
# TAB 1: 1-DAY SCANNER
# -----------------------------
with tab1:
    if st.button("🚀 RUN 1-DAY SCAN", key="scan_1d"):
        res = []
        for s in stocks:
            try:
                df_1d = add_indicators(data_1d[s + ".NS"].dropna())
                df_5m = add_indicators(data_5m[s + ".NS"].dropna())
                is_bull_1d = df_1d['Close'].iloc[-1] > df_1d['EMA20'].iloc[-1]
                last_p = round(df_5m['Close'].iloc[-1], 2)
                atr = df_5m['ATR'].iloc[-1]
                if is_bull_1d and last_p > df_5m['VWAP'].iloc[-1]:
                    res.append({
                        "TIME": df_5m.index[-1].strftime('%H:%M'), "STOCK": s, "1D TREND": "UP 📈",
                        "ENTRY": last_p, "SL": round(last_p - (atr*1.5), 2),
                        "TARGET": round(last_p + (atr*3), 2), "SMART": "🔥 BIG" if df_5m['Volume'].iloc[-1] > df_5m['Volume'].rolling(20).mean().iloc[-1]*2 else "Normal"
                    })
            except: continue
        if res:
            df_res = pd.DataFrame(res)
            st.dataframe(df_res, use_container_width=True)
            # ఎక్సెల్ డౌన్‌లోడ్ బటన్
            excel_data = convert_to_excel(df_res)
            st.download_button(label="📥 Download Scanner Data (Excel)", data=excel_data, file_name="NSE_Scanner_Report.xlsx")
        else: st.info("No stocks matching trend.")

# -----------------------------
# TAB 2: 1-DAY PULLBACK
# -----------------------------
with tab2:
    if st.button("🎯 SCAN 1D PULLBACKS", key="pb_1d"):
        pb_res = []
        for s in stocks:
            try:
                df_5m = add_indicators(data_5m[s + ".NS"].dropna())
                last_5m = df_5m.iloc[-1]
                dist = abs(last_5m['Close'] - last_5m['EMA20']) / last_5m['EMA20']
                if dist < 0.005 and last_5m['Close'] > last_5m['Open']:
                    pb_res.append({
                        "TIME": df_5m.index[-1].strftime('%H:%M'), "STOCK": s, 
                        "ENTRY": round(last_5m['Close'], 2), "SL": round(last_5m['Close'] - last_5m['ATR'], 2),
                        "TARGET": round(last_5m['Close'] + (last_5m['ATR']*2), 2), "TYPE": "BUY PB"
                    })
            except: continue
        if pb_res:
            df_pb = pd.DataFrame(pb_res)
            st.dataframe(df_pb, use_container_width=True)
            # ఎక్సెల్ డౌన్‌లోడ్ బటన్
            excel_pb = convert_to_excel(df_pb)
            st.download_button(label="📥 Download Pullback Data (Excel)", data=excel_pb, file_name="NSE_Pullback_Report.xlsx")
        else: st.info("No pullbacks found.")

# -----------------------------
# TAB 4: PB BACKTEST (with Excel)
# -----------------------------
with tab4:
    test_date = st.date_input("Backtest Date", value=now.date() - timedelta(days=1), key="bt_date")
    if st.button("🔥 START ACCURATE BACKTEST", key="bt_run"):
        logs = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                df_day = df[df.index.date == test_date]
                for i in range(15, len(df_day)-4):
                    snap = df_day.iloc[:i+1]
                    if abs(snap['Close'].iloc[-1] - snap['EMA20'].iloc[-1]) / snap['EMA20'].iloc[-1] < 0.005:
                        entry_p = snap['Close'].iloc[-1]
                        exit_p = df_day['Close'].iloc[i+4]
                        res = "WIN ✅" if exit_p > entry_p else "LOSS ❌"
                        logs.append({"ENTRY_TIME": df_day.index[i].strftime('%H:%M'), "STOCK": s, "ENTRY": round(entry_p,2), "RESULT": res})
            except: continue
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs, use_container_width=True)
            # ఎక్సెల్ డౌన్‌లోడ్ బటన్
            excel_bt = convert_to_excel(df_logs)
            st.download_button(label="📥 Download Backtest Report (Excel)", data=excel_bt, file_name="Backtest_Report.xlsx")
