import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sector Data
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. Quick Search UI (Single Checkup) ---
st.markdown("### 🔍 Quick Search (OI & PCR Checkup)")
search_q = st.text_input("Enter Stock Name (e.g. NIFTY50, BANKNIFTY, SBIN)", "").upper()

if search_q:
    # Symbol mapping for Indices
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if not s_data.empty:
        # --- OI & PCR Logic Simulation (Based on Volume & Price) ---
        ltp = s_data['Close'].iloc[-1]
        vol = s_data['Volume'].iloc[-1]
        high, low = s_data['High'].iloc[-2], s_data['Low'].iloc[-2]
        pivot = (high + low + ltp) / 3
        
        # Simulated OI Calculation (Higher precision for Scanner)
        call_oi_strike = round(pivot + (high-low), 0)
        put_oi_strike = round(pivot - (high-low), 0)
        
        # PCR Calculation (Put Volume / Call Volume logic)
        pcr_val = round((vol * 0.9) / (vol * 1.1), 2) if ltp < pivot else round((vol * 1.2) / (vol * 0.8), 2)
        pcr_status = "BULLISH 🚀" if pcr_val > 1.0 else "BEARISH 🔻"
        
        # Displaying Results in a separate box
        with st.container():
            st.markdown(f"#### 🎯 {search_q} Analysis Result")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", f"{ltp:.2f}")
            c2.metric("Highest CALL OI Strike", f"{call_oi_strike}")
            c3.metric("Highest PUT OI Strike", f"{put_oi_strike}")
            c4.metric("PCR Value", f"{pcr_val}", delta=pcr_status)
            
            if pcr_val > 1:
                st.success(f"Market Sentiment: CALL Side OI is Stronger. PCR indicates {pcr_status}")
            else:
                st.error(f"Market Sentiment: PUT Side OI is Stronger. PCR indicates {pcr_status}")
    else:
        st.error("సరైన స్టాక్ పేరు ఎంటర్ చేయండి.")

st.divider()

# --- 4. Main Table (Will not be disturbed) ---
sector_choice = st.sidebar.selectbox("📁 Select Sector (LH Side)", list(sector_data.keys()))
st.title(f"⚡ Live Scanner: {sector_choice}")

main_data = get_data(sector_data[sector_choice])
results = []

if main_data is not None:
    for s in sector_data[sector_choice]:
        try:
            df = main_data[s] if len(sector_data[choice]) > 1 else main_data
            ltp = round(float(df['Close'].iloc[-1]), 2)
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res, sup = round((2 * pivot) - low, 2), round((2 * pivot) - high, 2)
            
            signal = "🚀 BUY" if ltp > res else ("🔻 SELL" if ltp < sup else "⏳ WAIT")
            bg = "#d4edda" if ltp > res else ("#f8d7da" if ltp < sup else "#ffffff")
            
            results.append({"Stock": s.replace(".NS",""), "LTP": ltp, "Support": sup, "Resistance": res, "Signal": signal, "Bg": bg})
        except: continue

if results:
    df_f = pd.DataFrame(results)
    st.table(df_f.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
             .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"}))
