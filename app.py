import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro", layout="wide")

# 2. Sidebar Folders
st.sidebar.title("Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్కానింగ్ ఫంక్షన్
def start_scan(stock_list):
    results = []
    for s in stock_list:
        try:
            d = yf.download(s, period="5d", interval="1d", progress=False)
            if not d.empty:
                lp = round(d['Close'].iloc[-1].item(), 2)
                results.append({"Stock": s.replace(".NS",""), "Price": lp})
        except: continue
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("No Data Found!")

# పేజీలు
if page == "1. OI Strength":
    st.title("Option Analysis")
    sym = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
    if st.button("Check OI Now"):
        try:
            t = yf.Ticker(sym)
            o = t.option_chain(t.options[0])
            c, p = int(o.calls['openInterest'].sum()), int(o.puts['openInterest'].sum())
            st.write(f"Call OI: {c:,} | Put OI: {p:,}")
        except: st.warning("Data error")

elif page == "2. Nifty 50":
    st.title("Nifty 50 Watch")
    if st.button("Scan Now"): start_scan(["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])

elif page == "3. Bank Nifty":
    st.title("Bank Nifty Watch")
    if st.button("Scan Now"): start_scan(["SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"])

elif page == "4. Fin Nifty":
    st.title("Fin Nifty Watch")
    if st.button("Scan Now"): start_scan(["BAJFINANCE.NS", "PFC.NS", "RECLTD.NS"])

st.caption("Manohar - Variety Motors")
