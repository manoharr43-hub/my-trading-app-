import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="NSE AI EXCEL DOWNLOADER")
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("📥 NSE AI PRO V58 - EXCEL ONLY DOWNLOAD")

# NSE 200 STOCKS LIST (Sample - extendable)
nse_200 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "BHARTIARTL", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN", "HCLTECH", "ADANIENT", "SUNPHARMA", "TATASTEEL",
    "WIPRO", "ULTRACEMCO", "NTPC", "JSWSTEEL", "POWERGRID", "M&M", "ONGC", "HINDALCO", "TATAMOTORS", "ADANIPORTS"
]

def process_data(stock_list, period_days="7d", target_date=None):
    tickers = [s + ".NS" for s in stock_list]
    data = yf.download(tickers, period=period_days, interval="5m", group_by="ticker", threads=True)
    
    final_results = []
    
    for s in stock_list:
        try:
            df = data[s+".NS"].dropna()
            df.index = df.index.tz_convert(IST)
            
            # Filter for specific date if provided (for Backtest)
            if target_date:
                df = df[df.index.date == target_date].copy()
            
            if len(df) < 20: continue
            
            # Indicators
            df['EMA20'] = df['Close'].ewm(span=20).mean()
            df['Support'] = df['Low'].rolling(20).min()
            df['Resistance'] = df['High'].rolling(20).max()
            tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(14).mean()
            df['VolAvg'] = df['Volume'].rolling(20).mean()

            for i in range(1, len(df)):
                row, prev = df.iloc[i], df.iloc[i-1]
                
                signal = None
                if row['Close'] <= row['Support'] * 1.002: signal = "BUY SUPPORT"
                elif row['Close'] >= row['Resistance'] * 0.998: signal = "SELL RESISTANCE"
                elif prev['Close'] < prev['EMA20'] and row['Close'] > row['EMA20']: signal = "BUY CROSS"
                elif prev['Close'] > prev['EMA20'] and row['Close'] < row['EMA20']: signal = "SELL CROSS"
                
                if signal:
                    entry = round(row['Close'], 2)
                    atr = row['ATR']
                    sl = round(entry - (atr*1.5), 2) if "BUY" in signal else round(entry + (atr*1.5), 2)
                    target = round(entry + (atr*2), 2) if "BUY" in signal else round(entry - (atr*2), 2)
                    
                    final_results.append({
                        "DATE": df.index[i].strftime('%Y-%m-%d'),
                        "TIME": df.index[i].strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "ENTRY": entry,
                        "STOPLOSS": sl,
                        "TARGET": target,
                        "BIG_PLAYER": "YES" if row['Volume'] > row['VolAvg']*2 else "NO"
                    })
        except: continue
        
    return pd.DataFrame(final_results)

# ==========================================
# UI - DOWNLOAD BUTTONS
# ==========================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Live Signals")
    if st.button("Download Live Excel"):
        with st.spinner("Processing..."):
            res_df = process_data(nse_200, period_days="2d")
            if not res_df.empty:
                # Latest signals only for live
                live_df = res_df.sort_values(by=['DATE', 'TIME']).tail(50) 
                st.download_button("📥 Click to Save Live.csv", live_df.to_csv(index=False).encode('utf-8'), "NSE_Live_Signals.csv", "text/csv")
            else: st.error("No Signals Found")

with col2:
    st.subheader("📊 Backtest")
    b_date = st.date_input("Select Date", now.date() - timedelta(days=1))
    if st.button("Download Backtest Excel"):
        with st.spinner("Analyzing History..."):
            res_df = process_data(nse_200, period_days="7d", target_date=b_date)
            if not res_df.empty:
                st.download_button("📥 Click to Save Backtest.csv", res_df.to_csv(index=False).encode('utf-8'), f"Backtest_{b_date}.csv", "text/csv")
            else: st.error("No Data/Signals for this date")
