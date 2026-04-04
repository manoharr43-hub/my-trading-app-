import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Sector Scanner", layout="wide")

# --- Sidebar ---
st.sidebar.title("📁 Sector Folders")
sector_choice = st.sidebar.selectbox(
    "Select Sector to Scan", 
    ["Nifty 50", "Banking", "Auto (Variety Motors)", "IT", "Pharma", "Metal", "Finance"]
)

def run_advanced_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Analyzing {s}...")
        try:
            ticker = yf.Ticker(s)
            # 20 days data to calculate average volume
            df = ticker.history(period="20d", interval="1d")
            if not df.empty and len(df) > 1:
                ltp = round(df['Close'].iloc[-1], 2)
                
                # Pivot Levels
                high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
                pivot = (high + low + close) / 3
                buy_above = round((2 * pivot) - low, 2)
                sell_below = round((2 * pivot) - high, 2)
                
                # Volume Logic
                curr_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].mean()
                
                # --- Fake Breakout / Breakdown Logic ---
                analysis = "Normal"
                sig, color = "⏳ NEUTRAL", "#ffffff"
                
                if ltp > buy_above:
                    sig, color = "🚀 BUY", "#d4edda"
                    analysis = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT (Low Vol)"
                elif ltp < sell_below:
                    sig, color = "🔻 SELL", "#f8d7da"
                    analysis = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN (Low Vol)"
                else:
                    analysis = "Range Bound"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Buy Above": f"{buy_above:.2f}",
                    "Sell Below": f"{sell_below:.2f}",
                    "Signal": sig,
                    "Breakout Analysis": analysis,
                    "Bg": color
                })
        except: continue
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# --- Sector Lists ---
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "PNB.NS", "KOTAKBANK.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "MARUTI.NS", "BAJAJ-AUTO.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS"],
    "Metal": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

st.title(f"🔍 {sector_choice} - Breakout & Breakdown Scanner")
if st.button(f"Start {sector_choice} Scan"):
    run_advanced_scan(sector_data.get(sector_choice, []))

st.divider()
st.caption("Developed by Manohar | Variety Motors, Hyderabad")
