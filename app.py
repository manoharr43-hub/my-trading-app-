import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors SM Pro", layout="wide")
st_autorefresh(interval=15000, limit=None, key="fizzbuzzcounter")

# 2. Updated Sectors (Pharmacy & IT Added)
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"],
    "Bank Nifty": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "AUBANK.NS"],
    "Pharmacy": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "AUBANK.NS"],
    "IT Sector": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "LTIM.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"]
}

@st.cache_data(ttl=15)
def get_data(stock_list):
    try:
        return yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
    except: return None

# --- 3. UI Layout: LH Sector Select & RH Search Box ---
col_lh, col_rh = st.columns([2, 1])

with col_lh:
    sector_choice = st.selectbox("📁 Select Sector (LH Side)", list(sector_data.keys()))

with col_rh:
    search_stock = st.text_input("🔍 Search Stock Name (RH Side)", "").upper()
    if search_stock and not search_stock.endswith(".NS"):
        search_stock += ".NS"

# Display List Preparation
final_list = sector_data[sector_choice]
if search_stock:
    if search_stock not in final_list:
        final_list = [search_stock] + final_list

def run_scanner(stock_list):
    results = []
    data = get_data(stock_list)
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 10: continue
            
            # LTP Rounding (Removing extra zeros)
            ltp = round(float(df['Close'].iloc[-1]), 1)
            
            # Pivot Levels
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 1)
            sup = round((2 * pivot) - high, 1)

            # Volume Logic for Fake Breakout
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            
            status = "⏳ Neutral"
            bg_color = "#ffffff"

            # Signal Logic (Call/Put Side & Fake Alerts)
            if ltp > res:
                if curr_vol < avg_vol:
                    status = "⚠️ FAKE BREAKOUT"
                    bg_color = "#fff3cd" # Yellow
                else:
                    status = "🟢 CALL SIDE (BUY)"
                    bg_color = "#d4edda" # Green
            elif ltp < sup:
                if curr_vol < avg_vol:
                    status = "⚠️ FAKE BREAKDOWN"
                    bg_color = "#fff3cd" # Yellow
                else:
                    status = "🔴 PUT SIDE (SELL)"
                    bg_color = "#f8d7da" # Red

            results.append({
                "Stock Name": s.replace(".NS",""),
                "LTP": ltp,
                "Support": sup,
                "Resistance": res,
                "Market Side": status,
                "Bg": bg_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"] * len(x), axis=1)
            .set_properties(subset=['Support'], **{'color': 'blue', 'font-weight': 'bold'})
            .set_properties(subset=['Resistance'], **{'color': 'red', 'font-weight': 'bold'})
        )

st.title(f"⚡ Live Scanner: {sector_choice}")
run_scanner(final_list)
