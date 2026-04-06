import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta # ఇండికేటర్ల కోసం ఇది అవసరం
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="SMC Pro Max Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# --- 1. సెక్టార్ డేటా ---
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_smc_data(stock_list):
    return yf.download(stock_list, period="20d", interval="15m", group_by='ticker', threads=True, progress=False)

def run_smc_scanner(stock_list):
    results = []
    data = get_smc_data(stock_list)
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 20: continue
            
            # --- SMC Pro Max Calculations ---
            ltp = round(df['Close'].iloc[-1], 2)
            ema9 = ta.ema(df['Close'], length=9).iloc[-1]
            ema21 = ta.ema(df['Close'], length=21).iloc[-1]
            ema50 = ta.ema(df['Close'], length=50).iloc[-1]
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)['ADX_14'].iloc[-1]
            vol_ma = df['Volume'].rolling(window=20).mean().iloc[-1]
            
            # Trend & Signal Logic
            trend = "BULL" if ltp > ema50 else "BEAR"
            vol_stat = "STRNG" if df['Volume'].iloc[-1] > vol_ma else "WEAK"
            ema_cross = "UP" if ema9 > ema21 else "DOWN"
            
            # Strong Signal Formula (SM Pro Max)
            signal = "WAIT"
            bg = "#ffffff"
            if trend == "BULL" and vol_stat == "STRNG" and rsi > 60:
                signal = "🔥 STRONG BUY"
                bg = "#d4edda" # Green
            elif trend == "BEAR" and vol_stat == "STRNG" and rsi < 40:
                signal = "💥 STRONG SELL"
                bg = "#f8d7da" # Red

            results.append({
                "Stock": s.replace(".NS",""),
                "Trend": trend,
                "Vol": vol_stat,
                "ADX": round(adx, 1),
                "RSI": round(rsi, 0),
                "EMA": ema_cross,
                "LTP": ltp,
                "Signal": signal,
                "Bg": bg
            })
        except: continue

    if results:
        df_f = pd.DataFrame(results)
        # 8 Columns Dashboard Style Display
        st.table(df_f.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1))

# UI
sector_choice = st.sidebar.selectbox("📁 Select Sector", list(sector_data.keys()))
st.title(f"🚀 SMC Pro Max 8-Col Scanner: {sector_choice}")
run_smc_scanner(sector_data[sector_choice])
