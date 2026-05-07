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
st.set_page_config(page_title="🚀 NSE AI V27 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# NIFTY 50 STATUS (FIXED LOGIC)
# =========================================================
def get_nifty_summary():
    try:
        # నిఫ్టీ డేటా కోసం ^NSEI ఇండెక్స్
        nifty = yf.Ticker("^NSEI").history(period="2d")
        if len(nifty) >= 2:
            last_close = nifty['Close'].iloc[-1]
            prev_close = nifty['Close'].iloc[-2]
            change = last_close - prev_close
            pct = (change / prev_close) * 100
            color = "#22c55e" if change >= 0 else "#ef4444"
            status = "POSITIVE" if change >= 0 else "NEGATIVE"
            return f"<div style='text-align:center; padding:15px; border-radius:10px; background-color:{color}; color:white;'><h2>NIFTY 50: {status} ({pct:.2f}%)</h2></div>"
        return "<div style='text-align:center; padding:15px; background-color:#334155; color:white;'><h2>NIFTY 50: MARKET REFRESHING...</h2></div>"
    except:
        return "<div style='text-align:center; padding:15px; background-color:#334155; color:white;'><h2>NIFTY 50: DATA BUSY</h2></div>"

st.markdown(get_nifty_summary(), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# NIFTY 200 LIST
# =========================================================
nifty_200 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "AXISBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "ZOMATO",
    "TATASTEEL", "ADANIENT", "ADANIPORTS", "ADANIPOWER", "BEL", "BHEL", "BPCL", "COALINDIA", "DLF", "GAIL",
    "HCLTECH", "HINDALCO", "JSWSTEEL", "M&M", "MARUTI", "NTPC", "ONGC", "SUNPHARMA", "TECHM", "TITAN", "WIPRO"
] # Need more? Add from previous list.

# =========================================================
# EXCEL DOWNLOAD FUNCTION
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
    return output.getvalue()

# =========================================================
# CORE SCANNER LOGIC
# =========================================================
def run_v27_engine(stock, raw_data, target_date=None):
    try:
        ticker = stock + ".NS"
        df = raw_data[ticker].dropna().copy()
        if len(df) < 50: return []

        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['PV'] = df['Close'] * df['Volume']
        df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))
        
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()

        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        # Filter by Target Date
        analysis_df = df[df.index.date == target_date]
        
        results = []
        for i in range(1, len(analysis_df)):
            row = analysis_df.iloc[i]
            prev = analysis_df.iloc[i-1]
            
            is_green = row['Close'] > row['Open']
            is_red = row['Close'] < row['Open']

            buy_sig = (prev['EMA21'] <= prev['VWAP']) and (row['EMA21'] > row['VWAP']) and is_green
            sell_sig = (prev['EMA21'] >= prev['VWAP']) and (row['EMA21'] < row['VWAP']) and is_red

            if buy_sig or sell_sig:
                entry = round(float(row['Close']), 2)
                atr = float(row['ATR'])
                sl = round(entry - (atr * 1.5), 2) if buy_sig else round(entry + (atr * 1.5), 2)
                tgt = round(entry + (atr * 3), 2) if buy_sig else round(entry - (atr * 3), 2)

                # Target/SL simulation
                status = "⏳ OPEN"
                future = analysis_df.iloc[i+1 : i+15]
                for _, f in future.iterrows():
                    if buy_sig:
                        if f['High'] >= tgt: status = "✅ TARGET HIT"; break
                        if f['Low'] <= sl: status = "❌ SL HIT"; break
                    else:
                        if f['Low'] <= tgt: status = "✅ TARGET HIT"; break
                        if f['High'] >= sl: status = "❌ SL HIT"; break

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": "BUY" if buy_sig else "SELL",
                    "ENTRY": entry,
                    "SL": sl,
                    "TGT": tgt,
                    "STATUS": status
                })
        return results
    except: return []

# =========================================================
# UI TABS
# =========================================================
@st.cache_data(ttl=300)
def fetch_bulk():
    return yf.download([s+".NS" for s in nifty_200], period="1mo", interval="15m", group_by="ticker", auto_adjust=True)

all_data = fetch_bulk()

tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 DATE-WISE BACKTEST"])

with tab1:
    if st.button("🔥 RUN TODAY'S LIVE SCAN"):
        results = []
        for s in nifty_200:
            res = run_v27_engine(s, all_data, now.date())
            if res: results.append(res[-1])
        
        if results:
            df_live = pd.DataFrame(results)
            st.dataframe(df_live, use_container_width=True)
            st.download_button("📥 Download Live Scanner Excel", to_excel(df_live), f"Live_Scanner_{now.date()}.xlsx")
        else:
            st.info("No crossover signals found today.")

with tab2:
    selected_date = st.date_input("Select Date for Backtest:", now.date() - timedelta(days=1))
    if st.button("📈 RUN BACKTEST FOR SELECTED DATE"):
        bt_results = []
        for s in nifty_200:
            bt_results.extend(run_v27_engine(s, all_data, selected_date))
        
        if bt_results:
            df_bt = pd.DataFrame(bt_results)
            st.dataframe(df_bt, use_container_width=True)
            st.download_button("📥 Download Backtest Excel", to_excel(df_bt), f"Backtest_{selected_date}.xlsx")
            
            wins = len(df_bt[df_bt['STATUS'] == "✅ TARGET HIT"])
            losses = len(df_bt[df_bt['STATUS'] == "❌ SL HIT"])
            st.success(f"Results for {selected_date}: Wins: {wins} | Losses: {losses}")
        else:
            st.warning(f"No signals found for {selected_date}.")
