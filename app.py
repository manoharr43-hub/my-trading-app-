import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# Sidebar
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

def advanced_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Analyzing {s}...")
        try:
            ticker = yf.Ticker(s)
            # 20 days data to calculate Average Volume
            df = ticker.history(period="20d", interval="1d")
            if not df.empty and len(df) > 1:
                ltp = round(df['Close'].iloc[-1], 2)
                high = df['High'].iloc[-2]
                low = df['Low'].iloc[-2]
                close = df['Close'].iloc[-2]
                
                # Volume Analysis
                current_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].mean()
                
                # Pivot Point Calculation
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)   # Buy Level
                sup1 = round((2 * pivot) - high, 2)  # Sell Level
                
                # --- Signal Logic ---
                # ఒకవేళ ప్రైస్ రెసిస్టెన్స్ పైన ఉంటే BUY, సపోర్ట్ కింద ఉంటే SELL
                if ltp > res1:
                    sig = "🚀 BUY"
                    color = "#d4edda" # Green
                    breakout = "✅ REAL" if current_vol > avg_vol else "⚠️ FAKE (Low Vol)"
                elif ltp < sup1:
                    sig = "🔻 SELL"
                    color = "#f8d7da" # Red
                    breakout = "✅ REAL" if current_vol > avg_vol else "⚠️ FAKE (Low Vol)"
                else:
                    sig = "⏳ NEUTRAL"
                    color = "#ffffff" # White
                    breakout = "No Breakout"
                
                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Buy Above": f"{res1:.2f}",
                    "Sell Below": f"{sup1:.2f}",
                    "Current Signal": sig,
                    "Breakout Info": breakout,
                    "Bg": color
                })
        except: continue
    
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        # టేబుల్ లో సిగ్నల్ ని బట్టి కలర్ అప్లై చేయడం
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
    else:
        st.error("No Data Found!")

# Pages
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    st.info("OI డేటా సోమవారం లైవ్ లో వస్తుంది.")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 - Buy/Sell Scanner")
    if st.button("Scan Nifty"): 
        advanced_scan(["RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS", "AXISBANK.NS"])

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty - Buy/Sell Scanner")
    if st.button("Scan Bank Nifty"): 
        advanced_scan(["SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "FEDERALBNK.NS"])

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty - Buy/Sell Scanner")
    if st.button("Scan Fin Nifty"): 
        advanced_scan(["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS"])

st.caption("Developed by Manohar - Variety Motors, Hyderabad")
