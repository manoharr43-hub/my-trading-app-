import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Variety Motors Pro", layout="wide")

# 2. Sidebar Folders
st.sidebar.title("Trading Folders")
page = st.sidebar.selectbox("Select Folder", ["1. OI Strength", "2. Nifty 50", "3. Bank Nifty", "4. Fin Nifty"])

# స్కానింగ్ ఫంక్షన్ (With Buy/Sell Logic)
def start_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Scanning {s}...")
        try:
            # 5 రోజుల డేటాను డౌన్‌లోడ్ చేస్తున్నాం
            d = yf.download(s, period="5d", interval="1d", progress=False)
            if not d.empty:
                lp = round(d['Close'].iloc[-1].item(), 2)
                # 3 రోజుల మూవింగ్ యావరేజ్ లెక్కకడుతున్నాం
                ma = d['Close'].rolling(window=3).mean().iloc[-1]
                
                # Buy/Sell కండిషన్
                sig = "🚀 BUY" if lp > ma else "🔻 SELL"
                results.append({"Stock": s.replace(".NS",""), "Price": lp, "Signal": sig})
        except: continue
    
    status.empty()
    if results:
        # టేబుల్ రూపంలో డేటా చూపిస్తుంది
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
            st.metric("Call OI", f"{c:,}")
            st.metric("Put OI", f"{p:,}")
            if c > p: st.error("🔻 MARKET DOWN")
            else: st.success("🚀 MARKET UP")
        except: st.warning("Data error")

elif page == "2. Nifty 50":
    st.title("Nifty 50 Watch")
    # నిఫ్టీ టాప్ స్టాక్స్
    if st.button("Scan Now"): 
        start_scan(["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS"])

elif page == "3. Bank Nifty":
    st.title("Bank Nifty Watch")
    # బ్యాంక్ నిఫ్టీ టాప్ స్టాక్స్
    if st.button("Scan Now"): 
        start_scan(["SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "HDFCBANK.NS", "ICICIBANK.NS", "PNB.NS", "FEDERALBNK.NS"])

elif page == "4. Fin Nifty":
    st.title("Fin Nifty Watch")
    # ఫిన్ నిఫ్టీ టాప్ స్టాక్స్
    if st.button("Scan Now"): 
        start_scan(["BAJFINANCE.NS", "PFC.NS", "RECLTD.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS"])

st.markdown("---")
st.caption("Manohar - Variety Motors, Hyderabad")
