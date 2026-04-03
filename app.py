import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. Page Config
st.set_page_config(page_title="Variety Motors - Nifty 50 Scanner", layout="wide")

# 2. Sidebar Navigation
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", ["1. Nifty 50 Scanner", "2. OI Strength & History"])

# Nifty 50 Full List
nifty50_list = [
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

if folder == "1. Nifty 50 Scanner":
    st.title("🎯 Nifty 50 Full Market Watch")
    st.caption(f"Last Update: {time.strftime('%H:%M:%S')}")

    if st.button("🚀 Start Full 50 Scan"):
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, symbol in enumerate(nifty50_list):
            status_text.text(f"Scanning {i+1}/50: {symbol}")
            try:
                # Fast Download
                df = yf.download(symbol, period="5d", interval="1d", progress=False)
                if not df.empty:
                    price = round(df['Close'].iloc[-1], 2)
                    sma = round(df['Close'].rolling(window=3).mean().iloc[-1], 2)
                    
                    if price > sma:
                        signal, color = "🚀 BUY", "background-color: #d4edda; color: #155724;"
                    else:
                        signal, color = "🔻 SELL", "background-color: #f8d7da; color: #721c24;"
                    
                    all_data.append({
                        "Stock": symbol.replace(".NS",""),
                        "LTP": price,
                        "Signal": signal,
                        "Style": color
                    })
            except:
                continue
            progress_bar.progress((i + 1) / len(nifty50_list))

        status_text.empty()
        if all_data:
            df_display = pd.DataFrame(all_data)
            # Apply Colors
            def apply_style(row):
                return [row['Style']] * len(row)
            
            styled_df = df_display.drop(columns=['Style']).style.apply(apply_style, axis=1)
            st.dataframe(styled_df, height=600, use_container_width=True)
        else:
            st.error("డేటా లోడ్ అవ్వలేదు.")

elif folder == "2. OI Strength & History":
    st.title("📊 Option Analysis")
    st.write("సోమవారం మార్కెట్ సమయంలో ఇక్కడ లైవ్ డేటా అప్‌డేట్ అవుతుంది.")

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
