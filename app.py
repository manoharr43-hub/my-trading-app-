import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors Trader Pro", layout="wide", page_icon="🚀")

# 2. Sidebar Navigation
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", ["1. Nifty 50 Scanner", "2. OI Strength & History"])

# --- FOLDER 1: NIFTY 50 SCANNER ---
if folder == "1. Nifty 50 Scanner":
    st.title("🎯 Nifty 50 Market Watch")
    nifty50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "INFY.NS", "ITC.NS"]
    
    if st.button("🚀 Start Scan"):
        all_data = []
        status = st.empty()
        
        for symbol in nifty50:
            status.info(f"Scanning {symbol}...")
            try:
                # period="5d" కి బదులు "1mo" వాడదాం, డేటా లోడ్ అవ్వడానికి సులభంగా ఉంటుంది
                df = yf.download(symbol, period="1mo", interval="15m", progress=False)
                if not df.empty:
                    price = round(df['Close'].iloc[-1].item(), 2)
                    # Indicators
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
            st.error("ప్రస్తుతానికి సర్వర్ నుండి డేటా అందడం లేదు. దయచేసి రీబూట్ చేయండి.")

# --- FOLDER 2: OI STRENGTH & HISTORY ---
elif folder == "2. OI Strength & History":
    st.title("📊 Option OI & History")
    index_choice = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
    
    # OI Strength
    if st.button("🔍 Check OI Strength"):
        try:
            ticker = yf.Ticker(index_choice)
            expiry = ticker.options[0]
            opt = ticker.option_chain(expiry)
            c_oi, p_oi = int(opt.calls['openInterest'].sum()), int(opt.puts['openInterest'].sum())
            
            st.metric("Call OI", f"{c_oi:,}")
            st.metric("Put OI", f"{p_oi:,}")
            if c_oi > p_oi: st.error("🔻 MARKET DOWN (Call Side Strong)")
            else: st.success("🚀 MARKET UP (Put Side Strong)")
        except: st.warning("ఆప్షన్స్ డేటా ప్రస్తుతం అందుబాటులో లేదు.")

    st.markdown("---")
    # History
    pick_date = st.date_input("Select Date", datetime.date.today() - datetime.timedelta(days=1))
    if st.button("📊 View Chart"):
        hist = yf.download(index_choice, start=pick_date, end=pick_date + datetime.timedelta(days=1), interval="15m")
        if not hist.empty: st.line_chart(hist['Close'])
        else: st.warning("డేటా లేదు.")

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
