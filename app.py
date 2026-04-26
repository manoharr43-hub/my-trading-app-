import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE AI PRO V23 - LIVE SCANNER", layout="wide")
st.title("🚀 NSE AI PRO V23 - Multi-Sector Live Scanner")

st_autorefresh(interval=300000, key="auto_scan") # 5 mins refresh

# =============================
# SECTOR STOCK LIST
# =============================
sectors = {
    "NIFTY 50": ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "BHARTIARTL", "ITC", "HINDUNILVR", "LT"],
    "BANK NIFTY": ["SBIN", "HDFCBANK", "ICICIBANK", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "PNB", "FEDERALBNK", "IDFCFIRSTB"],
    "IT SECTOR": ["TCS", "INFY", "WIPRO", "HCLTECH", "LTIM", "TECHM", "COFORGE", "PERSISTENT"],
    "AUTO SECTOR": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "TVSMOTOR", "ASHOKLEY"],
    "METAL SECTOR": ["TATASTEEL", "JINDALSTEL", "HINDALCO", "JSWSTEEL", "VEDL", "NMDC", "SAIL"]
}

# =============================
# SCANNING ENGINE
# =============================
def perform_scan():
    results = []
    all_symbols = [stock for sublist in sectors.values() for stock in sublist]
    total = len(all_symbols)
    
    progress_text = "Scanning NSE Stocks... Please wait."
    my_bar = st.progress(0, text=progress_text)
    
    for i, symbol in enumerate(all_symbols):
        try:
            ticker = f"{symbol}.NS"
            # 15 min timeframe lo scan chesthunnam
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            # Indicators Calculation
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['Date'] = df.index.date
            df['VWAP'] = ( ( (df['High']+df['Low']+df['Close'])/3 ) * df['Volume'] ).groupby(df['Date']).cumsum() / df['Volume'].groupby(df['Date']).cumsum()
            
            last = df.iloc[-1]
            
            # Signal Logic
            signal = "NEUTRAL"
            if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
                signal = "STRONG BUY 🟢"
            elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
                signal = "STRONG SELL 🔴"
            
            if signal != "NEUTRAL":
                results.append({
                    "Stock": symbol,
                    "Price": round(last['Close'], 2),
                    "Signal": signal,
                    "VWAP": round(last['VWAP'], 2),
                    "Volume": last['Volume']
                })
        except:
            pass
        my_bar.progress((i + 1) / total)
    
    my_bar.empty()
    return pd.DataFrame(results)

# =============================
# MAIN INTERFACE
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 INDIVIDUAL CHART"])

with tab1:
    st.subheader("Filter All Sector Stocks for Entry")
    if st.button("🚀 Start Full Market Scan"):
        scan_df = perform_scan()
        
        if not scan_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("✅ BUY CONFIRMATION LIST")
                buys = scan_df[scan_df['Signal'].str.contains("BUY")]
                st.dataframe(buys, use_container_width=True, hide_index=True)
                
            with col2:
                st.error("❌ SELL CONFIRMATION LIST")
                sells = scan_df[scan_df['Signal'].str.contains("SELL")]
                st.dataframe(sells, use_container_width=True, hide_index=True)
        else:
            st.info("No strong signals detected right now. Try again later.")

with tab2:
    st.info("Scanner lo vachina stock name ikkada select chesi chart chudandi.")
    all_stocks = [s for sub in sectors.values() for s in sub]
    sel_stock = st.selectbox("Select Stock to Analyze", all_stocks)
    # Meeru mundu vadina chart code ikkada add cheskovachu
    st.write(f"Displaying analysis for {sel_stock}...")
