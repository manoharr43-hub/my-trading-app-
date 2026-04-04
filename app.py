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

# --- Faster Scan Function ---
def run_fast_scan(stock_list):
    results = []
    status = st.empty()
    
    # ఒకేసారి అన్ని స్టాక్స్ డేటా లోడ్ చేయడానికి (Faster approach)
    status.info("Fetching data from market... Please wait.")
    try:
        # Download data for all stocks at once to save time
        data = yf.download(stock_list, period="20d", interval="1d", group_by='ticker', threads=True, progress=False)
        
        for s in stock_list:
            df = data[s] if len(stock_list) > 1 else data
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
                
                # Signal & Fake Detection
                analysis = "Normal"
                sig, color = "⏳ NEUTRAL", "#ffffff"
                
                if ltp > buy_above:
                    sig, color = "🚀 BUY", "#d4edda"
                    analysis = "✅ REAL BREAKOUT" if curr_vol > avg_vol else "⚠️ FAKE BREAKOUT (Low Vol)"
                elif ltp < sell_below:
                    sig, color = "🔻 SELL", "#f8d7da"
                    analysis = "✅ REAL BREAKDOWN" if curr_vol > avg_vol else "⚠️ FAKE BREAKDOWN (Low Vol)"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Buy Above": f"{buy_above:.2f}",
                    "Sell Below": f"{sell_below:.2f}",
                    "Signal": sig,
                    "Breakout Info": analysis,
                    "Bg": color
                })
    except Exception as e:
        st.error(f"Error loading data: {e}")
        
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# --- Sector Data ---
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "MARUTI.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS"],
    "Metal": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

st.title(f"🔍 {sector_choice} Scanner")
if st.button(f"Scan {sector_choice}"):
    run_fast_scan(sector_data.get(sector_choice, []))

st.caption("Developed by Manohar | Variety Motors, Hyderabad")
