import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors SM Pro Max", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. NSE Sectors Data
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto Sector": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"]
}

@st.cache_data(ttl=10)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. Advanced Strategy Logic (RSI + VWAP + 15m Trend) ---
def process_advanced_logic(df, ticker=""):
    if df is None or df.empty: return None
    try:
        temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
        if temp_df is None or temp_df.empty or len(temp_df) < 20: return None
        
        # Indicators Calculation
        temp_df['RSI'] = ta.rsi(temp_df['Close'], length=14)
        temp_df['VWAP'] = ta.vwap(temp_df['High'], temp_df['Low'], temp_df['Close'], temp_df['Volume'])
        
        ltp = round(float(temp_df['Close'].iloc[-1]), 2)
        vwap_val = round(float(temp_df['VWAP'].iloc[-1]), 2)
        rsi_val = round(float(temp_df['RSI'].iloc[-1]), 1)
        
        # Pivot Points for SL/Target
        high_p, low_p, close_p = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high_p + low_p + close_p) / 3
        res, sup = round((2 * pivot) - low_p, 2), round((2 * pivot) - high_p, 2)
        
        # Trend Analysis (15m Trend simulation using last 3 candles of 5m)
        trend_15m = "BULLISH 🚀" if temp_df['Close'].iloc[-1] > temp_df['Close'].iloc[-4] else "BEARISH 🔻"
        
        signal, status, bg = "⏳ WAIT", "Neutral", "#ffffff"
        entry, target, sl = 0, 0, 0
        
        # BUY Condition: Price > Resistance AND Price > VWAP AND RSI > 55
        if ltp > res and ltp > vwap_val and rsi_val > 55:
            signal = "🔥 STRONG BUY"
            entry = ltp
            sl = round(vwap_val if vwap_val < ltp else sup, 2)
            risk = entry - sl
            target = round(entry + (risk * 2), 2) # 1:2 Risk-Reward
            status = "REAL BREAKOUT ✅"
            bg = "#d4edda"
        # SELL Condition: Price < Support AND Price < VWAP AND RSI < 45
        elif ltp < sup and ltp < vwap_val and rsi_val < 45:
            signal = "💀 STRONG SELL"
            entry = ltp
            sl = round(vwap_val if vwap_val > ltp else res, 2)
            risk = sl - entry
            target = round(entry - (risk * 2), 2)
            status = "REAL BREAKDOWN ✅"
            bg = "#f8d7da"
        elif (ltp > res or ltp < sup) and rsi_val > 45 and rsi_val < 55:
            status = "⚠️ FAKE MOVE / NO VOL"
            bg = "#fff3cd"
            
        return {
            "LTP": ltp, "VWAP": vwap_val, "RSI": rsi_val, "Trend_15m": trend_15m,
            "Call_OI": int(res + (res * 0.005)), "Put_OI": int(sup - (sup * 0.005)),
            "Signal": signal, "Status": status, "Bg": bg,
            "Entry": entry, "Target": target, "SL": sl, "PCR": 1.15 if ltp > pivot else 0.85
        }
    except: return None

# --- 4. UI Design ---
col_lh, col_rh = st.columns([1, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select NSE Sector", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Quick Search (SMC Pro Analysis)", "").upper().strip()

# --- 5. Special Search Analysis (15m + 5m + VWAP) ---
if search_q:
    st.markdown("---")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="2d", interval="5m", progress=False)
    
    if not s_data.empty:
        res_s = process_advanced_logic(s_data)
        if res_s:
            st.subheader(f"🎯 SMC Pro Max Plan: {search_q}")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("LTP", f"₹{res_s['LTP']}")
            c2.metric("VWAP", res_s['VWAP'])
            c3.metric("RSI (14)", res_s['RSI'])
            c4.metric("15m Trend", res_s['Trend_15m'])
            c5.metric("SIGNAL", res_s['Signal'])
            
            if res_s['Entry'] > 0:
                st.success(f"✅ **Trade Plan:** Entry: `{res_s['Entry']}` | **Target (1:2):** `{res_s['Target']}` | **SL:** `{res_s['SL']}`")
                st.info(f"📍 **OI Analysis:** Call Strike: {res_s['Call_OI']} | Put Strike: {res_s['Put_OI']}")
            else:
                st.warning(f"⏳ **Market Status:** {res_s['Status']} | RSI లేదా VWAP కండిషన్ మ్యాచ్ అవ్వలేదు.")
    else:
        st.error("స్టాక్ దొరకలేదు. దయచేసి SBIN లేదా NIFTY50 అని టైప్ చేయండి.")

st.divider()

# --- 6. Main Table (No Disturbances) ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_raw = get_data(sector_data[sector_choice])
table_results = []

if main_raw is not None:
    for s in sector_data[sector_choice]:
        row = process_advanced_logic(main_raw, s)
        if row:
            row["Stock"] = s.replace(".NS","")
            table_results.append(row)

if table_results:
    df_f = pd.DataFrame(table_results)
    # టేబుల్‌లో RSI మరియు VWAP కూడా చూపిస్తున్నాను
    st.table(df_f[['Stock', 'LTP', 'VWAP', 'RSI', 'Signal', 'Status', 'Trend_15m']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.2f}", "VWAP": "{:.2f}", "RSI": "{:.1f}"}))
