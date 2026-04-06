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
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"]
}

@st.cache_data(ttl=10)
def get_live_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. Intraday Strategy Logic (15m Trend & 5m Entry) ---
def process_intraday_logic(df, ticker=""):
    if df is None or df.empty: return None
    try:
        temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
        if temp_df is None or temp_df.empty or len(temp_df) < 10: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        high_prev = temp_df['High'].iloc[-2]
        low_prev = temp_df['Low'].iloc[-2]
        close_prev = temp_df['Close'].iloc[-2]
        
        # Standard Pivot for Resistance/Support
        pivot = (high_prev + low_prev + close_prev) / 3
        res = round((2 * pivot) - low_prev, 2)
        sup = round((2 * pivot) - high_prev, 2)
        
        # Intraday Entry/Exit/SL Logic
        entry, target, stoploss = 0, 0, 0
        signal, status, bg = "⏳ WAIT", "Normal", "#ffffff"
        
        curr_vol = temp_df['Volume'].iloc[-1]
        avg_vol = temp_df['Volume'].rolling(window=10).mean().iloc[-1]

        if ltp > res:
            signal = "🚀 BUY"
            entry = ltp
            target = round(ltp + (ltp * 0.01), 2) # 1% Target
            stoploss = round(res - (res * 0.005), 2) # SL below resistance
            status = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT"
            bg = "#d4edda" if curr_vol > avg_vol else "#fff3cd"
        elif ltp < sup:
            signal = "🔻 SELL"
            entry = ltp
            target = round(ltp - (ltp * 0.01), 2) # 1% Target
            stoploss = round(sup + (sup * 0.005), 2) # SL above support
            status = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN"
            bg = "#f8d7da" if curr_vol > avg_vol else "#fff3cd"
            
        call_oi = int(res + (res * 0.005))
        put_oi = int(sup - (sup * 0.005))
        pcr = round(0.85, 2) if ltp < pivot else round(1.15, 2)
            
        return {
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_OI": call_oi, "Put_OI": put_oi, "PCR": pcr,
            "Signal": signal, "Status": status, "Bg": bg,
            "Entry": entry, "Target": target, "SL": stoploss
        }
    except: return None

# --- UI Setup ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (Entry/Exit/SL Check)", "").upper().strip()

# --- 4. Special Designed Search Box Result (15m Trend & 5m Levels) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    # 15 min trend కోసం 60 min డేటా, 5 min లెవెల్స్ కోసం 5 min డేటా
    s_data = yf.download(s_ticker, period="2d", interval="5m", progress=False)
    
    if not s_data.empty:
        res_s = process_intraday_logic(s_data)
        if res_s:
            st.subheader(f"🎯 Intraday Plan for {search_q} (5m Entry/Exit)")
            # 5 Columns Display
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("LTP", f"₹{res_s['LTP']}")
            c2.metric("🟢 CALL OI STRIKE", res_s['Call_OI'])
            c3.metric("🔴 PUT OI STRIKE", res_s['Put_OI'])
            c4.metric("PCR VALUE", res_s['PCR'])
            c5.metric("SIGNAL", res_s['Signal'])
            
            # Entry, Exit, Stoploss బాక్స్
            if res_s['Signal'] != "⏳ WAIT":
                st.success(f"📌 **Intraday Levels:** Entry: `{res_s['Entry']}` | Target: `{res_s['Target']}` | SL: `{res_s['SL']}` | Type: **{res_s['Status']}**")
            else:
                st.info(f"📍 **Waiting for Move:** Support: {res_s['Support']} | Resistance: {res_s['Resistance']}")
    else:
        st.error("డేటా దొరకలేదు. దయచేసి SBIN లేదా NIFTY50 అని టైప్ చేయండి.")

st.divider()

# --- 5. Main Sector Table (Unchanged) ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_raw = get_live_data(sector_data[sector_choice])
table_results = []

if main_raw is not None:
    for s in sector_data[sector_choice]:
        row = process_intraday_logic(main_raw, s)
        if row:
            row["Stock"] = s.replace(".NS","")
            table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Signal', 'Status', 'PCR']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"}))
