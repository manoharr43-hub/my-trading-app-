import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V4 STABLE", layout="wide")
IST = pytz.timezone("Asia/Kolkata")

st.title("🚀 NSE AI QUANT PRO V4 - STABLE NSE200")

# =============================
# NSE STOCK LIST (Lite for stability)
# =============================
stocks = [
"RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK",
"BAJFINANCE","ASIANPAINT","MARUTI","TITAN","SUNPHARMA","WIPRO","ULTRACEMCO",
"POWERGRID","NTPC","ONGC","JSWSTEEL","TATASTEEL","HINDALCO","COALINDIA",
"DRREDDY","CIPLA","DIVISLAB","EICHERMOT","HEROMOTOCO","M&M","BAJAJ-AUTO",
"BPCL","IOC","ADANIPORTS","ADANIENT","DLF","GAIL","VEDL","PEL","HAL",
"BEL","SIEMENS","ABB","BHEL","HAVELLS","DABUR","MARICO","COLPAL","NESTLEIND",
"BRITANNIA","PIDILITIND","GODREJCP","TATACONSUM","INDIGO","IRCTC"
]

# =============================
# INDICATORS (VWAP FIXED)
# =============================
def add_indicators(df):
    df = df.copy()
    if df.empty:
        return df

    df['EMA20'] = df['Close'].ewm(span=20).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / (loss + 1e-9)))

    # ✅ VWAP FIX
    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['CumPV'] = df.groupby('Date')['PV'].transform('cumsum')
    df['CumVol'] = df.groupby('Date')['Volume'].transform('cumsum')
    df['VWAP'] = df['CumPV'] / (df['CumVol'] + 1e-9)

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)

    return df

# =============================
# DATA FETCH SAFE
# =============================
@st.cache_data(ttl=60)
def fetch_data():
    data = {}
    for s in stocks:
        try:
            df = yf.download(s + ".NS", period="5d", interval="5m", progress=False)
            if not df.empty:
                data[s] = df
        except:
            continue
    return data

data = fetch_data()

# =============================
# SCANNER
# =============================
def scan_stock(s):
    try:
        if s not in data:
            return None

        df = add_indicators(data[s].dropna())
        if len(df) < 50:
            return None

        last = df.iloc[-1]

        if last['Close'] > last['VWAP'] and last['RSI'] > 55 and last['RVOL'] > 1.5:
            return {
                "Stock": s,
                "Price": round(last['Close'], 2),
                "Signal": "BUY",
                "RVOL": round(last['RVOL'], 2)
            }
    except:
        return None

# =============================
# BACKTEST
# =============================
def run_backtest():
    results = []

    for s in stocks:
        if s not in data:
            continue

        df = add_indicators(data[s].dropna())
        if len(df) < 50:
            continue

        for i in range(30, len(df) - 10):
            row = df.iloc[i]

            if row['Close'] > row['VWAP'] and row['RSI'] > 55 and row['RVOL'] > 1.3:

                entry = row['Close']
                atr = row['ATR']
                if atr == 0 or np.isnan(atr):
                    continue

                sl = entry - atr * 1.5
                tgt = entry + atr * 2.5

                result = "OPEN"
                exit_price = None
                exit_time = None

                for j in range(i+1, min(i+50, len(df))):
                    if df.iloc[j]['Low'] <= sl:
                        result = "LOSS"
                        exit_price = sl
                        exit_time = df.index[j]
                        break

                    if df.iloc[j]['High'] >= tgt:
                        result = "PROFIT"
                        exit_price = tgt
                        exit_time = df.index[j]
                        break

                if result != "OPEN":
                    entry_dt = df.index[i].astimezone(IST)
                    exit_dt = exit_time.astimezone(IST)

                    duration = (exit_dt - entry_dt).total_seconds() / 60
                    pnl = exit_price - entry

                    results.append({
                        "Stock": s,
                        "Entry_DateTime": entry_dt.strftime('%Y-%m-%d %H:%M'),
                        "Exit_DateTime": exit_dt.strftime('%Y-%m-%d %H:%M'),
                        "Entry": round(entry, 2),
                        "Exit": round(exit_price, 2),
                        "Result": result,
                        "PnL": round(pnl, 2),
                        "Duration_Min": round(duration, 1)
                    })

    return pd.DataFrame(results)

# =============================
# UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 SCAN"):
        with st.spinner("Scanning..."):
            with ThreadPoolExecutor(max_workers=15) as executor:
                res = [r for r in executor.map(scan_stock, stocks) if r]

        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
        else:
            st.warning("No signals")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with st.spinner("Running backtest..."):
            df_bt = run_backtest()

        if not df_bt.empty:
            wins = len(df_bt[df_bt['Result']=="PROFIT"])
            total = len(df_bt)

            st.metric("Win Rate %", round((wins/total)*100,2))

            st.dataframe(df_bt, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False)

            st.download_button("📥 Download Report", data=output.getvalue(), file_name="Backtest_V4.xlsx")
        else:
            st.warning("No trades found")
