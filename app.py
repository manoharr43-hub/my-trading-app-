import streamlit as st
import yfinance as yf
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Variety Motors Trader Pro", layout="wide")

# Sidebar Folders
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", ["1. Nifty 50 Scanner", "2. OI Strength (Call/Put)"])

# --- FOLDER 1: NIFTY 50 SCANNER ---
if folder == "1. Nifty 50 Scanner":
    st.title("🎯 Nifty 50 Market Watch")
    nifty50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "INFY.NS", "ITC.NS"]
    
    if st.button("🚀 Start Scan"):
        all_data = []
        signals = []
        status = st.empty()
        
        for symbol in nifty50:
            status.info(f"Scanning {symbol}...")
            try:
                df = yf.download(symbol, period="5d", interval="15m", progress=False)
                if not df.empty:
                    price = round(df['Close'].iloc[-1].item(), 2)
                    # Simple Trend Logic
                    ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
                    ema21 = df['Close'].ewm(span=21).mean().iloc[-1]
                    
                    signal = "WAIT ⏳"
                    if ema9 > ema21: signal = "🚀 BUY"
                    elif ema9 < ema21: signal = "🔻 SELL"
                    
                    all_data.append({"Stock": symbol.replace(".NS",""), "LTP": price, "Signal": signal})
            except: continue
        
        status.empty()
        st.table(pd.DataFrame(all_data))

# --- FOLDER 2: OI STRENGTH ---
elif folder == "2. OI Strength (Call/Put)":
    st.title("📊 Option OI Strength Analysis")
    st.markdown("---")
    index_choice = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
    
    if st.button("🔍 Check OI Strength"):
        with st.spinner("Fetching Option Chain Data..."):
            try:
                ticker = yf.Ticker(index_choice)
                expiry = ticker.options[0]
                opt = ticker.option_chain(expiry)
                
                c_oi = int(opt.calls['openInterest'].sum())
                p_oi = int(opt.puts['openInterest'].sum())
                
                col1, col2 = st.columns(2)
                col1.metric("Call OI (Resistance)", f"{c_oi:,}")
                col2.metric("Put OI (Support)", f"{p_oi:,}")
                
                st.markdown("---")
                if c_oi > p_oi:
                    st.error("🔻 CALL SIDE OI బలంగా ఉంది (Sellers are active at Top)")
                    st.subheader("వ్యూ: MARKET DOWN అయ్యే అవకాశం ఉంది 📉")
                else:
                    st.success("🚀 PUT SIDE OI బలంగా ఉంది (Buyers are active at Bottom)")
                    st.subheader("వ్యూ: MARKET UP అయ్యే అవకాశం ఉంది 📈")
                    
            except:
                st.error("ప్రస్తుతానికి డేటా అందుబాటులో లేదు. కాసేపు ఆగి ప్రయత్నించండి.")

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
