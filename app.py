import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
from xgboost import XGBClassifier
import warnings

warnings.filterwarnings('ignore')

# 1. PAGE SETUP
st.set_page_config(page_title="NSE AI PRO V11.12 PRO", layout="wide")

# 2. BULK DATA FETCHING
@st.cache_data(ttl=3600)
def get_bulk_data(tickers):
    return yf.download(tickers, period="6mo", interval="1d", group_by='ticker', auto_adjust=True, progress=False)

# 3. ADVANCED ANALYTICS ENGINE
def compute_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["RSI"] = 100 - (100 / (1 + df["Close"].diff().clip(lower=0).rolling(14).mean() / -df["Close"].diff().clip(upper=0).rolling(14).mean()))
    df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df["Volume"].cumsum()
    return df

# 4. MAIN INTERFACE
st.title("🚀 NSE AI PRO V11.12 - Institutional Ultimate")

tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS", "TATAMOTORS.NS"]

if st.button("🚀 RUN FULL SCANNER"):
    with st.spinner("Analyzing Institutional Flow..."):
        all_data = get_bulk_data(tickers)
        results = []
        
        for ticker in tickers:
            if ticker in all_data.columns.levels[0]:
                df = all_data[ticker].copy()
                df = compute_indicators(df)
                
                # Logic
                last = df.iloc[-1]
                trend = "BULLISH 🚀" if last["EMA20"] > last["EMA50"] else "BEARISH 🔻"
                rsi_sig = "Overbought" if last["RSI"] > 70 else "Oversold" if last["RSI"] < 30 else "Normal"
                
                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "LTP": round(last["Close"], 2),
                    "EMA20": round(last["EMA20"], 2),
                    "RSI": round(last["RSI"], 2),
                    "Trend": trend,
                    "RSI_Status": rsi_sig
                })
        
        final_df = pd.DataFrame(results)
        
        # Color Formatting
        def color_df(row):
            colors = [''] * len(row)
            if "BULLISH" in str(row['Trend']): colors[4] = 'background-color: #d4edda'
            if "BEARISH" in str(row['Trend']): colors[4] = 'background-color: #f8d7da'
            return colors

        st.dataframe(final_df.style.apply(color_df, axis=1), use_container_width=True)
        st.success("Analysis Complete!")

# 5. SMC EDUCATIONAL REFERENCE
st.markdown("---")
st.subheader("💡 Institutional Concept Reference")
st.write("మార్కెట్ స్ట్రక్చర్ మరియు స్మార్ట్ మనీ కాన్సెప్ట్స్ గురించి మరింత అవగాహన కోసం ఈ డయాగ్రామ్ చూడండి:")

