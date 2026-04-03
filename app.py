import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# Sidebar
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్కానింగ్ ఫంక్షన్ (With Support & Resistance)
def advanced_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Analyzing {s}...")
        try:
            ticker = yf.Ticker(s)
            df = ticker.history(period="5d", interval="1d")
            if not df.empty:
                ltp = round(df['Close'].iloc[-1], 2)
                high = df['High'].iloc[-1]
                low = df['Low'].iloc[-1]
                close = df['Close'].iloc[-1]
                
                # Pivot Point Calculation (Support & Resistance)
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)   # Selling Zone (Resistance)
                sup1 = round((2 * pivot) - high, 2)  # Buying Zone (Support)
                
                # Signal Logic
                if ltp > pivot:
                    sig, color = "🚀 BUY", "#d4edda"
                else:
                    sig, color = "🔻 SELL", "#f8d7da"
                
                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Support (Buy)": f"{sup1:.2f}",
                    "Resist (Sell)": f"{res1:.2f}",
                    "Signal": sig,
                    "Bg": color
                })
        except: continue
    
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
    else:
        st.error("No Data Found!")

# Pages
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    st.info("OI డేటా సోమవారం లైవ్ లో వస్తుంది.")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 - Support & Resistance")
    if st.button("Scan Nifty"): 
        advanced_scan(["RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS"])

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty - Support & Resistance")
    if st.button("Scan Bank Nifty"): 
        advanced_scan(["SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS"])

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty - Support & Resistance")
    if st.button("Scan Fin Nifty"): 
        advanced_scan(["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS"])

st.caption("Manohar - Variety Motors, Hyderabad")
