import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# Manual Indicators
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

# --- Strict Logic for Manohar ---
def process_logic(df, ticker=""):
    if df is None or df.empty: return None
    try:
        temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
        if temp_df is None or temp_df.empty or len(temp_df) < 30: return None
        
        # 1. Price & Indicators
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        temp_df['VWAP'] = (temp_df['Close'] * temp_df['Volume']).cumsum() / temp_df['Volume'].cumsum()
        vwap_val = round(float(temp_df['VWAP'].iloc[-1]), 2)
        rsi_val = round(get_rsi(temp_df['Close']).iloc[-1], 1)
        
        # 2. Volume Filter (Strict)
        avg_vol = temp_df['Volume'].iloc[-6:-1].mean()
        curr_vol = temp_df['Volume'].iloc[-1]
        vol_pumping = curr_vol > (avg_vol * 1.5) # 50% more volume than average
        
        # 3. Support/Resistance
        high_p, low_p, close_p = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high_p + low_p + close_p) / 3
        res, sup = round((2 * pivot) - low_p, 2), round((2 * pivot) - high_p, 2)
        
        signal, status, bg = "⏳ WAIT", "Neutral", "#ffffff"
        entry, target, sl = 0, 0, 0

        # --- STRICT BUY CONDITION ---
        # ధర Resistance పైన ఉండాలి + VWAP పైన ఉండాలి + RSI 55-70 మధ్య ఉండాలి + Volume పెరగాలి
        if ltp > res and ltp > vwap_val and 55 <= rsi_val <= 72 and vol_pumping:
            signal, entry, bg = "🔥 STRONG BUY", ltp, "#d4edda"
            sl = round(vwap_val if vwap_val < ltp else sup, 2)
            target = round(entry + (entry - sl) * 2, 2)
            status = "🚀 REAL BREAKOUT (VOL+)"
            
        # --- STRICT SELL CONDITION ---
        elif ltp < sup and ltp < vwap_val and 30 <= rsi_val <= 45 and vol_pumping:
            signal, entry, bg = "💀 STRONG SELL", ltp, "#f8d7da"
            sl = round(vwap_val if vwap_val > ltp else res, 2)
            target = round(entry - (sl - entry) * 2, 2)
            status = "📉 REAL BREAKDOWN (VOL+)"
            
        elif (ltp > res or ltp < sup) and not vol_pumping:
            status, bg = "⚠️ FAKE MOVE / NO VOL", "#fff3cd"
        elif rsi_val > 72:
            status, bg = "🛑 OVERBOUGHT - WAIT", "#ffcccc"

        return {
            "Stock": ticker.replace(".NS",""), "LTP": ltp, "VWAP": vwap_val, "RSI": rsi_val, 
            "Support": sup, "Resistance": res, "Signal": signal, "Status": status, "Bg": bg,
            "Entry": entry, "Target": target, "SL": sl
        }
    except: return None

# --- UI Setup ---
st.markdown("### 🛠 Variety Motors - SMC Strict Scanner")
col_lh, col_rh = st.columns([1, 1])

with col_lh:
    sectors = {
        "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "ITC.NS"],
        "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
        "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"]
    }
    choice = st.selectbox("📁 Select Sector", list(sectors.keys()))

with col_rh:
    search_q = st.text_input("🔍 Quick Search (Plan)", "").upper().strip()

if search_q:
    s_ticker = search_q if search_q.endswith(".NS") else search_q + ".NS"
    s_data = yf.download(s_ticker, period="2d", interval="5m", progress=False)
    if not s_data.empty:
        res_s = process_logic(s_data, s_ticker)
        if res_s:
            st.subheader(f"🎯 Trade Plan: {search_q}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("LTP", res_s['LTP'])
            c2.metric("VWAP", res_s['VWAP'])
            c3.metric("RSI", res_s['RSI'])
            c4.metric("Signal", res_s['Signal'])
            if res_s['Entry'] > 0:
                st.success(f"✅ Entry: {res_s['Entry']} | Target: {res_s['Target']} | SL: {res_s['SL']}")
            st.warning(f"💡 Info: {res_s['Status']}")

st.divider()
st.title(f"⚡ Live Scanner: {choice}")
raw = get_data(sectors[choice])
results = []
if raw is not None:
    for s in sectors[choice]:
        row = process_logic(raw, s)
        if row: results.append(row)

if results:
    df = pd.DataFrame(results)
    st.table(df[['Stock', 'LTP', 'Support', 'Resistance', 'VWAP', 'RSI', 'Signal', 'Status']].style.apply(
        lambda x: [f"background-color: {df.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}", "VWAP": "{:.2f}", "RSI": "{:.1f}"}))
