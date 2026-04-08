import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. SETUP
st.set_page_config(page_title="NSE Smart Scanner", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# 2. INDICATORS
def get_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9) # 0 డివిజన్ రాకుండా
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df

# 3. STOCKS
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"]
}

st.title("⚡ NSE Pro Smart Scanner")
sector_name = st.sidebar.selectbox("Select Sector", list(sectors.keys()))

# 4. DATA PROCESSING
def process_stocks(tickers):
    data = yf.download(tickers, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            df = get_indicators(df)
            last = df.iloc[-1]
            
            # Simple Logic
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            vwap = round(float(last['VWAP']), 2)
            
            signal = "🚀 BUY" if ltp > vwap and rsi > 50 else "⚠️ SELL" if ltp < vwap else "HOLD"
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# 5. DISPLAY
res_df = process_stocks(sectors[sector_name])

if not res_df.empty:
    # మీ ఫోటోలో వచ్చిన ఎర్రర్‌ని నివారించడానికి సింపుల్ హైలైటింగ్ పద్ధతి:
    def highlight_signal(row):
        color = 'background-color: #004d1a' if 'BUY' in row.Signal else 'background-color: #4d0000' if 'SELL' in row.Signal else ''
        return [color] * len(row)

    # ఇక్కడ తక్కువ ఫార్మాటింగ్ వాడి రిస్క్ తగ్గించాను
    st.dataframe(res_df.style.apply(highlight_signal, axis=1), use_container_width=True, height=500)
    
    st.success(f"Updated at: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("Loading Data... Please wait.")
