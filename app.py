import streamlit as st
import yfinance as yf
import pandas as pd

# Page Configuration
st.set_page_config(page_title="SMC Pro Max V18 - Variety Motors", layout="wide", page_icon="📈")

st.title("📈 SMC Pro Max V18 - Smart Trading Scanner")
st.caption("Variety Motors Edition - Santosh Nagar, Hyderabad")

# Stocks to scan
stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS", "TATAMOTORS.NS", "INFIBEAM.NS", "IREDA.NS"]

if st.button("🔍 Scan for Buy/Sell Signals"):
    results = []
    st.info("SMC Pro Max V18 Logic ని ఉపయోగించి మార్కెట్ ని స్కాన్ చేస్తున్నాను...")
    
    for symbol in stocks:
        try:
            # Fetching last 30 days of data for accurate Indicators
            df = yf.download(symbol, period="1mo", interval="15m", progress=False)
            
            if not df.empty:
                # 1. EMA Calculations
                df['ema9'] = df['Close'].ewm(span=9, adjust=False).mean()
                df['ema21'] = df['Close'].ewm(span=21, adjust=False).mean()
                
                # 2. VWAP Calculation
                df['vwap'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                
                # 3. Volume Analysis
                vol_ma = df['Volume'].rolling(window=20).mean()
                is_vol_high = df['Volume'].iloc[-1] > vol_ma.iloc[-1]
                
                # 4. Current Values
                price = df['Close'].iloc[-1]
                ema9_val = df['ema9'].iloc[-1]
                ema21_val = df['ema21'].iloc[-1]
                vwap_val = df['vwap'].iloc[-1]
                
                # Previous Values (for crossover)
                prev_ema9 = df['ema9'].iloc[-2]
                prev_ema21 = df['ema21'].iloc[-2]

                # 5. SMC V18 BUY/SELL Logic
                # Buy: EMA9 crosses above EMA21 + Price > VWAP + Volume High
                is_buy = (prev_ema9 <= prev_ema21 and ema9_val > ema21_val) and (price > vwap_val) and is_vol_high
                
                # Sell: EMA9 crosses below EMA21 + Price < VWAP + Volume High
                is_sell = (prev_ema9 >= prev_ema21 and ema9_val < ema21_val) and (price < vwap_val) and is_vol_high

                signal = "WAIT ⏳"
                if is_buy: signal = "🚀 STRONG BUY"
                elif is_sell: signal = "🔻 STRONG SELL"

                results.append({
                    "Stock": symbol.replace(".NS", ""),
                    "LTP": round(price, 2),
                    "Signal": signal,
                    "Vol Status": "STRONG 💪" if is_vol_high else "WEAK ⚠️"
                })
        except: pass
    
    if results:
        # Styling the table
        res_df = pd.DataFrame(results)
        st.table(res_df)
    else:
        st.error("Data Fetch చేయడం వీలు కాలేదు.")

st.markdown("---")
st.info("💡 గమనిక: '🚀 STRONG BUY' వస్తే మీ Pine Script ప్రకారం కండిషన్స్ అన్నీ మ్యాచ్ అయ్యాయని అర్థం.")
