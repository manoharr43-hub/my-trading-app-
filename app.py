import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Config & Auto-refresh (15 Seconds)
st.set_page_config(page_title="Variety Motors SM Pro Scanner", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Updated Sectors (FinNifty Added)
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "AUBANK.NS"],
    "Fin Nifty": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS", "HDFCBANK.NS", "ICICIBANK.NS", "MUTHOOTFIN.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        # threads=True వాడటం వల్ల లోడింగ్ ఫాస్ట్ గా ఉంటుంది
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. LH Side: Sector Scoring Roller ---
st.markdown("### 📊 Today's Sector Scoring (LH)")
perf_cols = st.columns(len(sector_data))
for i, (sector, stocks) in enumerate(sector_data.items()):
    s_data = yf.download(stocks, period="1d", interval="15m", progress=False)['Close']
    if not s_data.empty:
        change = ((s_data.iloc[-1] - s_data.iloc[0]) / s_data.iloc[0]).mean() * 100
        color = "green" if change > 0 else "red"
        perf_cols[i].markdown(f"**{sector}**\n<h2 style='color:{color};'>{change:.2f}%</h2>", unsafe_allow_html=True)

st.divider()

# --- 4. Main UI Layout: LH Selector & RH Search ---
col_lh, col_rh = st.columns([2, 1])

with col_lh:
    sector_choice = st.selectbox("📁 Select Sector / Index (LH Side)", list(sector_data.keys()))

with col_rh:
    search_stock = st.text_input("🔍 Search Any Stock / Index (RH Side)", "").upper()
    if search_stock and not (search_stock.endswith(".NS") or search_stock.startswith("^")):
        # NIFTY లేదా BANKNIFTY అని టైప్ చేస్తే ఆటోమేటిక్ గా సింబల్ మారుస్తుంది
        if "BANK" in search_stock: search_stock = "^NSEBANK"
        elif "NIFTY" in search_stock: search_stock = "^NSEI"
        else: search_stock += ".NS"

# Final list logic
final_list = sector_data[sector_choice]
if search_stock:
    if search_stock not in final_list:
        final_list = [search_stock] + final_list

def run_scanner(stock_list):
    results = []
    data = get_data(stock_list)
    if data is None or data.empty: 
        st.info("డేటా లోడ్ అవుతోంది... ఆగండి.")
        return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if df.empty or len(df) < 10: continue
            
            # --- Rounding LTP, Support, Resistance (సున్నాల తొలగింపు) ---
            ltp = round(float(df['Close'].iloc[-1]), 2)
            
            # Pivot Levels
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 2)
            sup = round((2 * pivot) - high, 2)

            # Volume & Fake Breakout Logic
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            
            status = "⏳ Neutral"
            bg_color = "#ffffff"

            # Buy/Sell & Call/Put Logic
            if ltp > res:
                if curr_vol < avg_vol:
                    status = "⚠️ FAKE BREAKOUT"
                    bg_color = "#fff3cd" # పసుపు (Warning)
                else:
                    status = "🚀 BUY / CALL SIDE"
                    bg_color = "#d4edda" # ఆకుపచ్చ (Green)
            elif ltp < sup:
                if curr_vol < avg_vol:
                    status = "⚠️ FAKE BREAKDOWN"
                    bg_color = "#fff3cd"
                else:
                    status = "🔻 SELL / PUT SIDE"
                    bg_color = "#f8d7da" # ఎరుపు (Red)

            results.append({
                "Stock Name": s.replace(".NS","").replace("^",""),
                "LTP (Price)": ltp,
                "Support": sup,
                "Resistance": res,
                "OI / Market Signal": status,
                "Bg": bg_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"] * len(x), axis=1)
            .set_properties(subset=['Support'], **{'color': 'blue', 'font-weight': 'bold'})
            .set_properties(subset=['Resistance'], **{'color': 'red', 'font-weight': 'bold'})
            .format({"LTP (Price)": "{:.2f}", "Support": "{:.2f}", "Resistance": "{:.2f}"})
        )

st.title(f"⚡ Live Scanner: {sector_choice}")
run_scanner(final_list)
