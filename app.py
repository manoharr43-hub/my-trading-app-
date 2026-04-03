import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st.title("🎯 Nifty 50 Smart Scanner - V18")

nifty50_stocks = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
]

if st.button("🚀 Run Full Market Scan"):
    signals = []
    all_prices = []
    
    status = st.empty()
    prog = st.progress(0)
    
    for i, symbol in enumerate(nifty50_stocks):
        status.info(f"Scanning {symbol}...")
        try:
            df = yf.download(symbol, period="1mo", interval="15m", progress=False)
            if not df.empty and len(df) > 30:
                # Indicators
                ema9 = df['Close'].ewm(span=9, adjust=False).mean()
                ema21 = df['Close'].ewm(span=21, adjust=False).mean()
                vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                
                price = df['Close'].iloc[-1].item()
                cur_ema9, cur_ema21 = ema9.iloc[-1].item(), ema21.iloc[-1].item()
                prev_ema9, prev_ema21 = ema9.iloc[-2].item(), ema21.iloc[-2].item()
                cur_vwap = vwap.iloc[-1].item()
                
                # Logic
                is_buy = (prev_ema9 <= prev_ema21 and cur_ema9 > cur_ema21) and (price > cur_vwap)
                is_sell = (prev_ema9 >= prev_ema21 and cur_ema9 < cur_ema21) and (price < cur_vwap)
                
                stock_name = symbol.replace(".NS", "")
                
                # Table 1: Filtered Signals
                if is_buy: signals.append({"Stock": stock_name, "Price": round(price, 2), "Signal": "🚀 BUY"})
                if is_sell: signals.append({"Stock": stock_name, "Price": round(price, 2), "Signal": "🔻 SELL"})
                
                # Table 2: All Prices
                all_prices.append({"Stock": stock_name, "LTP": round(price, 2)})
        except: continue
        prog.progress((i+1)/50)

    status.empty()
    
    # Display Table 1
    st.subheader("🔥 Best Trading Setups (SMC V18)")
    if signals:
        st.table(pd.DataFrame(signals))
    else:
        st.warning("ప్రస్తుతానికి పక్కా సిగ్నల్స్ ఏవీ లేవు. 'WAIT' చేయండి.")

    # Display Table 2
    st.subheader("📊 Nifty 50 - All Stock Prices")
    st.dataframe(pd.DataFrame(all_prices)) # ఇది ఒక పెద్ద లిస్ట్ లా కనిపిస్తుంది

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors")
