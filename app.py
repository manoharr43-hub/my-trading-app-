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
st.set_page_config(page_title="🚀 EMA21-VWAP BIG VOL SCANNER", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown("<h1 style='text-align:center;color:#3b82f6;'>🚀 NSE AI QUANT V24</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;'>EMA 21 & VWAP CROSSOVER + BIG VOLUME</h3>", unsafe_allow_html=True)

# =========================================================
# NIFTY 200 STOCKS (Top 150+ for Performance)
# =========================================================
nifty_200 = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL",
    "ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK","CIPLA","COALINDIA","DLF","DRREDDY",
    "GAIL","HDFCBANK","HCLTECH","HINDALCO","ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M",
    "MARUTI","NTPC","ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO",
    "AUROPHARMA","BALKRISIND","BANKBARODA","BERGEPAINT","BIOCON","CHOLAFIN","CONCOR","CUMMINSIND","ESCORTS",
    "FEDERALBNK","GODREJCP","HAVELLS","HEROMOTOCO","HIND-UNILVR","ICICIGI","IDFCFIRSTB","IGL","INDHOTEL",
    "INDUSINDBK","INDUSTOWER","IOC","IRCTC","JINDALSTEL","JUBLFOOD","LTIM","LUPIN","MRF","MUTHOOTFIN",
    "NAUKRI","NESTLEIND","OBEROIRLTY","PFC","PIDILITIND","PNB","RECLTD","SRF","TATACONSUM","TATAMOTORS",
    "TATAPOWER","TRENT","TVSMOTOR","ULTRACEMCO","VOLTAS","YESBANK"
]

# =========================================================
# INDICATORS & LOGIC
# =========================================================
def get_v24_signals(stock, raw_data):
    try:
        ticker = stock + ".NS"
        df = raw_data[ticker].dropna().copy()
        if len(df) < 30: return []

        # EMA 21
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

        # VWAP
        df['PV'] = df['Close'] * df['Volume']
        df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))

        # Volume Analysis (Big Volume = 2x Average)
        df['AvgVol'] = df['Volume'].rolling(20).mean()
        df['BigVol'] = df['Volume'] > (df['AvgVol'] * 2)

        # Timezone
        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        results = []
        # Last 10 Days only for Backtest
        ten_days_ago = (datetime.now(IST) - timedelta(days=10)).date()
        df = df[df.index.date >= ten_days_ago]

        for i in range(1, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]

            # BUY: EMA21 crosses above VWAP + Big Volume
            buy_signal = (prev['EMA21'] <= prev['VWAP']) and (row['EMA21'] > row['VWAP']) and row['BigVol']
            
            # SELL: EMA21 crosses below VWAP + Big Volume
            sell_signal = (prev['EMA21'] >= prev['VWAP']) and (row['EMA21'] < row['VWAP']) and row['BigVol']

            if buy_signal or sell_signal:
                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": "BIG BUY" if buy_signal else "BIG SELL",
                    "PRICE": round(row['Close'], 2),
                    "VOLUME": int(row['Volume']),
                    "VOL_SHOCK": "YES" if row['BigVol'] else "NO"
                })
        return results
    except: return []

# =========================================================
# EXCEL HELPER
# =========================================================
def convert_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Signals')
    return output.getvalue()

# =========================================================
# UI DATA LOADING
# =========================================================
@st.cache_data(ttl=600)
def fetch_data_bulk():
    tickers = [s + ".NS" for s in nifty_200]
    return yf.download(tickers, period="1mo", interval="15m", group_by="ticker", auto_adjust=True)

all_data = fetch_data_bulk()

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 10-DAY BACKTEST EXCEL"])

with tab1:
    if st.button("🔥 RUN EMA-VWAP SCAN"):
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_v24_signals, s, all_data) for s in nifty_200]
            for f in futures:
                # Only take the latest signal for Live Scanner
                res = f.result()
                if res: results.append(res[-1])
        
        if results:
            df_live = pd.DataFrame(results)
            st.success(f"Found {len(df_live)} Big Momentum Signals")
            st.dataframe(df_live, use_container_width=True)
            
            excel_data = convert_to_excel(df_live)
            st.download_button("📥 Download Live Excel", excel_data, "Live_Signals.xlsx")
        else:
            st.warning("No Crossover with Big Volume found right now.")

with tab2:
    st.write("గత 10 రోజుల డేటాలో వచ్చిన అన్ని క్రాస్ఓవర్ సిగ్నల్స్ ఇక్కడ కనిపిస్తాయి.")
    if st.button("📈 GENERATE 10-DAY REPORT"):
        bt_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_v24_signals, s, all_data) for s in nifty_200]
            for f in futures: bt_results.extend(f.result())
        
        if bt_results:
            df_bt = pd.DataFrame(bt_results)
            st.dataframe(df_bt.sort_values("DATE", ascending=False), use_container_width=True)
            
            bt_excel = convert_to_excel(df_bt)
            st.download_button("📥 Download 10-Day Backtest Excel", bt_excel, "Backtest_10Days.xlsx")
        else:
            st.error("No signals found in the last 10 days.")
