import streamlit as st
import yfinance as yf
import pandas as pd

# Page Setup
st.set_page_config(page_title="SMC Pro Max V18", page_icon="🚀")
st.title("🚀 SMC Pro Max V18 - Smart Scanner")
st.caption("Variety Motors Edition - Hyderabad")

# Stocks List
stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "INFIBEAM.NS", "IREDA.NS"]

if st.button("🔍 Scan Now"):
    results = []
    st.info("SMC V18 లాజిక్ తో స్కాన్ చేస్తున్నాను...")
    
    for symbol in stocks:
        try:
            # Fetch data for 1 month to calculate EMA accurately
            df = yf.download(symbol, period="1mo", interval="15m", progress=False)
            
            if not df.empty and len(df) > 21:
                # Indicators Calculation
                ema9 = df['Close'].ewm(span=9, adjust=False).mean()
                ema21 = df['Close'].ewm(span=21, adjust=False).mean()
                vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                vol_ma = df['Volume'].rolling(window=20).mean()

                # Current & Previous Values
                price = df['Close'].iloc[-1]
                cur_ema9 = ema9.iloc[-1]
                cur_ema21 = ema21.iloc[-1]
                cur_vwap = vwap.iloc[-1]
                cur_vol = df['Volume'].iloc[-1]
                cur_vol_ma = vol_ma.iloc[-1]
                
                prev_ema9 = ema9.iloc[-2]
                prev_ema21 = ema21.iloc[-2]

                # SMC V18 Logic
                is_vol_high = cur_vol > cur_vol_ma
                is_buy = (prev_ema9 <= prev_ema21 and cur_ema9 > cur_ema21) and (price > cur_vwap) and is_vol_high
                is_sell = (prev_ema9 >= prev_ema21 and cur_ema9 < cur_ema21) and (price < cur_vwap) and is_vol_high

                signal = "WAIT ⏳"
                if is_buy: signal = "🚀 STRONG BUY"
                elif is_sell: signal = "🔻 STRONG SELL"

                results.append({
                    "Stock": symbol.replace(".NS", ""),
                    "LTP": round(price, 2),
                    "Signal": signal,
                    "Volume": "STRONG" if is_vol_high else "NORMAL"
                })
        except Exception as e:
            continue

    if results:
        res_df = pd.DataFrame(results)
        st.table(res_df)
    else:
        st.error("డేటా అందుబాటులో లేదు. కాసేపు ఆగి ప్రయత్నించండి.")

st.markdown("---")
st.info("💡 గమనిక: ధర VWAP కంటే పైన ఉండి, EMA 9 పైన క్రాస్ అయితేనే BUY సిగ్నల్ వస్తుంది.")
