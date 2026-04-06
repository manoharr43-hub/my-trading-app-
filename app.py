import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sector Data
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

def process_stock(s, df):
    if df is None or df.empty: return None
    try:
        temp_df = df[s] if isinstance(df.columns, pd.MultiIndex) and s in df.columns.levels[0] else df
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)

        # --- Volume Analysis for Fake/Real Check ---
        curr_vol = temp_df['Volume'].iloc[-1]
        avg_vol = temp_df['Volume'].rolling(window=10).mean().iloc[-1]
        is_high_vol = curr_vol > avg_vol

        # --- Buy/Sell & Fake/Real Logic ---
        signal = "⏳ WAIT"
        bo_type = "Normal"
        bg = "#ffffff"

        if ltp > res:
            signal = "🚀 BUY"
            if not is_high_vol:
                bo_type = "⚠️ FAKE BREAKOUT"
                bg = "#fff3cd" # Yellow for Warning
            else:
                bo_type = "✅ REAL BREAKOUT"
                bg = "#d4edda" # Green for Real
        elif ltp < sup:
            signal = "🔻 SELL"
            if not is_high_vol:
                bo_type = "⚠️ FAKE BREAKDOWN"
                bg = "#fff3cd" # Yellow
            else:
                bo_type = "✅ REAL BREAKDOWN"
                bg = "#f8d7da" # Red for Real

        strength = "BULLISH 🚀" if ltp > pivot else "BEARISH 🔻"
        
        return {
            "Stock": s.replace(".NS",""),
            "LTP": ltp, 
            "Support": sup, 
            "Resistance": res,
            "Signal": signal,
            "Breakout Status": bo_type, # కొత్త కాలమ్
            "Strength": strength, 
            "Bg": bg
        }
    except: return None

# --- UI Layout ---
col_lh, col_rh = st.columns([2, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Search Stock Name", "").upper()

st.divider()

# --- 4. Main Table ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_data = get_data(sector_data[sector_choice])
results = []
if main_data is not None:
    for s in sector_data[sector_choice]:
        row = process_stock(s, main_data)
        if row: results.append(row)

if results:
    df_f = pd.DataFrame(results)
    # అన్ని కాలమ్స్ నీట్‌గా అమర్చాను
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'Breakout Status', 'Strength']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"})
    )
