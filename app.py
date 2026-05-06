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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V3 NSE200", layout="wide")
IST = pytz.timezone("Asia/Kolkata")

st.title("🚀 NSE AI QUANT PRO V3 - NSE 200 + BACKTEST")

# =============================
# NSE 200 STOCK LIST
# =============================
stocks = [
"ABB","ACC","AUBANK","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","AMBUJACEM",
"APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUROPHARMA","AXISBANK",
"BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BALKRISIND","BANDHANBNK","BANKBARODA","BEL",
"BERGEPAINT","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA",
"CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR",
"CROMPTON","CUMMINSIND","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB",
"DIXON","DLF","DRREDDY","EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS",
"GAIL","GLENMARK","GMRINFRA","GODREJCP","GODREJPROP","GRASIM","GUJGASLTD",
"HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO",
"HINDCOPPER","HINDPETRO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI",
"IDFCFIRSTB","IEX","IGL","INDHOTEL","INDIGO","INDUSINDBK","INDUSTOWER",
"INFY","IOC","IRCTC","IRFC","ITC","JINDALSTEL","JSWENERGY","JSWSTEEL",
"JUBLFOOD","KOTAKBANK","KPITTECH","L&TFH","LT","LTIM","LTTS","LICHSGFIN",
"LICI","LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO","MARUTI","MAXHEALTH",
"METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM",
"NESTLEIND","NMDC","NTPC","OBEROIRLTY","ONGC","PAYTM","PEL","PERSISTENT",
"PETRONET","PFC","PIDILITIND","PIIND","PNB","POLYCAB","POONAWALLA",
"POWERGRID","PRESTIGE","PVRINOX","RECLTD","RELIANCE","SAIL","SBICARD",
"SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA",
"SUNTV","SYNGENE","TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS",
"TATAPOWER","TATASTEEL","TCS","TECHM","TITAN","TORNTPHARM","TRENT",
"TVSMOTOR","ULTRACEMCO","UBL","UPL","VBL","VEDL","VOLTAS","WIPRO",
"YESBANK","ZEEL","ZOMATO",
"AARTIIND","ALKEM","BALRAMCHIN","BATAINDIA","BDL","BEML","CENTRALBK",
"COCHINSHIP","CREDITACC","EIDPARRY","ENGINERSIN","FSL","HATSUN",
"HFCL","IBULHSGFIN","INDIAMART","IRB","ISEC","JBCHEPHARM",
"KALYANKJIL","KEC","LALPATHLAB","MAHABANK","MAZDOCK","NBCC",
"NLCINDIA","OIL","PAGEIND","RBLBANK","ROUTE","RVNL","SCI",
"SUZLON","TANLA","TRIDENT","UJJIVANSFB","UNIONBANK"
]

# =============================
# INDICATORS
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

    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date')['PV'].cumsum() / df.groupby('Date')['Volume'].cumsum()

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
# DATA FETCH
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
    if st.button("🚀 SCAN NSE 200"):
        with st.spinner("Scanning..."):
            with ThreadPoolExecutor(max_workers=30) as executor:
                res = [r for r in executor.map(scan_stock, stocks) if r]

        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
        else:
            st.warning("No signals found")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        with st.spinner("Running..."):
            df_bt = run_backtest()

        if not df_bt.empty:
            wins = len(df_bt[df_bt['Result']=="PROFIT"])
            total = len(df_bt)
            st.metric("Win Rate %", round((wins/total)*100,2))

            st.dataframe(df_bt, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_bt.to_excel(writer, index=False)

            st.download_button("📥 Download Report", data=output.getvalue(), file_name="NSE200_Backtest.xlsx")
        else:
            st.warning("No trades found")
