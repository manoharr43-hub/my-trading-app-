import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# RSI Calculation (Manual - No library needed)
def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=10)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# Core Logic
def process_logic(df, ticker=""):
    if df is None or df.empty: return None
    try:
        temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
        if temp_df is None or temp_df.empty or len(temp_df) < 20: return None
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        # Manual VWAP calculation
        temp_df['VWAP'] = (temp_df['Close'] * temp_df['Volume']).cumsum() / temp_df['Volume'].cumsum()
        vwap_val = round(float(temp_df['VWAP'].iloc[-1]), 2)
        rsi_val = round(get_rsi(temp_df['Close']).iloc[-1], 1)
        
        high_p, low_p, close_p = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high_p + low_p + close_p) / 3
        res, sup = round((2 * pivot) - low_p, 2), round((2 * pivot) - high_p, 2)
        
        signal, status, bg = "⏳ WAIT", "Neutral", "#ffffff"
        entry, target, sl = 0, 0, 0
        
        if ltp > res and ltp > vwap_val and rsi_val > 55:
            signal, entry, bg = "🔥 STRONG BUY", ltp, "#d4edda"
            sl = round(vwap_val if vwap_val < ltp else sup, 2)
            target = round(entry + (entry - sl) * 2, 2)
            status = "REAL BREAKOUT ✅"
        elif ltp < sup and ltp < vwap_val and rsi_val < 45:
            signal, entry, bg = "💀 STRONG SELL", ltp, "#f8d7da"
            sl = round(vwap_val if vwap_val > ltp else res, 2)
            target = round(entry - (sl - entry) * 2, 2)
            status = "REAL BREAKDOWN ✅"
        elif (ltp > res or ltp < sup):
            status, bg = "⚠️ FAKE MOVE / NO VOL", "#fff3cd"
            
        return {"LTP": ltp, "VWAP": vwap_val, "RSI": rsi_val, "Signal": signal, "Status": status, "Bg": bg, "Entry": entry, "Target": target, "SL": sl}
    except: return None

# UI Layout
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_data = {"Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "ITC.NS"],
                   "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
                   "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"]}
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (RELIANCE, NIFTY50)", "").upper().strip()

if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS")
    s_data = yf.download(s_ticker, period="2d", interval="5m", progress=False)
    if not s_data.empty:
        res_s = process_logic(s_data)
        if res_s:
            st.subheader(f"🎯 SMC Plan: {search_q}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", f"₹{res_s['LTP']}")
            c2.metric("VWAP", res_s['VWAP'])
            c3.metric("RSI", res_s['RSI'])
            c4.metric("SIGNAL", res_s['Signal'])
            if res_s['Entry'] > 0:
                st.success(f"✅ Entry: `{res_s['Entry']}` | Target: `{res_s['Target']}` | SL: `{res_s['SL']}`")
    else: st.error("Stock not found.")

st.divider()
st.title(f"⚡ Live Scanner: {sector_choice}")
main_raw = get_data(sector_data[sector_choice])
table_results = []
if main_raw is not None:
    for s in sector_data[sector_choice]:
        row = process_logic(main_raw, s)
        if row:
            row["Stock"] = s.replace(".NS","")
            table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    st.table(df_f[['Stock', 'LTP', 'VWAP', 'RSI', 'Signal', 'Status']].style.apply(lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1).format({"LTP": "{:.2f}", "VWAP": "{:.2f}", "RSI": "{:.1f}"}))
