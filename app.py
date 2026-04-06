import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. NSE All Sectors (LH Side)
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
        # Multi-stock download
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

def process_logic(s, df, is_single=False):
    if df is None or df.empty: return None
    try:
        # Single search మరియు Table data రెండింటికీ పని చేసేలా మార్పులు
        if is_single:
            temp_df = df
        else:
            temp_df = df[s] if isinstance(df.columns, pd.MultiIndex) and s in df.columns.levels[0] else df
        
        if temp_df is None or temp_df.empty: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
        
        # Volume Analysis (Fake/Real Check)
        curr_vol = temp_df['Volume'].iloc[-1]
        avg_vol = temp_df['Volume'].rolling(window=10).mean().iloc[-1]
        is_high_vol = curr_vol > avg_vol
        
        # Signal & Status
        signal, status, bg = "⏳ WAIT", "Normal", "#ffffff"
        if ltp > res:
            signal = "🚀 BUY"
            status = "✅ REAL BREAKOUT" if is_high_vol else "⚠️ FAKE BREAKOUT"
            bg = "#d4edda" if is_high_vol else "#fff3cd"
        elif ltp < sup:
            signal = "🔻 SELL"
            status = "✅ REAL BREAKDOWN" if is_high_vol else "⚠️ FAKE BREAKDOWN"
            bg = "#f8d7da" if is_high_vol else "#fff3cd"

        # OI simulation
        call_oi = int(res + (res * 0.005))
        put_oi = int(sup - (sup * 0.005))
        pcr = round(0.85, 2) if ltp < pivot else round(1.15, 2)
        
        return {
            "Stock": s.replace(".NS","").replace("^",""),
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI": call_oi, "Put_OI": put_oi,
            "PCR": pcr, "Signal": signal, "Status": status, "Bg": bg
        }
    except: return None

# --- UI Layout ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (NIFTY50, BANKNIFTY, SBIN, etc.)", "").upper()

# --- 3. Quick Search Fix (ఇప్పుడు డేటా ఖచ్చితంగా లోడ్ అవుతుంది) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    
    # సింగిల్ స్టాక్ కోసం ప్రత్యేక డౌన్లోడ్ (group_by లేకుండా)
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if s_data is not None and not s_data.empty:
        res_data = process_logic(s_ticker, s_data, is_single=True)
        if res_data:
            st.subheader(f"🎯 Search Analysis: {search_q}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", f"₹{res_data['LTP']}")
            c2.metric("🟢 CALL OI STRIKE", res_data['Call_OI'])
            c3.metric("🔴 PUT OI STRIKE", res_data['Put_OI'])
            c4.metric("PCR", res_data['PCR'])
            st.write(f"**Signal:** {res_data['Signal']} | **Status:** {res_data['Status']}")
        else:
            st.warning("ఈ స్టాక్ డేటా ప్రాసెస్ చేయలేకపోతున్నాము.")
    else:
        st.error("డేటా లోడ్ అవ్వలేదు. సరైన పేరు టైప్ చేయండి (e.g. SBIN, NIFTY50).")

st.divider()

# --- 4. Main Sector Table (LH Sector) ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_data = get_live_data(sector_data[sector_choice])
table_results = []

if main_data is not None:
    for s in sector_data[sector_choice]:
        row = process_logic(s, main_data)
        if row: table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'Status', 'PCR']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"})
    )
