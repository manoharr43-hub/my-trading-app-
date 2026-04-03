import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# Sidebar
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్టాక్స్ లిస్ట్‌లు
nifty50 = ["RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "INFY.NS"]
banknifty = ["SBIN.NS", "HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS"]
finnifty = ["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS"]

# మేజిక్ స్కానింగ్ ఫంక్షన్
def magic_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Searching {s}...")
        try:
            # ఇక్కడ 'period' ని 1mo కి మార్చాను, ఇది డేటా లేకపోయినా పాతది లాగుతుంది
            ticker = yf.Ticker(s)
            df = ticker.history(period="1mo", interval="1d")
            
            if not df.empty:
                current_price = round(df['Close'].iloc[-1], 2)
                prev_price = round(df['Close'].iloc[-2], 2)
                
                # Simple Logic: నిన్నటి కంటే ధర పెరిగితే BUY, తగ్గితే SELL
                if current_price > prev_price:
                    sig, color = "🚀 BUY", "#d4edda"
                else:
                    sig, color = "🔻 SELL", "#f8d7da"
                
                results.append({"Stock": s.replace(".NS",""), "LTP": current_price, "Signal": sig, "Bg": color})
        except: continue
    
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        # రంగులు అప్లై చేయడం
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))
    else:
        st.error("NSE సర్వర్ రెస్పాన్స్ ఇవ్వడం లేదు. దయచేసి 'Scan' ని మళ్ళీ నొక్కండి.")

# Pages
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    st.write("మార్కెట్ సెలవు కాబట్టి ఇక్కడ డేటా సోమవారం కనిపిస్తుంది.")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 Watch")
    if st.button("Scan Nifty"): magic_scan(nifty50)

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty Watch")
    if st.button("Scan Bank Nifty"): magic_scan(banknifty)

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty Watch")
    if st.button("Scan Fin Nifty"): magic_scan(finnifty)

st.caption("Manohar - Variety Motors, Hyderabad")
