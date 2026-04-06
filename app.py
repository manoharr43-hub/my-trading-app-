import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Sector Data
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Fin Nifty": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS", "MUTHOOTFIN.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

def process_stock(s, df):
    if df is None or df.empty: return None
    try:
        temp_df = df[s] if isinstance(df.columns, pd.MultiIndex) and s in df.columns.levels[0] else df
        # LTP Rounding (సున్నాలు లేకుండా)
        ltp = round(float(temp_df['Close'].iloc[-1]), 1)
        high, low, close = temp_df['High'].iloc[-2], temp_df['Low'].iloc[-2], temp_df['Close'].iloc[-2]
        pivot = (high + low + close) / 3
        
        # Call/Put Side Levels (సున్నాలు లేకుండా రౌండ్ ఆఫ్)
        call_strikes = [round(pivot + (i * (high-low)), 1) for i in range(1, 6)]
        put_strikes = [round(pivot - (i * (high-low)), 1) for i in range(1, 6)]
        
        res, sup = round(call_strikes[0], 1), round(put_strikes[0], 1)
        
        strength = "BULLISH 🚀" if ltp > pivot else "BEARISH 🔻"
        bg = "#d4edda" if ltp > pivot else "#f8d7da"
        
        return {
            "Stock": s.replace(".NS","").replace("^",""),
            "LTP": ltp, "Support": sup, "Resistance": res,
            "Call_Strikes": call_strikes, "Put_Strikes": put_strikes,
            "Strength": strength, "Bg": bg
        }
    except: return None

# --- UI Layout ---
col_lh, col_rh = st.columns([2, 1])
with col_lh:
    sector_choice = st.selectbox("📁 Select Sector (LH Side)", list(sector_data.keys()))
with col_rh:
    search_q = st.text_input("🔍 Search Stock / Index (e.g. NIFTY50, BANKNIFTY)", "").upper()

# --- 3. Search Result Box ---
if search_q:
    st.markdown(f"### 🎯 Search Analysis for: {search_q}")
    s_ticker = "^NSEI" if "NIFTY50" in search_q else ("^NSEBANK" if "BANKNIFTY" in search_q else (search_q if search_q.endswith(".NS") else search_q + ".NS"))
    s_data = yf.download(s_ticker, period="5d", interval="5m", progress=False)
    
    if not s_data.empty:
        res_dict = process_stock(s_ticker, s_data)
        if res_dict:
            st.success(f"**Overall Strength: {res_dict['Strength']}**")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🟢 Top 5 Call Side Strikes**")
                for val in res_dict['Call_Strikes']:
                    st.write(f"`{val}`")
            with c2:
                st.markdown("**🔴 Top 5 Put Side Strikes**")
                for val in res_dict['Put_Strikes']:
                    st.write(f"`{val}`")
        else: st.warning("డేటా లోడ్ అవ్వలేదు.")
    else: st.error("సరైన పేరు టైప్ చేయండి.")

st.divider()

# --- 4. Main Table ---
st.title(f"⚡ Live Scanner: {sector_choice}")
main_data = get_data(sector_data[sector_choice])
results = []
if main_data is not None:
    for s in sector_data[sector_choice]:
        row = process_stock(s, main_data)
        if row: results.append(row)

if results:
    df_f = pd.DataFrame(results)
    # టేబుల్ లో కూడా సున్నాలు లేకుండా క్లియర్ గా చూపించడం
    st.table(df_f[['Stock', 'LTP', 'Support', 'Resistance', 'Strength']].style.apply(
        lambda x: [f"background-color: {df_f.loc[x.name, 'Bg']}"]*len(x), axis=1)
        .format({"LTP": "{:.1f}", "Support": "{1:.1f}", "Resistance": "{:.1f}"}))
