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
st.set_page_config(page_title="🚀 NSE AI V26 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# NIFTY 50 STATUS (TOP BOX)
# =========================================================
def get_nifty_status():
    try:
        nifty = yf.download("^NSEI", period="2d", interval="1m", progress=False)
        last_price = nifty['Close'].iloc[-1]
        prev_close = nifty['Close'].iloc[-2]
        change = last_price - prev_close
        pct_change = (change / prev_close) * 100
        color = "#22c55e" if change >= 0 else "#ef4444"
        status = "POSITIVE" if change >= 0 else "NEGATIVE"
        return f"<div style='text-align:center; padding:10px; border-radius:10px; background-color:{color}; color:white;'><h3>NIFTY 50: {status} ({pct_change:.2f}%)</h3></div>"
    except:
        return "<div style='text-align:center; padding:10px; background-color:#334155; color:white;'><h3>NIFTY 50: DATA BUSY</h3></div>"

st.markdown(get_nifty_status(), unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# STOCK LIST (NIFTY 200)
# =========================================================
nifty_200 = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "AXISBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "ZOMATO", "TATASTEEL", "ADANIENT"] # Add more as needed

# =========================================================
# CORE ENGINE V26
# =========================================================
def run_v26_analysis(stock, raw_data, mode="TODAY"):
    try:
        ticker = stock + ".NS"
        df = raw_data[ticker].dropna().copy()
        if len(df) < 50: return []

        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['PV'] = df['Close'] * df['Volume']
        df['VWAP'] = (df.groupby(df.index.date)['PV'].cumsum() / (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9))
        
        # Risk Management (ATR)
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()

        if df.index.tz is None: df.index = df.index.tz_localize("UTC")
        df.index = df.index.tz_convert(IST)

        analysis_df = df[df.index.date >= (now - timedelta(days=10)).date()] if mode == "BACKTEST" else df[df.index.date == df.index.date.max()]

        results = []
        for i in range(1, len(analysis_df)):
            row = analysis_df.iloc[i]
            prev = analysis_df.iloc[i-1]

            # Logic: Cross + Candle Color Check
            is_green = row['Close'] > row['Open']
            is_red = row['Close'] < row['Open']

            buy_sig = (prev['EMA21'] <= prev['VWAP']) and (row['EMA21'] > row['VWAP']) and is_green
            sell_sig = (prev['EMA21'] >= prev['VWAP']) and (row['EMA21'] < row['VWAP']) and is_red

            if buy_sig or sell_sig:
                entry = round(row['Close'], 2)
                sl = round(entry - (row['ATR'] * 1.5), 2) if buy_sig else round(entry + (row['ATR'] * 1.5), 2)
                tgt = round(entry + (row['ATR'] * 3), 2) if buy_sig else round(entry - (row['ATR'] * 3), 2)

                # Backtest Outcome
                status = "⏳ OPEN"
                future_data = analysis_df.iloc[i+1 : i+15] # Next 15 candles
                for _, frow in future_data.iterrows():
                    if buy_sig:
                        if frow['High'] >= tgt: status = "✅ TARGET HIT"; break
                        if frow['Low'] <= sl: status = "❌ SL HIT"; break
                    else:
                        if frow['Low'] <= tgt: status = "✅ TARGET HIT"; break
                        if frow['High'] >= sl: status = "❌ SL HIT"; break

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
@st.cache_data(ttl=600)
def fetch_data():
    return yf.download([s+".NS" for s in nifty_200], period="1mo", interval="15m", group_by="ticker", auto_adjust=True)

data_pool = fetch_data()

t1, t2 = st.tabs(["🔍 LIVE SIGNALS", "📊 BACKTEST REPORT"])

def style_df(df):
    def color_signal(val):
        if val == "BUY": return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
        if val == "SELL": return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
        return ''
    
    def color_status(val):
        if "TARGET" in str(val): return 'color: #22c55e; font-weight: bold;'
        if "SL" in str(val): return 'color: #ef4444; font-weight: bold;'
        return ''

    return df.style.applymap(color_signal, subset=['SIGNAL']).applymap(color_status, subset=['STATUS'])

with t1:
    if st.button("RUN LIVE SCANNER"):
        live_res = []
        for s in nifty_200:
            res = run_v26_analysis(s, data_pool, "TODAY")
            if res: live_res.append(res[-1])
        
        if live_res:
            st.dataframe(style_df(pd.DataFrame(live_res)), use_container_width=True)
        else:
            st.info("No Crossover signals found with required candle color.")

with t2:
    if st.button("RUN 10-DAY BACKTEST"):
        bt_res = []
        for s in nifty_200:
            bt_res.extend(run_v26_analysis(s, data_pool, "BACKTEST"))
        
        if bt_res:
            bt_df = pd.DataFrame(bt_res).sort_values("DATE", ascending=False)
            st.dataframe(style_df(bt_df), use_container_width=True)
            
            # Summary Metrics
            wins = len(bt_df[bt_df['STATUS'] == "✅ TARGET HIT"])
            losses = len(bt_df[bt_df['STATUS'] == "❌ SL HIT"])
            st.success(f"Backtest Summary: Wins: {wins} | Losses: {losses} | Win Rate: {(wins/(wins+losses)*100 if wins+losses > 0 else 0):.2f}%")
        else:
            st.warning("No backtest data available.")
