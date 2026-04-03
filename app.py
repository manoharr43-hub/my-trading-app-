import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", ["1. Nifty 50 Scanner", "2. OI Strength & History"])

if folder == "1. Nifty 50 Scanner":
    st.title("🎯 Nifty 50 Market Watch")
    
    # స్టాక్స్ లిస్ట్ ని కొంచెం తగ్గించి టెస్ట్ చేద్దాం
    test_stocks = ["RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "ITC.NS"]
    
    if st.button("🚀 Start Scan"):
        all_data = []
        status = st.empty()
        
        for symbol in test_stocks:
            status.info(f"Scanning {symbol}...")
            try:
                # ఇక్కడ 'period' ని 1mo నుండి 5d కి మార్చాను, ఇది వేగంగా లోడ్ అవుతుంది
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d", interval="1d") 
                
                if not df.empty:
                    price = round(df['Close'].iloc[-1], 2)
                    # సింపుల్ మూవింగ్ యావరేజ్
                    sma = df['Close'].rolling(window=3).mean().iloc[-1]
                    
                    signal = "🚀 BUY" if price > sma else "🔻 SELL"
                    all_data.append({"Stock": symbol.replace(".NS",""), "LTP": price, "Signal": signal})
            except Exception as e:
                continue
        
        status.empty()
        if all_data:
            st.table(pd.DataFrame(all_data))
        else:
            st.warning("NSE సర్వర్ నుండి రెస్పాన్స్ రావడం లేదు. దయచేసి 5 నిమిషాల తర్వాత 'Start Scan' నొక్కండి.")

# Section 2 కోడ్ అలాగే ఉంటుంది...
elif folder == "2. OI Strength & History":
    st.title("📊 Option Analysis")
    st.write("సోమవారం మార్కెట్ ఓపెన్ అయ్యాక ఇక్కడ లైవ్ డేటా కనిపిస్తుంది.")
