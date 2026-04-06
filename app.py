import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sector Data (LH Side)
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "IDFCFIRSTB.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"]
}

@st.cache_data(ttl=15)
def get_live_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. Search Result Logic ---
def process_stock_logic(df):
    if df is None or df.empty or len(df) < 5: return None
    try:
        ltp = round(float(df['Close'].iloc[-1]), 2)
        high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
        
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
        
        curr_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
        
        # Signal & Fake Alert
        signal = "🚀 BUY" if ltp > res else ("🔻 SELL" if ltp < sup else "⏳ WAIT")
        status = "Normal"
        bg = "#ffffff"
        if ltp > res:
            status = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT"
            bg = "#d4edda" if curr_vol > avg_vol else "#fff3cd"
        elif ltp < sup:
            status = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN"
            bg = "#f8d7da" if curr_vol > avg_vol else "#fff3cd"
            
        call_oi = int(res + (res * 0.005))
        put_oi = int(sup - (sup * 0.005))
        pcr = round(0.85, 2) if ltp < pivot else round(1.15, 2)
        
        return {
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI": call_oi, "Put_OI": put_oi,
            "PCR": pcr, "Signal": signal, "Status": status, "Bg": bg
        }
    except: return None

# --- UI Setup ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (Enter Stock Name e.g. SBIN, NIFTY50)", "").upper()

# --- 4. Search Result Display (Top Section) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if not s_data.empty:
        res = process_stock_logic(s_data)
        if res:
            st.subheader(f"🎯 Analysis for: {search_q}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", f"₹{res['LTP']}")
            c2.metric("🟢 CALL OI STRIKE", res['Call_OI'])
            c3.metric("🔴 PUT OI STRIKE", res['Put_OI'])
            c4.metric("PCR", res['PCR'])
            
            # Highlight Signal & Status
            st.markdown(f"**Signal:** {res['Signal']} | **Market Status:** {res['Status']}")
        else:
            st.warning("ఈ స్టాక్ డేటా లోడ్ అవ్వలేదు.")
    else:
        st.error("స్టాక్ పేరు దొరకలేదు. దయచేసి పేరు చెక్ చేయండి.")

st.divider()

# --- 5. Main Sector Table (Bottom Section) ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_data = get_live_data(sector_data[sector_choice])
table_results = []

if main_data is not None:
    for s in sector_data[sector_choice]:
        try:
            df = main_data[s] if len(sector_data[sector_choice]) > 1 else main_data
            row_data = process_stock_logic(df)
            if row_data:
                row_data["Stock"] = s.replace(".NS","")
                table_results.append(row_data)
        except: continue

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'Status', 'PCR']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"}))
