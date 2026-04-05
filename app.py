import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=5000, limit=None, key="fizzbuzzcounter")

# --- సెక్టార్ లిస్ట్ ---
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

# --- సెక్టార్ మూమెంట్ లెక్కించడం ---
def get_sector_performance():
    perf = []
    for sector, stocks in sector_data.items():
        data = yf.download(stocks, period="1d", interval="5m", progress=False)['Close']
        if not data.empty:
            avg_change = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]).mean() * 100
            perf.append({"Sector": sector, "Avg Change %": round(avg_change, 2)})
    return pd.DataFrame(perf).sort_values(by="Avg Change %", ascending=False)

# --- పైన సెక్టార్ పర్ఫార్మెన్స్ చూపించడం ---
st.subheader("🔥 Today's Top Sectors")
sector_perf_df = get_sector_performance()
cols = st.columns(len(sector_perf_df))
for i, row in enumerate(sector_perf_df.itertuples()):
    cols[i].metric(row.Sector, f"{row.Avg_Change_}%")

# --- మెయిన్ స్కానర్ ఫంక్షన్ ---
def run_live_scan(stock_list):
    results = []
    data = yf.download(stock_list, period="2d", interval="5m", group_by='ticker', progress=False)
    
    for s in stock_list:
        df = data[s] if len(stock_list) > 1 else data
        if not df.empty and len(df) > 5:
            ltp = df['Close'].iloc[-1]
            # --- Operator Entry Logic ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            
            # వాల్యూమ్ 2 రెట్లు పెరిగితే ఆపరేటర్ ఎంట్రీ
            is_operator = "⚠️ OPERATOR ENTRY" if curr_vol > (avg_vol * 2.5) else "Regular"
            
            # Pivot Levels
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res1 = (2 * pivot) - low
            
            results.append({
                "Stock": s.replace(".NS",""),
                "LTP": round(ltp, 2),
                "Signal": "🚀 BUY" if ltp > res1 else "⏳ WAIT",
                "Volume Alert": is_operator,
                "Operator Status": "🟢 BIG FISH" if is_operator != "Regular" else "⚪ Retail"
            })
    
    if results:
        st.table(pd.DataFrame(results))

# Sidebar & Execution
sector_choice = st.sidebar.selectbox("Select Sector", list(sector_data.keys()))
st.title(f"⚡ Live Scanner: {sector_choice}")
run_live_scan(sector_data[sector_choice])
