import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro", layout="wide")

# 2. Sidebar Folders
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్టాక్స్ లిస్ట్లు
nifty50 = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
banknifty = ["SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
finnifty = ["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS"]

# స్కానింగ్ ఫంక్షన్
def start_scan(stock_list):
    results = []
    for s in stock_list:
        try:
            d = yf.download(s, period="5d", interval="1d", progress=False)
            if not d.empty:
                lp = round(d['Close'].iloc[-1].item(), 2)
                ma = d['Close'].rolling(window=3).mean().iloc[-1]
                sig, bg = ("🚀 BUY", "#d4edda") if lp > ma else ("🔻 SELL", "#f8d7da")
                results.append({"Stock": s.replace(".NS",""), "Price": lp, "Signal": sig, "Color": bg})
        except: continue
    
    if results:
        df = pd.DataFrame(results)
        st.table(df.drop(columns=['Color']).style.apply(lambda x: [f"background-color: {df.loc[x.name, 'Color']}"]*len(x), axis=1))
    else:
        st.error("Data Not Found!")

# పేజీలు
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    sym = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
    if st.button("Check OI"):
        try:
            t = yf.Ticker(sym)
            o = t.option_chain(t.options[0])
            c, p = int(o.calls['openInterest'].sum()), int(o.puts['openInterest'].sum())
            st.write(f"Call OI: {c:,} | Put OI: {p:,}")
            if c > p: st.error("🔻 MARKET DOWN")
            else: st.success("🚀 MARKET UP")
        except: st.warning("No Data Available")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 Watch")
    if st.button("Scan Now"): start_scan(nifty50)

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty Watch")
    if st.button("Scan Now"): start_scan(banknifty)

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty Watch")
    if st.button("Scan Now"): start_scan(finnifty)

st.markdown("---")
st.caption("Manohar - Variety Motors, Hyderabad")
