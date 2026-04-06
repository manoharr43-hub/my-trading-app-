import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. NSE All Sectors (LH Side కోసం)
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "IDFCFIRSTB.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "Metal Sector": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS"],
    "FMCG": ["ITC.NS", "HINDUNILVR.NS", "BRITANNIA.NS", "NESTLEIND.NS", "DABUR.NS"]
}

@st.cache_data(ttl=15)
def get_live_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

def process_single_stock(s, df):
    if df is None or df.empty: return None
    try:
        # Multi-index check
        temp_df = df[s] if isinstance(df.columns, pd.MultiIndex) and s in df.columns.levels[0] else df
        if temp_df.empty: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
        
        # OI/PCR Simulation logic (Based on Price Action)
        pcr = round(0.85, 2) if ltp < pivot else round(1.15, 2)
        call_oi_strike = round(res + (res * 0.01), 0)
        put_oi_strike = round(sup - (sup * 0.01), 0)
        
        status = "🚀 BUY / CALL SIDE" if ltp > res else ("🔻 SELL / PUT SIDE" if ltp < sup else "⏳ WAIT")
        bg = "#d4edda" if ltp > res else ("#f8d7da" if ltp < sup else "#ffffff")
        
        return {
            "Stock": s.replace(".NS","").replace("^",""),
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI_Strike": call_oi_strike, "Put_OI_Strike": put_oi_strike,
            "PCR": pcr, "Signal": status, "Bg": bg
        }
    except: return None

# --- 3. UI: LH Selector & RH Quick Search ---
col_lh, col_rh = st.columns([1, 1])

with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))

with col_rh:
    search_q = st.text_input("🔍 Quick Search (NIFTY50, BANKNIFTY, etc.)", "").upper()

# --- 4. Search Result Box (పైన విడిగా కనిపించేలా) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if not s_data.empty:
        res = process_single_stock(s_ticker, s_data)
        if res:
            st.subheader(f"🎯 Analysis for {search_q}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", f"₹{res['LTP']}")
            c2.metric("Signal", res['Signal'])
            c3.metric("PCR", res['PCR'])
            c4.metric("Market", "BULLISH" if res['PCR'] > 1 else "BEARISH")
            
            st.info(f"📍 Highest Call OI Strike: **{res['Call_OI_Strike']}** | Highest Put OI Strike: **{res['Put_OI_Strike']}**")
    else:
        st.error("స్టాక్ పేరు దొరకలేదు. ఉదాహరణకు: SBIN లేదా NIFTY50 అని టైప్ చేయండి.")

st.markdown("---")

# --- 5. Main Sector Table ---
st.title(f"⚡ Live Sector Scanner: {sector_choice}")
main_data = get_live_data(sector_data[sector_choice])
table_results = []

if main_data is not None:
    for s in sector_data[sector_choice]:
        row = process_single_stock(s, main_data)
        if row: table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'PCR']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"})
    )
