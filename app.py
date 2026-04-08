import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Live Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Pharma": ["SUNPHARMA.NS","DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","GLENMARK.NS"],
    "Energy": ["RELIANCE.NS","NTPC.NS","POWERGRID.NS","BPCL.NS","IOC.NS"]
}

# =============================
# 3. INDICATORS
# =============================
def analyze_stock(df):
    if df.empty or len(df)<15:
        return df, 0, 0
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss+1e-9)
    df['RSI'] = 100 - (100/(1+rs))
    
    # EMA
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)
    
    # Support & Resistance
    recent = df.iloc[-20:] if len(df)>=20 else df
    sup = recent['Low'].min()
    res = recent['High'].max()
    
    return df, round(res,2), round(sup,2)

# =============================
# 4. MAIN INTERFACE
# =============================
st.title("🛡️ NSE Live Scanner")
with st.sidebar:
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Trend Filter", ["UPTREND","DOWNTREND"], default=["UPTREND","DOWNTREND"])

# =============================
# 5. SCANNER FUNCTION
# =============================
def process_scanner(tickers):
    results = []
    data = yf.download(tickers, period="2d", interval="5m", group_by='ticker', progress=False)
    
    for t in tickers:
        try:
            df = data[t].dropna()
            df, res, sup = analyze_stock(df)
            if df.empty: continue
            last = df.iloc[-1]
            ltp = round(float(last['Close']),2)
            rsi = round(float(last['RSI']),1)
            change_pct = round(((ltp - df.iloc[0]['Open'])/df.iloc[0]['Open'])*100,2)
            trend = "UPTREND" if last['EMA20']>last['EMA50'] else "DOWNTREND"
            
            # Breakout / Breakdown
            status = "NORMAL"
            if ltp > res:
                status = "🚀 BREAKOUT" if rsi<70 else "⚠️ FAKE BREAKOUT"
            elif ltp < sup:
                status = "📉 BREAKDOWN" if rsi>30 else "⚠️ FAKE BREAKDOWN"
            
            # Signal
            signal = "BUY" if ltp>last['VWAP'] and trend=="UPTREND" else "SELL" if ltp<last['VWAP'] else "WAIT"
            
            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": change_pct,
                "RSI": rsi,
                "Support": sup,
                "Resistance": res,
                "Trend": trend,
                "Status": status,
                "Signal": signal
            })
        except Exception as e:
            continue
    return pd.DataFrame(results)

res_df = process_scanner(sectors[sector_name])

# =============================
# 6. DISPLAY
# =============================
if not res_df.empty:
    res_df = res_df[res_df['Trend'].isin(trend_filter)]
    
    def style_row(row):
        styles = ['']*len(row)
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color:#004d1a; color:white']*len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color:#4d0000; color:white']*len(row)
        elif "FAKE" in str(row.Status):
            styles = ['background-color:#634a00; color:white']*len(row)
        return styles
    
    st.dataframe(res_df.style.apply(style_row, axis=1), use_container_width=True)
    st.write(f"✅ Last Update: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("Searching for stocks...")
