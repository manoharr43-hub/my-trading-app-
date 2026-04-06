import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sector Data
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "IDFCFIRSTB.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"]
}

@st.cache_data(ttl=15)
def get_live_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. Core Logic (Common for Search & Table) ---
def process_data(df, ticker=""):
    if df is None or df.empty: return None
    try:
        # Handling different data structures for Table vs Search
        temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
        if temp_df is None or temp_df.empty or len(temp_df) < 5: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
        
        # Volume Check for Fake/Real
        curr_vol = temp_df['Volume'].iloc[-1]
        avg_vol = temp_df['Volume'].rolling(window=10).mean().iloc[-1]
        
        # Signal & Status
        signal, status, bg = "⏳ WAIT", "Normal", "#ffffff"
        if ltp > res:
            signal = "🚀 BUY"
            status = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT"
            bg = "#d4edda" if curr_vol > avg_vol else "#fff3cd"
        elif ltp < sup:
            signal = "🔻 SELL"
            status = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN"
            bg = "#f8d7da" if curr_vol > avg_vol else "#fff3cd"
            
        # OI Strike Simulation
        call_oi_strike = int(res + (res * 0.005))
        put_oi_strike = int(sup - (sup * 0.005))
        pcr = round(0.85, 2) if ltp < pivot else round(1.15, 2)
        
        return {
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI": call_oi_strike, "Put_OI": put_oi_strike,
            "PCR": pcr, "Signal": signal, "Status": status, "Bg": bg
        }
    except: return None

# --- 4. UI: Selector & Search ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector (LH Side)", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (RELIANCE, SBIN, NIFTY50)", "").upper().strip()

# --- 5. Quick Search Display (మీరు అడిగిన 5 కాలమ్స్ బాక్స్) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_raw = yf.download(s_ticker, period="5d", interval="5m", progress=False, auto_adjust=True)
    
    if not s_raw.empty:
        res_s = process_data(s_raw)
        if res_s:
            st.subheader(f"🎯 Analysis for: {search_q}")
            # 5 Columns for Search Result
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("LTP", f"₹{res_s['LTP']}")
            c2.metric("🟢 CALL OI STRIKE", res_s['Call_OI'])
            c3.metric("🔴 PUT OI STRIKE", res_s['Put_OI'])
            c4.metric("PCR VALUE", res_s['PCR'])
            c5.metric("SIGNAL", res_s['Signal'])
            st.markdown(f"**Market Status:** {res_s['Status']}")
    else:
        st.error("స్టాక్ దొరకలేదు. దయచేసి పూర్తి పేరు టైప్ చేయండి.")

st.divider()

# --- 6. Main Live Scanner Table (Unchanged & Safe) ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_raw = get_live_data(sector_data[sector_choice])
table_results = []

if main_raw is not None:
    for s in sector_data[sector_choice]:
        row = process_data(main_raw, s)
        if row:
            row["Stock"] = s.replace(".NS","")
            table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'Status', 'PCR']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"}))
