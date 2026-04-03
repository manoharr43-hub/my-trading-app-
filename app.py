import streamlit as st
import yfinance as yf
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Variety Motors NSE Scanner", layout="wide", page_icon="🚀")

# Title and Styling
st.title("🚀 NSE Stock Scanner - Variety Motors Edition")
st.markdown("---")

# Sidebar for Inputs
st.sidebar.header("Scanner Settings")
stocks = "RELIANCE.NS, TCS.NS, HDFCBANK.NS, SBIN.NS, ICICIBANK.NS, TATAMOTORS.NS, INFIBEAM.NS"
input_stocks = st.sidebar.text_area("Enter Stock Symbols (NSE)", stocks, height=150)
stock_list = [s.strip() for s in input_stocks.split(",")]

# Timeframe Selection
tf = st.sidebar.selectbox("Select Timeframe", ("15m", "30m", "1h", "1d"), index=0)

# Main Button
if st.button("🔍 Scan Now"):
    results = []
    status = st.empty()
    status.info("Fetching Market Data... Please wait.")
    
    # Progress Bar
    prog = st.progress(0)
    
    for i, symbol in enumerate(stock_list):
        try:
            # period="5d" gives us enough historical data even on weekends
            data = yf.download(symbol, period="5d", interval=tf, progress=False)
            
            if not data.empty:
                last_row = data.iloc[-1]
                prev_row = data.iloc[-2]
                
                change = ((last_row['Close'] - prev_row['Close']) / prev_row['Close']) * 100
                
                results.append({
                    "Stock": symbol.replace(".NS", ""),
                    "LTP (Price)": round(float(last_row['Close']), 2),
                    "Change %": f"{round(float(change), 2)}%",
                    "High": round(float(last_row['High']), 2),
                    "Low": round(float(last_row['Low']), 2),
                    "Volume": int(last_row['Volume'])
                })
        except Exception as e:
            pass
        
        prog.progress((i + 1) / len(stock_list))
    
    status.empty()
    
    if results:
        df = pd.DataFrame(results)
        # Display as a nice table
        st.success(f"Successfully Scanned {len(results)} Stocks!")
        st.table(df)
        
        # Adding a simple Charting option
        selected_stock = st.selectbox("Select Stock to see History", df['Stock'].tolist())
        if selected_stock:
            chart_data = yf.download(f"{selected_stock}.NS", period="5d", interval=tf, progress=False)
            st.line_chart(chart_data['Close'])
            
    else:
        st.error("No data found. Please check the symbols or internet connection.")

st.markdown("---")
st.caption("Developed by Manohar - Variety Motors, Santosh Nagar, Hyderabad.")
