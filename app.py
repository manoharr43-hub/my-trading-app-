import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Variety Motors Multi-Scanner", layout="wide")

# 2. Sidebar Navigation (Folders 1, 2, 3, 4)
st.sidebar.title("📁 Trading Folders")
folder = st.sidebar.selectbox("Select Folder", [
    "1. OI Strength (All Index)",
    "2. Nifty 50 Stocks",
    "3. Bank Nifty Stocks",
    "4. Fin Nifty Stocks"
])

# స్టాక్స్ లిస్ట్ లు
nifty50_main = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
bank_nifty_stocks = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "AUBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"]
fin_nifty_stocks = ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "PFC.NS", "RECLTD.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS"]

# స్కానింగ్ ఫంక్షన్ (Common Function)
def run_stock_scan(stock_list):
    all_data = []
    prog = st.progress(0)
    for i, symbol in enumerate(stock_list):
        try:
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if not df.empty:
                price = round(df['Close'].iloc[-1].item(), 2)
                sma = df['Close'].rolling(window=3).mean().iloc[-1]
                signal, color = ("🚀 BUY", "background-color: #d4edda;") if price > sma else ("🔻 SELL", "background-color: #f8d7da;")
                all_data.append({"Stock": symbol.replace(".NS",""), "LTP": price, "Signal": signal, "Style": color})
        except: continue
        prog.progress((i + 1) / len(stock_list))
    
    if all_data:
        df_display = pd.DataFrame(all_data)
        styled_df = df_display.drop(columns=['Style']).style.apply(lambda row: [row['Style']]*len(row), axis=1)
        st.table(styled_df)
    else:
        st.error("డేటా అందడం లేదు. మళ్ళీ ప్రయత్నించండి.")

# --- FOLDER 1: OI STRENGTH ---
if folder == "1. OI Strength (All Index)":
    st.title("📊 Option OI Strength Analysis")
    idx = st.radio("Select Index", ["^NSEI (Nifty)", "^NSEBANK (Bank Nifty)"])
    if st.button("🔍 Check OI Now"):
        try:
            ticker = yf.Ticker(idx)
            opt = ticker.option_chain(ticker.options[0])
            c_oi, p_oi = int(opt.calls['openInterest'].sum()), int(opt.puts['openInterest'].sum())
            st.metric("Call OI", f"{c_oi:,}")
            st.metric("Put OI", f"{p_oi:,}")
            if c_oi > p_oi: st.error("🔻 MARKET DOWN (Call Side Strong)")
            else: st.success("🚀 MARKET UP (Put Side Strong)")
        except: st.warning("డేటా అందుబాటులో లేదు.")

# --- FOLDER 2: NIFTY 50 ---
elif folder == "2. Nifty 50 Stocks":
    st.title("🎯 Nifty 50 Market Watch")
    if st.button("🚀 Scan Nifty 50"):
        run_stock_scan(nifty50_main)

# --- FOLDER 3: BANK NIFTY ---
elif folder == "3. Bank Nifty Stocks":
    st.title("🏦 Bank Nifty Market Watch")
    if st.button("🚀 Scan Bank Nifty"):
        run_stock_scan(bank_nifty_stocks)

# --- FOLDER 4: FIN NIFTY ---
elif folder == "4. Fin Nifty Stocks":
    st.title("💰 Fin Nifty Market Watch")
    if st.button("🚀 Scan Fin Nifty"):
        run_stock_scan(fin_nifty_stocks)

st.markdown("---")
st.caption("Developed for Manohar - Variety Motors, Hyderabad")
