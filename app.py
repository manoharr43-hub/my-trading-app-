import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V58 - EXCEL EXPORT", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V58 - PRO TRADING SYSTEM")

# ==========================================
# NSE STOCKS (Top Stocks - You can add up to 200)
# ==========================================
nse_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "KOTAKBANK"]

# ==========================================
# INDICATORS & TARGET LOGIC
# ==========================================
def add_indicators(df):
    if df.empty: return df
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Support'] = df['Low'].rolling(20).min()
    df['Resistance'] = df['High'].rolling(20).max()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    
    # ATR for Dynamic SL/Target
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    df['ATR'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
    
    return df

def calculate_levels(row, signal):
    entry = round(row['Close'], 2)
    atr = row['ATR']
    
    if "BUY" in signal:
        sl = round(entry - (atr * 1.5), 2)
        target = round(entry + (atr * 2), 2)
    else: # SELL
        sl = round(entry + (atr * 1.5), 2)
        target = round(entry - (atr * 2), 2)
    
    return entry, sl, target

# ==========================================
# DATA FETCHING
# ==========================================
@st.cache_data(ttl=300)
def get_data(stock_list):
    tickers = [s + ".NS" for s in stock_list]
    return yf.download(tickers, period="5d", interval="5m", group_by="ticker", threads=True)

# ==========================================
# MAIN INTERFACE
# ==========================================
tab1, tab2 = st.tabs(["🚀 LIVE SCANNER", "📊 BACKTEST"])

with tab1:
    if st.button("🚀 SCAN MARKET & CALCULATE LEVELS"):
        data = get_data(nse_stocks)
        results = []
        
        for s in nse_stocks:
            try:
                df = data[s+".NS"].dropna()
                df = add_indicators(df)
                row, prev = df.iloc[-1], df.iloc[-2]
                
                # Signal Logic
                sig = None
                if row['Close'] <= row['Support'] * 1.002: sig = "BUY SUPPORT"
                elif row['Close'] >= row['Resistance'] * 0.998: sig = "SELL RESISTANCE"
                elif prev['Close'] < prev['EMA20'] and row['Close'] > row['EMA20']: sig = "BUY CROSS"
                elif prev['Close'] > prev['EMA20'] and row['Close'] < row['EMA20']: sig = "SELL CROSS"
                
                if sig:
                    entry, sl, target = calculate_levels(row, sig)
                    results.append({
                        "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "ENTRY": entry,
                        "STOP LOSS": sl,
                        "TARGET": target,
                        "BIG PLAYER": "🔥 YES" if row['Volume'] > row['VolAvg']*2 else "NO"
                    })
            except: continue
        
        if results:
            df_final = pd.DataFrame(results)
            st.dataframe(df_final, use_container_width=True)
            
            # EXCEL/CSV DOWNLOAD BUTTON
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results as CSV", csv, "NSE_Signals.csv", "text/csv")
        else:
            st.info("నో సిగ్నల్స్.")

with tab2:
    test_date = st.date_input("Select Date", now.date() - timedelta(days=1))
    if st.button("RUN BACKTEST"):
        data = get_data(nse_stocks)
        bt_logs = []
        
        for s in nse_stocks:
            try:
                df_all = data[s+".NS"].dropna()
                df_all.index = df_all.index.tz_convert(IST)
                df = add_indicators(df_all[df_all.index.date == test_date])
                
                for i in range(1, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    # Logic same as above...
                    # (Simplified for display)
                    if prev['Close'] < prev['EMA20'] and row['Close'] > row['EMA20']:
                        entry, sl, target = calculate_levels(row, "BUY")
                        bt_logs.append({"TIME": df.index[i].strftime('%H:%M'), "STOCK": s, "SIGNAL": "BUY", "ENTRY": entry, "SL": sl, "TARGET": target})
            except: continue
            
        if bt_logs:
            bt_df = pd.DataFrame(bt_logs)
            st.dataframe(bt_df)
            st.download_button("📥 Download Backtest Excel", bt_df.to_csv(index=False).encode('utf-8'), "Backtest.csv")
