import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# 1. Page Config & Auto-refresh (15 Seconds for stability)
st.set_page_config(page_title="Variety Motors SM Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Individual Sectors
sector_data = {
    "Nifty 50 Stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
    "Bank Nifty Stocks": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Fin Nifty Stocks": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS", "BAJFINANCE.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

# 3. Faster Data Engine with Caching
@st.cache_data(ttl=15)
def get_sm_pro_data(stock_list):
    try:
        # RSI కోసం 20 రోజుల డేటా అవసరం
        data = yf.download(stock_list, period="20d", interval="15m", group_by='ticker', threads=True, progress=False)
        return data
    except: return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_live_scan(stock_list):
    results = []
    data = get_sm_pro_data(stock_list)
    if data is None or data.empty:
        st.info("🔄 డేటా లోడ్ అవుతోంది... దయచేసి 15 సెకన్లు ఆగండి.")
        return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 20: continue
            
            # --- Calculations ---
            ltp = round(float(df['Close'].iloc[-1]), 1)
            
            # Support/Resistance
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 1)
            sup = round((2 * pivot) - high, 1)

            # Volume & RSI
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            rsi_val = calculate_rsi(df['Close']).iloc[-1]
            
            # --- SM Pro Signal Logic ---
            status = "⏳ Neutral"
            bg_color = "#ffffff" 
            text_color = "black"

            if ltp > res and curr_vol > (avg_vol * 1.5) and rsi_val > 60:
                status = "🔥 STRONG BUY"
                bg_color = "#1e7e34" # Dark Green
                text_color = "white"
            elif ltp > res:
                status = "🚀 Buy Side"
                bg_color = "#d4edda"
            elif ltp < sup and curr_vol > (avg_vol * 1.5) and rsi_val < 40:
                status = "💥 STRONG SELL"
                bg_color = "#bd2130" # Dark Red
                text_color = "white"
            elif ltp < sup:
                status = "🔻 Sell Side"
                bg_color = "#f8d7da"

            results.append({
                "Stock (LH Side)": s.replace(".NS",""),
                "LTP": ltp,
                "Support (Blue)": sup,
                "Resistance (Red)": res,
                "RSI": round(rsi_val, 1),
                "Signal (SM Pro)": status,
                "Bg": bg_color,
                "Text": text_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg', 'Text']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}; color: {df_final.loc[x.name, 'Text']}"] * len(x), axis=1)
            .set_properties(subset=['Support (Blue)'], **{'color': 'blue', 'font-weight': 'bold'})
            .set_properties(subset=['Resistance (Red)'], **{'color': 'red', 'font-weight': 'bold'})
        )

# Sidebar & Execution
sector_choice = st.sidebar.selectbox("Select Sector", list(sector_data.keys()))
st.title(f"⚡ Variety Motors SM Pro Scanner: {sector_choice}")
run_live_scan(sector_data[sector_choice])
