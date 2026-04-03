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
            # Fetch data for 1 month
            df = yf.download(symbol, period="1mo", interval="15m", progress=False)
            
            # Check if data is enough (Error Fix: Added more checks)
            if df is not None and len(df) > 30:
                # Calculate Indicators
                ema9 = df['Close'].ewm(span=9, adjust=False).mean()
                ema21 = df['Close'].ewm(span=21, adjust=False).mean()
                vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                vol_ma = df['Volume'].rolling(window=20).mean()

                # Get the last valid values as single numbers (.item() ensures no ValueError)
                price = df['Close'].iloc[-1].item()
                cur_ema9 = ema9.iloc[-1].item()
                cur_ema21 = ema21.iloc[-1].item()
                cur_vwap = vwap.iloc[-1].item()
                cur_vol = df['Volume'].iloc[-1].item()
                cur_vol_ma = vol_ma.iloc[-1].item()
                
                prev_ema9 = ema9.iloc[-2].item()
                prev_ema21 = ema21.iloc[-2].item()

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
                    "Volume": "STRONG 💪" if is_vol_high else "NORMAL"
                })
        except Exception as e:
            continue

    if results:
        res_df = pd.DataFrame(results)
        st.table(res_df)
    else:
        st.error("డేటా లోడ్ అవ్వలేదు. నెట్వర్క్ ఒకసారి చెక్ చేయండి.")

st.markdown("---")
st.info("💡 గమనిక: మార్కెట్ క్లోజ్ అయి ఉన్నప్పుడు చివరి ట్రేడింగ్ డే డేటా కనిపిస్తుంది.")
