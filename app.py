import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. పేజీ సెటప్
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=10000, limit=None, key="fizzbuzzcounter")

# 2. ఇండెక్స్ మరియు సెక్టార్ డేటా (Indices Add చేశాం)
sector_data = {
    "Indices (Nifty/Bank/Fin)": ["^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS"],
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "PNB.NS"]
}

@st.cache_data(ttl=10)
def get_live_data(stock_list):
    try:
        data = yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        return data
    except: return None

# 3. పైన సెక్టార్ రోలర్ (Sector Strength)
st.subheader("📊 Sector Movement (High & Low Strong)")
perf_cols = st.columns(len(sector_data))
for i, (sector, stocks) in enumerate(sector_data.items()):
    s_data = yf.download(stocks, period="1d", interval="15m", progress=False)['Close']
    if not s_data.empty:
        change = ((s_data.iloc[-1] - s_data.iloc[0]) / s_data.iloc[0]).mean() * 100
        label = "🔥 Strong" if change > 0 else "❄️ Weak"
        perf_cols[i].metric(sector, f"{change:.2f}%", label)

def run_live_scan(stock_list):
    results = []
    data = get_live_data(stock_list)
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 10: continue
            
            # --- సున్నాల తొలగింపు (Decimal Rounding) ---
            ltp = round(float(df['Close'].iloc[-1]), 2)
            
            # Support & Resistance Calculations
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 2)
            sup = round((2 * pivot) - high, 2)

            # --- 4. OI & Operator Status (LH/RH Side Logic) ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            vol_spike = curr_vol > (avg_vol * 1.5)
            
            oi_status = "Normal"
            bg_color = "#ffffff" # Default White

            # నిఫ్టీ, బ్యాంక్ నిఫ్టీ లో Call/Put side OI తెలుసుకోవడానికి
            if ltp > res:
                oi_status = "🟢 Call Side OI High"
                bg_color = "#d4edda" # Buy (Green)
            elif ltp < sup:
                oi_status = "🔴 Put Side OI High"
                bg_color = "#f8d7da" # Sell (Red)

            # పేరు పక్కన స్టార్ తీసేసాం (Star Removed)
            display_name = s.replace(".NS","").replace("^","")

            results.append({
                "Stock (LH Side)": display_name,
                "LTP (Price)": ltp,
                "Support": sup,
                "Resistance": res,
                "OI Status (RH Side)": oi_status,
                "Bg": bg_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        # టేబుల్ కలరింగ్ మరియు ప్రదర్శన
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"] * len(x), axis=1))

# Sidebar & Execution
sector_choice = st.sidebar.selectbox("Select Index/Sector", list(sector_data.keys()))
st.title(f"⚡ Live Scanner: {sector_choice}")
run_live_scan(sector_data[sector_choice])

st.caption("Developed by Manohar | Variety Motors, Hyderabad | LH/RH Logic Enabled")
