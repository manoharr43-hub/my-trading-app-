import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(page_title="🚀 NSE AI V25 - ENTRY/SL/TGT", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown("<h1 style='text-align:center;color:#3b82f6;'>🚀 NSE AI QUANT V25 PRO</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>EMA 21 & VWAP + BIG VOL + ENTRY/SL/TARGET REPORT</h4>", unsafe_allow_html=True)

# =========================================================
# STOCK LIST (NIFTY 200)
# =========================================================
nifty_200 = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL",
    "ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK","CIPLA","COALINDIA","DLF","DRREDDY",
    "GAIL","HDFCBANK","HCLTECH","HINDALCO","ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M",
    "MARUTI","NTPC","ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO",
    "AUROPHARMA","BANKBARODA","BIOCON","CHOLAFIN","CONCOR","FEDERALBNK","HAVELLS","HEROMOTOCO","HIND-UNILVR",
    "IDFCFIRSTB","INDHOTEL","INDUSINDBK","IOC","IRCTC","JINDALSTEL","LTIM","LUPIN","MUTHOOTFIN","NAUKRI",
    "NESTLEIND","PFC","PNB","RECLTD","TATACONSUM","TATAMOTORS","TATAPOWER","TRENT","TVSMOTOR","VOLTAS"
]

# =========================================================
# ENGINE LOGIC
# =========================================================
def get_v25_analysis(stock, raw_data, mode="TODAY"):
    try:
        ticker = stock + ".NS"
        df = raw_data[ticker].dropna().copy()
        if len(df) < 50: return []

        # Indicators
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['PV'] = df['Close'] * df['Volume']
        df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))
        
        # Vol & ATR for Risk Management
        df['AvgVol'] = df['Volume'].rolling(20).mean()
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()

        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        # Filters for Backtest (Last 10 Days)
        ten_days_ago = (datetime.now(IST) - timedelta(days=10)).date()
        analysis_df = df[df.index.date >= ten_days_ago] if mode == "BACKTEST" else df[df.index.date == df.index.date.max()]

        results = []
        for i in range(1, len(analysis_df)):
            row = analysis_df.iloc[i]
            prev = analysis_df.iloc[i-1]

            # Signal Logic
            buy_cross = (prev['EMA21'] <= prev['VWAP']) and (row['EMA21'] > row['VWAP']) and (row['Volume'] > row['AvgVol'] * 1.5)
            sell_cross = (prev['EMA21'] >= prev['VWAP']) and (row['EMA21'] < row['VWAP']) and (row['Volume'] > row['AvgVol'] * 1.5)

            if buy_cross or sell_cross:
                entry_price = round(row['Close'], 2)
                atr_val = row['ATR']
                
                # SL & Target Calculation (Risk:Reward = 1:2)
                if buy_cross:
                    sl = round(entry_price - (atr_val * 1.5), 2)
                    tgt = round(entry_price + (atr_val * 3), 2)
                    signal = "BIG BUY"
                else:
                    sl = round(entry_price + (atr_val * 1.5), 2)
                    tgt = round(entry_price - (atr_val * 3), 2)
                    signal = "BIG SELL"

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": signal,
                    "ENTRY": entry_price,
                    "STOPLOSS": sl,
                    "TARGET": tgt,
                    "VOLUME": int(row['Volume'])
                })
        return results
    except: return []

# =========================================================
# EXCEL HELPER
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
    return output.getvalue()

# =========================================================
# DATA FETCH
# =========================================================
@st.cache_data(ttl=600)
def fetch_nifty_200():
    tickers = [s + ".NS" for s in nifty_200]
    return yf.download(tickers, period="1mo", interval="15m", group_by="ticker", auto_adjust=True, threads=True)

data_pool = fetch_nifty_200()

# =========================================================
# TABS UI
# =========================================================
t1, t2 = st.tabs(["🔍 LIVE SCANNER", "📊 10-DAY BACKTEST REPORT"])

with t1:
    if st.button("🚀 RUN V25 LIVE SCANNER"):
        live_res = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(get_v25_analysis, s, data_pool, "TODAY") for s in nifty_200]
            for f in futs:
                res = f.result()
                if res: live_res.append(res[-1]) # Latest only

        if live_res:
            df_l = pd.DataFrame(live_res)
            st.dataframe(df_l, use_container_width=True)
            st.download_button("📥 Export Live Trades (Excel)", to_excel(df_l), "Live_Trades.xlsx")
        else:
            st.info("No big volume crossovers found on today's chart.")

with t2:
    if st.button("📋 GENERATE 10-DAY BACKTEST REPORT"):
        bt_res = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(get_v25_analysis, s, data_pool, "BACKTEST") for s in nifty_200]
            for f in futs: bt_res.extend(f.result())

        if bt_res:
            df_b = pd.DataFrame(bt_res).sort_values(["DATE", "TIME"], ascending=False)
            st.dataframe(df_b, use_container_width=True)
            st.download_button("📥 Export 10-Day Report (Excel)", to_excel(df_b), "Backtest_10D_Report.xlsx")
        else:
            st.warning("No signals found in the last 10 trading days.")
