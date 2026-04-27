import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import io

# =============================
# CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V38", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V38 - FULL TREND REVERSAL SYSTEM")
st.write(f"🕒 **Market Time:** {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","BHARTIARTL",
    "SBIN","ITC","LT","BAJFINANCE","AXISBANK","KOTAKBANK",
    "HCLTECH","MARUTI","SUNPHARMA","TITAN","TATAMOTORS",
    "ULTRACEMCO","ADANIENT","JSWSTEEL","M&M","NTPC","POWERGRID"
]

# =============================
# CORE INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if len(df) < 20: return df
    # Trend Indicators
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    # Strength Indicator
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

@st.cache_data(ttl=60)
def fetch_data(symbols, interval, period):
    tickers = [s + ".NS" for s in symbols]
    try:
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        return data
    except:
        return pd.DataFrame()

data_5m = fetch_data(stocks, "5m", "5d")

# =============================
# EXCEL DOWNLOAD
# =============================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Backtest_Report')
    return output.getvalue()

# =============================
# TABS SETUP
# =============================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 BACKTEST (TREND REVERSAL)"])

# -----------------------------
# TAB 1: LIVE SCANNER
# -----------------------------
with tab1:
    if st.button("RUN SCANNER"):
        live_res = []
        for s in stocks:
            try:
                df = add_indicators(data_5m[s + ".NS"].dropna())
                l = df.iloc[-1]
                dist = abs(l['Close'] - l['EMA20']) / l['EMA20']
                
                if dist < 0.004:
                    action = "None"
                    if l['Close'] > l['VWAP'] and l['Close'] > l['Open']: action = "BUY 🟢"
                    elif l['Close'] < l['VWAP'] and l['Close'] < l['Open']: action = "SELL 🔴"
                    
                    if action != "None":
                        live_res.append({
                            "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
                            "STOCK": s, "ACTION": action, "PRICE": round(l['Close'], 2)
                        })
            except: continue
        if live_res: st.table(pd.DataFrame(live_res))
        else: st.info("No pullback signals found.")

# -----------------------------
# TAB 2: BACKTEST (FULL TREND)
# -----------------------------
with tab2:
    bt_date = st.date_input("Select Date", value=now.date() - timedelta(days=1))
    if st.button("RUN FULL TREND BACKTEST"):
        bt_results = []
        for s in stocks:
            try:
                df = data_5m[s + ".NS"].dropna()
                df.index = df.index.tz_convert(IST)
                df_day = add_indicators(df[df.index.date == bt_date])
                
                if df_day is None or df_day.empty: continue

                last_action = None # చివరి సిగ్నల్ (Buy/Sell) ట్రాక్ చేయడానికి
                last_time = None

                for i in range(15, len(df_day)):
                    row = df_day.iloc[i]
                    curr_time = df_day.index[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
                    
                    if dist < 0.004:
                        curr_action = None
                        if row['Close'] > row['VWAP'] and row['Close'] > row['Open']:
                            curr_action = "BUY 🟢"
                        elif row['Close'] < row['VWAP'] and row['Close'] < row['Open']:
                            curr_action = "SELL 🔴"
                        
                        if curr_action:
                            # ✅ REVERSAL LOGIC: 
                            # 1. ఒకవేళ ట్రెండ్ మారితే (Buy నుండి Sell కి) వెంటనే చూపించు.
                            # 2. అదే ట్రెండ్ కొనసాగితే కనీసం 1 గంట ఆగు (Repeat Rows తగ్గించడానికి).
                            is_reversal = (curr_action != last_action)
                            is_cooldown_over = (last_time and (curr_time - last_time) > timedelta(minutes=60))
                            
                            if is_reversal or is_cooldown_over:
                                bt_results.append({
                                    "TIME": curr_time.strftime('%H:%M'),
                                    "STOCK": s, "TYPE": curr_action, "PRICE": round(row['Close'], 2)
                                })
                                last_action = curr_action
                                last_time = curr_time
            except: continue
            
        if bt_results:
            bt_df = pd.DataFrame(bt_results)
            st.dataframe(bt_df, use_container_width=True)
            st.download_button("📥 Excel Download", data=to_excel(bt_df), file_name=f"Full_Trend_{bt_date}.xlsx")
        else:
            st.warning("No trend signals found for this date.")
