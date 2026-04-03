import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# 2. Sidebar Folders
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్టాక్స్ లిస్ట్‌లు
nifty50 = ["RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS"]
banknifty = ["SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"]
finnifty = ["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS"]

# స్కానింగ్ ఫంక్షన్ (Clean Pricing & Styling)
def clean_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Scanning {s}...")
        try:
            ticker = yf.Ticker(s)
            df = ticker.history(period="5d", interval="1d")
            if not df.empty:
                # ధరను 2 డెసిమల్స్ కి రౌండ్ చేస్తున్నాం
                current_price = round(df['Close'].iloc[-1], 2)
                prev_price = round(df['Close'].iloc[-2], 2)
                
                # Signal Logic
                if current_price > prev_price:
                    sig, color = "🚀 BUY", "#d4edda" # Green
                else:
                    sig, color = "🔻 SELL", "#f8d7da" # Red
                
                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{current_price:.2f}", # ఇక్కడ ధర నీట్‌గా మారుతుంది
                    "Signal": sig,
                    "Bg": color
                })
        except: continue
    
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        # స్టైలింగ్ అప్లై చేయడం
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
    else:
        st.error("Data error. Try again.")

# Pages
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    st.info("సోమవారం మార్కెట్ సమయంలో ఇక్కడ లైవ్ డేటా అప్‌డేట్ అవుతుంది.")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 Watch")
    if st.button("Scan Nifty"): clean_scan(nifty50)

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty Watch")
    if st.button("Scan Bank Nifty"): clean_scan(banknifty)

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty Watch")
    if st.button("Scan Fin Nifty"): clean_scan(finnifty)

st.markdown("---")
st.caption("Manohar - Variety Motors, Hyderabad")
