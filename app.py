import streamlit as st
import yfinance as yf

# Page Setup
st.set_page_config(page_title="Variety Motors Scanner", page_icon="🚀")
st.title("🚀 NSE Scanner - Variety Motors")

# Stocks List
stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS"]

if st.button("🔍 Scan Now"):
    st.info("Fetching Prices...")
    
    for symbol in stocks:
        try:
            # Ticker function usage
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                st.write(f"✅ **{symbol.replace('.NS','')}**: ₹{round(float(current_price), 2)}")
            else:
                st.warning(f"⚠️ No data for {symbol}")
        except Exception as e:
            st.error(f"❌ Error fetching {symbol}")

st.markdown("---")
st.caption("Developed by Manohar - Variety Motors, Hyderabad")
