import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NSE Stock Scanner", layout="wide")
st.title("🚀 NSE Stock Scanner - Variety Motors Edition")

stocks = "RELIANCE.NS, TCS.NS, HDFCBANK.NS, SBIN.NS, ICICIBANK.NS, TATAMOTORS.NS"
input_stocks = st.sidebar.text_area("Stocks (comma separated)", stocks)
stock_list = [s.strip() for s in input_stocks.split(",")]

if st.button("Scan Now"):
    results = []
    for symbol in stock_list:
        try:
            data = yf.download(symbol, period="1d", interval="15m", progress=False)
            if not data.empty:
                last_price = data['Close'].iloc[-1]
                results.append({"Stock": symbol, "Price": round(float(last_price), 2)})
        except: pass
    
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.warning("No data found.")
        
