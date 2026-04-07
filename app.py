Help meimport streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

1. Page Config

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

Indicators Calculation

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

Logic for Signal & Levels

def process_logic(df, ticker=""):
if df is None or df.empty: return None
try:
temp_df = df[ticker] if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0] else df
if temp_df is None or temp_df.empty or len(temp_df) < 20: return None

ltp = round(float(temp_df['Close'].iloc[-1]), 2)  
    # VWAP & RSI  
    temp_df['VWAP'] = (temp_df['Close'] * temp_df['Volume']).cumsum() / temp_df['Volume'].cumsum()  
    vwap_val = round(float(temp_df['VWAP'].iloc[-1]), 2)  
    rsi_val = round(get_rsi(temp_df['Close']).iloc[-1], 1)  
      
    # Pivot Levels  
    high_p, low_p, close_p = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]  
    pivot = (high_p + low_p + close_p) / 3  
    res, sup = round((2 * pivot) - low_p, 2), round((2 * pivot) - high_p, 2)  
      
    signal, status, bg = "⏳ WAIT", "Neutral", "#ffffff"  
    entry, target, sl = 0, 0, 0  
      
    # Confirmation Logic  
    if ltp > res and ltp > vwap_val and rsi_val > 52:  
        signal, entry, bg = "🔥 STRONG BUY", ltp, "#d4edda"  
        sl = round(vwap_val if vwap_val < ltp else sup, 2)  
        target = round(entry + (entry - sl) * 2, 2)  
        status = "REAL BREAKOUT ✅"  
    elif ltp < sup and ltp < vwap_val and rsi_val < 48:  
        signal, entry, bg = "💀 STRONG SELL", ltp, "#f8d7da"  
        sl = round(vwap_val if vwap_val > ltp else res, 2)  
        target = round(entry - (sl - entry) * 2, 2)  
        status = "REAL BREAKDOWN ✅"  
    elif (ltp > res or ltp < sup):  
        status, bg = "⚠️ NO MOMENTUM", "#fff3cd"  
          
    return {  
        "Stock": ticker.replace(".NS",""), "LTP": ltp, "Support": sup, "Resistance": res,  
        "VWAP": vwap_val, "RSI": rsi_val, "Signal": signal, "Status": status, "Bg": bg,  
        "Entry": entry, "Target": target, "SL": sl  
    }  
except: return None

--- UI Setup ---

st.markdown("### 🛠 Variety Motors - Multi-Sector Scanner")
col_lh, col_rh = st.columns([1, 1])

with col_lh:
# Ikada mari konni sectors add chesanu
sector_data = {
"Auto Sector": ["TATAMOTORS.NS", "HEROMOTOCO.NS", "M&M.NS", "BAJAJ-AUTO.NS", "ASHOKLEY.NS", "MARUTI.NS", "EICHERMOT.NS"],
"Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "ITC.NS", "LT.NS", "BHARTIARTL.NS"],
"Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"],
"IT Sector": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
"Metal Sector": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "VEDL.NS", "JSWSTEEL.NS"],
"Pharma Sector": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"]
}
sector_choice = st.selectbox("📁 Select NSE Sector (LH Side)", list(sector_data.keys()))

with col_rh:
search_q = st.text_input("🔍 Quick Plan (TATASTEEL, RELIANCE...)", "").upper().strip()

Quick Search Logic

if search_q:
s_ticker = search_q if search_q.endswith(".NS") else search_q + ".NS"
s_data = yf.download(s_ticker, period="2d", interval="5m", progress=False)
if not s_data.empty:
res_s = process_logic(s_data, s_ticker)
if res_s:
st.subheader(f"🎯 SMC Plan: {search_q}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("LTP", res_s['LTP'])
c2.metric("VWAP", res_s['VWAP'])
c3.metric("RSI", res_s['RSI'])
c4.metric("Signal", res_s['Signal'])
if res_s['Entry'] > 0:
st.success(f"✅ Entry: {res_s['Entry']} | Target: {res_s['Target']} | SL: {res_s['SL']}")

st.divider()

--- Live Scanner Table ---

st.title(f"⚡ Live Scanner: {sector_choice}")
main_raw = get_data(sector_data[sector_choice])
table_results = []

if main_raw is not None:
for s in sector_data[sector_choice]:
row = process_logic(main_raw, s)
if row: table_results.append(row)

if table_results:
df_f = pd.DataFrame(table_results)
st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'VWAP', 'RSI', 'Signal', 'Status']].style.apply(
lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
.format({"LTP": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}", "VWAP": "{:.2f}", "RSI": "{:.1f}"})) e code nse postion undha telugu explain chaye
