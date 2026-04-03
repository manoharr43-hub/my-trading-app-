import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors Trader Pro", layout="wide", page_icon="🚀")

# 2. Sidebar Navigation (Folders)
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", ["1. Nifty 50 Scanner", "2. OI Strength & History"])

# --- FOLDER 1: NIFTY 50 SCANNER (Section 1) ---
if folder == "1. Nifty 50 Scanner":
    st.title("🎯 Nifty 50 Market Watch")
    st.caption("SMC V18 Logic తో స్టాక్స్ ని స్కాన్ చేస్తుంది")
    
    nifty50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "INFY.NS", "ITC.NS"]
    
    if st.button("🚀 Start Scan"):
        all_data = []
        status = st.empty()
        
        for symbol in nifty50:
            status.info(f"Scanning {symbol}...")
            try:
                df = yf.download(symbol, period="5d", interval="15m", progress=False)
                if not df.empty:
                    price = round(df['Close'].iloc[-1].item(), 2)
                    ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
                    ema21 = df['Close'].ewm(span=21).mean().iloc[-1]
                    
                    signal = "WAIT ⏳"
                    if ema9 > ema21: signal = "🚀 BUY"
                    elif ema9 < ema21: signal = "🔻 SELL"
                    
                    all_data.append({"Stock": symbol.replace(".NS",""), "LTP": price, "Signal": signal})
            except: continue
        
        status.empty()
        if all_data:
            st.table(pd.DataFrame(all_data))
        else:
            st.error("డేటా లోడ్ అవ్వలేదు.")

# --- FOLDER 2: OI STRENGTH & HISTORY (Section 2) ---
elif folder == "2. OI Strength & History":
    st.title("📊 Option OI & Historical Observation")
    st.markdown("---")
    
    # Index Selection
    index_choice = st.selectbox("Select Index/Stock", ["^NSEI", "^NSEBANK", "RELIANCE.NS", "SBIN.NS"])
    
    # Part A: Current OI Strength
    st.subheader("🛡️ Live OI Strength (Call vs Put)")
    if st.button("🔍 Check OI Strength"):
        with st.spinner("Fetching Option Chain Data..."):
            try:
                ticker = yf.Ticker(index_choice)
                expiry = ticker.options[0]
                opt = ticker.option_chain(expiry)
                
                c_oi = int(opt.calls['openInterest'].sum())
                p_oi = int(opt.puts['openInterest'].sum())
                
                col1, col2 = st.columns(2)
                col1.metric("Total Call OI (Resistance)", f"{c_oi:,}")
                col2.metric("Total Put OI (Support)", f"{p_oi:,}")
                
                if c_oi > p_oi:
                    st.error("🔻 CALL SIDE OI బలంగా ఉంది: MARKET DOWN అయ్యే అవకాశం ఉంది")
                else:
                    st.success("🚀 PUT SIDE OI బలంగా ఉంది: MARKET UP అయ్యే అవకాశం ఉంది")
            except:
                st.warning("ఈ స్టాక్/ఇండెక్స్ కి ప్రస్తుతం ఆప్షన్స్ డేటా అందుబాటులో లేదు.")

    st.markdown("---")
    
    # Part B: Historical Observation (Calendar)
    st.subheader("📅 పాత డేటా పరిశీలన (History)")
    pick_date = st.date_input("ఏ తేదీ డేటా చూడాలనుకుంటున్నారు?", datetime.date.today() - datetime.timedelta(days=1))
    
    if st.button("📊 View Past Chart"):
        with st.spinner("చార్ట్ లోడ్ అవుతోంది..."):
            hist = yf.download(index_choice, start=pick_date, end=pick_date + datetime.timedelta(days=1), interval="15m")
            if not hist.empty:
                st.line_chart(hist['Close'])
                st.write(f"**{pick_date}** నాటి ధరల కదలిక పైన గ్రాఫ్ లో చూడవచ్చు.")
            else:
                st.warning("ఆ తేదీన మార్కెట్ సెలవు కావచ్చు లేదా డేటా అందుబాటులో లేదు.")

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
