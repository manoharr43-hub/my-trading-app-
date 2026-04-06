import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. పేజీ సెటప్
st.set_page_config(page_title="SMC Pro Max Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. సెక్టార్లు
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_smc_data(stock_list):
    try:
        return yf.download(stock_list, period="20d", interval="15m", group_by='ticker', threads=True, progress=False)
    except: return None

# RSI లెక్కించడానికి సొంత ఫార్ములా
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_smc_scanner(stock_list):
    results = []
    data = get_smc_data(stock_list)
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 20: continue
            
            # --- ఇండికేటర్ల లెక్కలు ---
            ltp = round(df['Close'].iloc[-1], 2)
            ema9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
            ema21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
            ema50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            rsi_val = calculate_rsi(df['Close']).iloc[-1]
            vol_ma = df['Volume'].rolling(window=20).mean().iloc[-1]
            
            # Trend & Strength
            trend = "BULL" if ltp > ema50 else "BEAR"
            vol_stat = "STRNG" if df['Volume'].iloc[-1] > vol_ma else "WEAK"
            
            # Signal Logic
            signal = "WAIT"
            bg = "#ffffff"
            if trend == "BULL" and rsi_val > 60:
                signal = "🔥 STRONG BUY"
                bg = "#d4edda"
            elif trend == "BEAR" and rsi_val < 40:
                signal = "💥 STRONG SELL"
                bg = "#f8d7da"

            results.append({
                "Stock": s.replace(".NS",""),
                "Trend": trend,
                "Vol": vol_stat,
                "RSI": round(rsi_val, 0),
                "EMA": "UP" if ema9 > ema21 else "DOWN",
                "LTP": ltp,
                "Signal": signal,
                "Bg": bg
            })
        except: continue

    if results:
        df_f = pd.DataFrame(results)
        st.table(df_f.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1))

# UI
sector_choice = st.sidebar.selectbox("📁 Select Sector", list(sector_data.keys()))
st.title(f"🚀 SMC Pro Max 8-Col Scanner: {sector_choice}")
run_smc_scanner(sector_data[sector_choice])
