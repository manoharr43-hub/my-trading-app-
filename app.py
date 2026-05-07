import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG & TIMEZONE
# =========================================================
st.set_page_config(page_title="🚀 NSE AI QUANT V15.3 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(f'<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V15.3</h1>', unsafe_allow_html=True)
st.markdown(f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | Strategy: EMA 21 + Excel Export</h4>', unsafe_allow_html=True)

# =========================================================
# INDICATORS ENGINE
# =========================================================
def get_indicators(df):
    df = df.copy()
    if len(df) < 40: return pd.DataFrame()

    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()

    df['VOLAVG'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VOLAVG'] + 1e-9)
    df['BODY'] = abs(df['Close'] - df['Open'])
    df['BODY_AVG'] = df['BODY'].rolling(10).mean()

    return df

# =========================================================
# STOCKS LIST
# =========================================================
stocks = ["ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
          "ABCAPITAL","ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT",
          "AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL",
          "CANBK","CIPLA","COALINDIA","DLF","DRREDDY","GAIL","HDFCBANK","HCLTECH","HINDALCO",
          "ICICIBANK","INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC","ONGC",
          "RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO","ZOMATO"]

@st.cache_data(ttl=300)
def fetch_data():
    tickers = [s + ".NS" for s in stocks]
    data = yf.download(tickers, period="7d", interval="15m", auto_adjust=True, group_by='ticker', progress=False)
    return data

data_pool = fetch_data()

# =========================================================
# SCAN LOGIC WITH P&L
# =========================================================
def scan(stock, mode="TODAY"):
    try:
        ticker = stock + ".NS"
        df = get_indicators(data_pool[ticker].dropna())
        if df.empty: return []
        df.index = df.index.tz_convert(IST)
        
        scan_df = df[df.index.date == now.date()] if mode == "TODAY" else df

        results = []
        for i in range(2, len(scan_df)):
            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]

            big_player = (row['RVOL'] > 2.0 and row['BODY'] > (1.5 * row['BODY_AVG']))
            pb_buy = (prev['Low'] > prev['EMA21'] and row['Low'] <= row['EMA21'] and row['Close'] > row['EMA21'])
            pb_sell = (prev['High'] < prev['EMA21'] and row['High'] >= row['EMA21'] and row['Close'] < row['EMA21'])

            buy_sig = (row['EMA9'] > row['EMA21'] and row['Close'] > row['VWAP'] and (big_player or pb_buy) and row['RSI'] > 52)
            sell_sig = (row['EMA9'] < row['EMA21'] and row['Close'] < row['VWAP'] and (big_player or pb_sell) and row['RSI'] < 48)

            if buy_sig or sell_sig:
                signal = "BUY" if buy_sig else "SELL"
                price = round(row['Close'], 2)
                risk = row['ATR'] * 1.5
                sl = round(price - risk, 2) if buy_sig else round(price + risk, 2)
                tgt = round(price + (risk * 2), 2) if buy_sig else round(price - (risk * 2), 2)

                status = "OPEN"
                pnl = 0.0
                if mode == "BACKTEST":
                    future_data = scan_df.iloc[i+1 : i+25] 
                    for _, f_row in future_data.iterrows():
                        if buy_sig:
                            if f_row['High'] >= tgt: status = "🎯 TGT DONE"; pnl = round(tgt - price, 2); break
                            elif f_row['Low'] <= sl: status = "🛑 SL HIT"; pnl = round(sl - price, 2); break
                        else:
                            if f_row['Low'] <= tgt: status = "🎯 TGT DONE"; pnl = round(price - tgt, 2); break
                            elif f_row['High'] >= sl: status = "🛑 SL HIT"; pnl = round(price - sl, 2); break

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": signal,
                    "PRICE": price,
                    "SL": sl,
                    "TGT": tgt,
                    "RESULT": status,
                    "P&L": pnl,
                    "TYPE": "🚀 BIG" if big_player else "🔄 PB"
                })
        return results
    except: return []

# =========================================================
# EXCEL HELPER
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='NSE_AI_Signals')
    return output.getvalue()

# =========================================================
# UI TABS
# =========================================================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST REPORT"])

with tab1:
    if st.button("🚀 RUN TODAY SCAN"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res = list(exec.map(lambda s: scan(s, "TODAY"), stocks))
        flat = [i for s in res for i in s]
        if flat:
            df_today = pd.DataFrame(flat).drop_duplicates('STOCK', keep='last').sort_values('TIME', ascending=False)
            st.dataframe(df_today, use_container_width=True)
            # Excel Download for Scanner
            excel_data = to_excel(df_today)
            st.download_button(label="📥 Download Today Excel", data=excel_data, file_name=f"Today_Signals_{now.strftime('%Y%m%d')}.xlsx")
        else: st.warning("No signals for today.")

with tab2:
    if st.button("📊 RUN 5-DAY BACKTEST"):
        with ThreadPoolExecutor(max_workers=15) as exec:
            res_bt = list(exec.map(lambda s: scan(s, "BACKTEST"), stocks))
        flat_bt = [i for s in res_bt for i in s]
        if flat_bt:
            df_bt = pd.DataFrame(flat_bt).sort_values(['DATE', 'TIME'], ascending=False)
            
            win_count = len(df_bt[df_bt['RESULT'] == "🎯 TGT DONE"])
            loss_count = len(df_bt[df_bt['RESULT'] == "🛑 SL HIT"])
            
            st.subheader("Performance Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Signals", len(df_bt))
            c2.metric("Wins / Losses", f"{win_count} ✅ / {loss_count} ❌")
            c3.metric("Total P&L Points", f"{round(df_bt['P&L'].sum(), 2)} pts")

            st.dataframe(df_bt, use_container_width=True)
            # Excel Download for Backtest
            excel_bt = to_excel(df_bt)
            st.download_button(label="📥 Download Backtest Excel", data=excel_bt, file_name="Backtest_Full_Report.xlsx")
        else: st.info("No backtest data found.")
