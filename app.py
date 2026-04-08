import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG & REFRESH
# =============================
st.set_page_config(page_title="NSE Smart Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh") # 20 సెకన్ల రిఫ్రెష్

# =============================
# 2. INDICATORS LOGIC
# =============================
def get_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    return df

# =============================
# 3. NSE SECTORS ADDED
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","APOLLOHOSP.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","VEDL.NS"],
    "FMCG": ["ITC.NS","HINDUNILVR.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS","ADANIGREEN.NS"]
}

# =============================
# 4. SIDEBAR SETTINGS
# =============================
st.title("🚀 NSE Pro Smart Scanner")

with st.sidebar:
    st.header("Filters")
    sector_name = st.selectbox("Select NSE Sector", list(sectors.keys()))
    trend_select = st.multiselect("Select Trend", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])
    st.write("---")
    st.info("Scanner updates every 20 seconds.")

# =============================
# 5. DATA PROCESSING
# =============================
def process_data(ticker_list):
    data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in ticker_list:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            df = get_indicators(df)
            last = df.iloc[-1]
            
            ltp = round(float(last['Close']), 2)
            # RSI రౌండింగ్ ఇక్కడ చేసాను
            rsi_val = round(float(last['RSI']), 1)
            vwap_val = round(float(last['VWAP']), 2)
            
            # Trend Logic
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Signal Logic
            signal = "🚀 BUY" if ltp > vwap_val and rsi_val > 50 else "⚠️ SELL" if ltp < vwap_val else "HOLD"
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi_val,
                "Trend": trend,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# =============================
# 6. DISPLAY RESULTS
# =============================
res_df = process_data(sectors[sector_name])

if not res_df.empty:
    # Trend Filter
    res_df = res_df[res_df['Trend'].isin(trend_select)]
    
    # Styling - అక్షరాలు క్లియర్‌గా కనిపించడానికి మార్పులు చేసాను
    def highlight_rows(row):
        if 'BUY' in row.Signal:
            return ['background-color: #004d1a; color: white'] * len(row)
        elif 'SELL' in row.Signal:
            return ['background-color: #4d0000; color: white'] * len(row)
        return ['color: #d1d1d1'] * len(row)

    st.dataframe(res_df.style.apply(highlight_rows, axis=1), use_container_width=True, height=550)
    
    # Metrics
    c1, c2 = st.columns(2)
    c1.success(f"Sector: {sector_name}")
    c2.info(f"Last Update: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.warning("No data found for the selected criteria.")
