import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. NSE All Sectors (LH Side)
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

def process_logic(s, df):
    if df is None or df.empty: return None
    try:
        temp_df = df[s] if isinstance(df.columns, pd.MultiIndex) and s in df.columns.levels[0] else df
        if temp_df.empty: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high + low + close) / 3
        res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
        
        # Volume Analysis (Fake/Real)
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

        # OI Strikes & PCR Simulation
        call_strike = round(res + (res * 0.005), 0)
        put_strike = round(sup - (sup * 0.005), 0)
        pcr = round(0.8, 2) if ltp < pivot else round(1.2, 2)
        
        return {
            "Stock": s.replace(".NS","").replace("^",""),
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI": int(call_strike), "Put_OI": int(put_strike),
            "PCR": pcr, "Signal": signal, "Status": status, "Bg": bg
        }
    except: return None

# --- UI Header ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector (LH Side)", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (NIFTY50, BANKNIFTY, SBIN, etc.)", "").upper()

# --- 3. Quick Search Result (మీ కండిషన్స్ ఇక్కడ ఉన్నాయి) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if not s_data.empty:
        res = process_logic(s_ticker, s_data)
        if res:
            st.subheader(f"🎯 Analysis Result: {search_q}")
            # విడివిడి కాలమ్స్ లో OI స్ట్రైక్స్
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("LTP", f"₹{res['LTP']}")
                st.write(f"**Signal:** {res['Signal']}")
            with c2:
                st.metric("🟢 CALL OI STRIKE", res['Call_OI'])
                st.write(f"**Status:** {res['Status']}")
            with c3:
                st.metric("🔴 PUT OI STRIKE", res['Put_OI'])
                st.write(f"**PCR:** {res['PCR']}")
            with c4:
                pcr_text = "BULLISH 🚀" if res['PCR'] > 1 else "BEARISH 🔻"
                st.metric("OVERALL STRENGTH", pcr_text)
        else: st.warning("డేటా లోడ్ అవ్వలేదు.")
    else: st.error("సరైన పేరు టైప్ చేయండి.")

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
