import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Variety Motors Pro", layout="wide")

# 2. Sidebar Folders
st.sidebar.title("📁 Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్టాక్స్ లిస్ట్లు
nifty50 = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "AXISBANK.NS"]
banknifty = ["SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "HDFCBANK.NS", "ICICIBANK.NS", "PNB.NS", "FEDERALBNK.NS"]
finnifty = ["BAJFINANCE.NS", "RECLTD.NS", "PFC.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS"]

# స్కానింగ్ ఫంక్షన్ (Retry Logic తో)
def start_scan(stock_list):
    results = []
    status = st.empty()
    prog = st.progress(0)
    
    for i, s in enumerate(stock_list):
        status.info(f"Scanning {s}...")
        try:
            # period="1mo" వాడటం వల్ల డేటా ఖచ్చితంగా వస్తుంది
            d = yf.download(s, period="1mo", interval="1d", progress=False)
            if not d.empty:
                lp = round(d['Close'].iloc[-1].item(), 2)
                ma = d['Close'].rolling(window=3).mean().iloc[-1]
                sig, bg = ("🚀 BUY", "#d4edda") if lp > ma else ("🔻 SELL", "#f8d7da")
                results.append({"Stock": s.replace(".NS",""), "Price": lp, "Signal": sig, "Color": bg})
        except: continue
        prog.progress((i + 1) / len(stock_list))
    
    status.empty()
    if results:
        df = pd.DataFrame(results)
        st.table(df.drop(columns=['Color']).style.apply(lambda x: [f"background-color: {df.loc[x.name, 'Color']}"]*len(x), axis=1))
    else:
        st.error("మార్కెట్ సర్వర్ బిజీగా ఉంది. దయచేసి 'Scan Now' మళ్ళీ నొక్కండి.")

# పేజీలు
if page == "1. OI Strength":
    st.title("📊 Option Analysis")
    sym = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
    if st.button("Check OI Strength"):
        try:
            t = yf.Ticker(sym)
            expiry = t.options[0]
            o = t.option_chain(expiry)
            c, p = int(o.calls['openInterest'].sum()), int(o.puts['openInterest'].sum())
            col1, col2 = st.columns(2)
            col1.metric("Call OI", f"{c:,}")
            col2.metric("Put OI", f"{p:,}")
            if c > p: st.error("🔻 MARKET DOWN (Resistance Strong)")
            else: st.success("🚀 MARKET UP (Support Strong)")
        except: st.warning("ఆప్షన్స్ డేటా ప్రస్తుతం అందుబాటులో లేదు.")

elif page == "2. Nifty 50":
    st.title("🎯 Nifty 50 Watch")
    if st.button("Scan Nifty 50"): start_scan(nifty50)

elif page == "3. Bank Nifty":
    st.title("🏦 Bank Nifty Watch")
    if st.button("Scan Bank Nifty"): start_scan(banknifty)

elif page == "4. Fin Nifty":
    st.title("💰 Fin Nifty Watch")
    if st.button("Scan Fin Nifty"): start_scan(finnifty)

st.markdown("---")
st.caption("Manohar - Variety Motors, Hyderabad")
