import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sectors
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Fin Nifty": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS", "HDFCBANK.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

def process_stock(s, df):
    if df.empty or len(df) < 10: return None
    ltp = round(float(df['Close'].iloc[-1]), 2)
    high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
    pivot = (high + low + close) / 3
    res = round((2 * pivot) - low, 2)
    sup = round((2 * pivot) - high, 2)
    curr_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
    
    status, bg = "⏳ Neutral", "#ffffff"
    if ltp > res:
        status, bg = ("⚠️ FAKE BREAKOUT", "#fff3cd") if curr_vol < avg_vol else ("🚀 BUY / CALL", "#d4edda")
    elif ltp < sup:
        status, bg = ("⚠️ FAKE BREAKDOWN", "#fff3cd") if curr_vol < avg_vol else ("🔻 SELL / PUT", "#f8d7da")
    
    return {"Stock": s.replace(".NS","").replace("^",""), "LTP": ltp, "Support": sup, "Resistance": res, "Signal": status, "Bg": bg}

# --- UI Layout ---
col_lh, col_rh = st.columns([2, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select Sector (LH)", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Search Stock (RH Side)", "").upper()

# --- 3. Search Result (Separate Column/Section) ---
if search_q:
    st.markdown("### 🎯 Search Result")
    s_ticker = search_q if search_q.endswith(".NS") or search_q.startswith("^") else search_q + ".NS"
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    if not s_data.empty:
        res_dict = process_stock(s_ticker, s_data)
        if res_dict:
            # సెర్చ్ చేసిన స్టాక్ ని విడిగా ఒక బాక్స్ లో చూపిస్తున్నాం
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Stock", res_dict['Stock'])
            c2.metric("LTP", res_dict['LTP'])
            c3.metric("Signal", res_dict['Signal'])
            st.info(f"Support: {res_dict['Support']} | Resistance: {res_dict['Resistance']}")
    else:
        st.error("స్టాక్ పేరు సరిగ్గా టైప్ చేయండి (e.g. SBIN)")

st.divider()

# --- 4. Main Sector Table ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_data = get_data(sector_data[sector_choice])
results = []
if main_data is not None:
    for s in sector_data[sector_choice]:
        row = process_stock(s, main_data[s] if len(sector_data[sector_choice]) > 1 else main_data)
        if row: results.append(row)

if results:
    df_f = pd.DataFrame(results)
    st.table(df_f.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
             .set_properties(subset=['Support'], **{'color': 'blue', 'font-weight': 'bold'})
             .set_properties(subset=['Resistance'], **{'color': 'red', 'font-weight': 'bold'})
             .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"}))
