import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")

# 2. Sidebar Navigation
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", [
    "1. OI Strength (All Index)",
    "2. Nifty 50 Stocks",
    "3. Bank Nifty Stocks",
    "4. Fin Nifty Stocks"
])

# Stocks Lists
nifty50_main = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "AXISBANK.NS"]
bank_nifty_stocks = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"]
fin_nifty_stocks = ["HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "PFC.NS", "RECLTD.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS"]

# స్కానింగ్ ఫంక్షన్ (With Safety Retry)
def run_stock_scan(stock_list):
    all_data = []
    status = st.empty()
    prog = st.progress(0)
    
    for i, symbol in enumerate(stock_list):
        status.info(f"Scanning {i+1}/{len(stock_list)}: {symbol}")
        try:
            # ఇక్కడ 1mo బదులు 5d వాడదాం (ఇది వేగంగా వస్తుంది)
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            
            if not df.empty:
                price = round(df['Close'].iloc[-1].item(), 2)
                sma = df['Close'].rolling(window=3).mean().iloc[-1]
                
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
        prog.progress((i + 1) / len(stock_list))
    
    status.empty()
    if all_data:
        df_display = pd.DataFrame(all_data)
        styled_df = df_display.drop(columns=['Style']).style.apply(lambda row: [row['Style']]*len(row), axis=1)
        st.table(styled_df)
    else:
        st.warning("ప్రస్తుతానికి సర్వర్ నుండి రెస్పాన్స్ రావడం లేదు. దయచేసి 'Reboot' చేసి 1 నిమిషం తర్వాత ప్రయత్నించండి.")

# --- FOLDER 1: OI STRENGTH ---
if folder == "1. OI Strength (All Index)":
    st.title("📊 Option OI Strength Analysis")
    idx = st.radio("Select Index", ["^NSEI", "^NSEBANK"])
    if st.button("🔍 Check OI Now"):
        try:
            ticker = yf.Ticker(idx)
            opt = ticker.option_chain(ticker.options[0])
            c_oi, p_oi = int(opt.calls['openInterest'].sum()), int(opt.puts['openInterest'].sum())
            col1, col2 = st.columns(2)
            col1.metric("Call OI", f"{c_oi:,}")
            col2.metric("Put OI", f"{p_oi:,}")
            if c_oi > p_oi: st.error("🔻 MARKET DOWN (Call Side Strong)")
            else: st.success("🚀 MARKET UP (Put Side Strong)")
        except: st.warning("ఆప్షన్స్ డేటా ప్రస్తుతం అందుబాటులో లేదు.")

# --- FOLDERS 2, 3, 4 ---
elif folder == "2. Nifty 50 Stocks":
    st.title("🎯 Nifty 50 Market Watch")
    if st.button("🚀 Scan Nifty 50"):
        run_stock_scan(nifty50_main)

elif folder == "3. Bank Nifty Stocks":
    st.title("🏦 Bank Nifty Market Watch")
    if st.button("🚀 Scan Bank Nifty"):
        run_stock_scan(bank_nifty_stocks)

elif folder == "4. Fin Nifty Stocks":
    st.title("💰 Fin Nifty Market Watch")
    if st.button("🚀 Scan Fin Nifty"):
        run_stock_scan(fin_nifty_stocks)

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
