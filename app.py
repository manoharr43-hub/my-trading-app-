import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="SMC Pro Max Scanner", layout="wide")
st.title("🚀 SMC Pro Max - NSE Stock Scanner")

stocks = "RELIANCE.NS, TCS.NS, HDFCBANK.NS, SBIN.NS, ICICIBANK.NS, TATAMOTORS.NS, INFY.NS"
input_stocks = st.sidebar.text_area("Stocks (comma separated)", stocks)
stock_list = [s.strip() for s in input_stocks.split(",")]
tf = st.sidebar.selectbox("Timeframe", ("15m", "30m", "1h", "1d"), index=0)

if st.button("Scan Now"):
    results = []
    prog = st.progress(0)
    for i, symbol in enumerate(stock_list):
        try:
            data = yf.download(symbol, period="5d", interval=tf, progress=False)
            if data.empty: continue
            data['EMA9'] = ta.ema(data['Close'], length=9)
            data['EMA21'] = ta.ema(data['Close'], length=21)
            data['VWAP'] = ta.vwap(data['High'], data['Low'], data['Close'], data['Volume'])
            data['VolMA'] = ta.sma(data['Volume'], length=20)
            st_data = ta.supertrend(data['High'], data['Low'], data['Close'], length=10, multiplier=3)
            data['ST_Dir'] = st_data['SUPERTd_10_3.0']
            last = data.iloc[-1]
            if last['EMA9'] > last['EMA21'] and last['Close'] > last['VWAP'] and last['Volume'] > last['VolMA'] and last['ST_Dir'] == 1:
                results.append({"Stock": symbol, "Price": round(last['Close'], 2), "Open=Low": "Yes" if last['Open'] == last['Low'] else "No"})
        except: pass
        prog.progress((i + 1) / len(stock_list))
    if results:
        st.table(pd.DataFrame(results))
        selected = st.selectbox("View Chart", [r['Stock'] for r in results])
        if selected:
            tv_s = "NSE:" + selected.replace(".NS", "")
            chart = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol={tv_s}&interval={tf.replace("m","")}&theme=light" width="100%" height="500"></iframe>'
            st.components.v1.html(chart, height=520)
    else:
        st.warning("No Signals Found.")
