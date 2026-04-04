import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# Sidebar
st.sidebar.title("📁 Sector Folders")
sector_choice = st.sidebar.selectbox(
    "Select Sector", 
    ["Nifty 50", "Banking", "Auto (Variety Motors)", "IT", "Pharma", "Metal", "Finance"]
)

def run_advanced_scan(stock_list):
    results = []
    status = st.empty()
    status.info("Fetching Market Data... Please wait.")
    
    try:
        # Download data in bulk for speed
        data = yf.download(stock_list, period="20d", interval="1d", group_by='ticker', threads=True, progress=False)
        
        for s in stock_list:
            df = data[s] if len(stock_list) > 1 else data
            if not df.empty and len(df) > 5:
                ltp = round(df['Close'].iloc[-1], 2)
                
                # --- Pivot Point Calculations (Standard) ---
                high = df['High'].iloc[-2]
                low = df['Low'].iloc[-2]
                close = df['Close'].iloc[-2]
                
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)   # Resistance (Sell Zone)
                sup1 = round((2 * pivot) - high, 2)  # Support (Buy Zone)
                
                # --- Volume Analysis ---
                curr_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].mean()
                
                # --- Logic for Signal & Zone ---
                zone = "Neutral"
                sig = "⏳ WAIT"
                bg_color = "#ffffff"
                analysis = "No Breakout"

                if ltp <= (sup1 * 1.005) and ltp >= (sup1 * 0.995):
                    zone = "🎯 AT SUPPORT"
                    sig = "🚀 BUY"
                    bg_color = "#d4edda" # Green
                elif ltp >= (res1 * 0.995) and ltp <= (res1 * 1.005):
                    zone = "🛑 AT RESISTANCE"
                    sig = "🔻 SELL"
                    bg_color = "#f8d7da" # Red
                
                # Fake Breakout Logic
                if ltp > res1:
                    analysis = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT"
                    sig = "🚀 BUY"
                    bg_color = "#d4edda"
                elif ltp < sup1:
                    analysis = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN"
                    sig = "🔻 SELL"
                    bg_color = "#f8d7da"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Support (Buy)": f"{sup1:.2f}",
                    "Resistance (Sell)": f"{res1:.2f}",
                    "Current Zone": zone,
                    "Signal": sig,
                    "Breakout/Down": analysis,
                    "Bg": bg_color
                })
    except Exception as e:
        st.error(f"Error: {e}")
        
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# Sector Lists
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "PNB.NS", "FEDERALBNK.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "TVSMOTOR.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS"],
    "Metal": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

st.title(f"🔍 {sector_choice} Pro Scanner")
if st.button(f"Start {sector_choice} Analysis"):
    run_advanced_scan(sector_data.get(sector_choice, []))

st.caption("Developed by Manohar - Service Center Manager | Variety Motors, Hyderabad")
