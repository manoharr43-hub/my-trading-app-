import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Advanced Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. INDICATORS & ANALYSIS
# =============================
def analyze_stock(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA & VWAP
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # SUPPORT & RESISTANCE (Pivot Points)
    high_p = df['High'].iloc[-20:-1].max()
    low_p = df['Low'].iloc[-20:-1].min()
    
    return df, high_p, low_p

# =============================
# 3. SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"]
}

# =============================
# 4. MAIN INTERFACE
# =============================
st.title("🛡️ NSE Pro Scanner (Breakout Detection)")

with st.sidebar:
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Filter Trend", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])

def process_scanner(ticker_list):
    data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in ticker_list:
        try:
            df = data[t].dropna()
            if len(df) < 30: continue
            
            df, res, sup = analyze_stock(df)
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # --- BREAKOUT & FAKE BREAKOUT LOGIC ---
            status = "NORMAL"
            # Resistance Breakout
            if last['Close'] > res:
                if rsi < 70: status = "🚀 BREAKOUT"
                else: status = "⚠️ FAKE BREAKOUT" # Overbought RSI with breakout is often fake
            # Support Breakdown
            elif last['Close'] < sup:
                if rsi > 30: status = "📉 BREAKDOWN"
                else: status = "⚠️ FAKE BREAKDOWN"
            
            # Signal
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" else "SELL" if ltp < last['VWAP'] else "WAIT"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Support": round(sup, 2),
                "Resistance": round(res, 2),
                "Trend": trend,
                "Status": status,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# =============================
# 5. DISPLAY & STYLING
# =============================
res_df = process_scanner(sectors[sector_name])

if not res_df.empty:
    # Filtering
    res_df = res_df[res_df['Trend'].isin(trend_filter)]
    
    def style_output(row):
        styles = [''] * len(row)
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color: #004d1a; color: white'] * len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color: #4d0000; color: white'] * len(row)
        elif "FAKE" in str(row.Status):
            styles = ['background-color: #634a00; color: white'] * len(row)
        return styles

    st.dataframe(res_df.style.apply(style_output, axis=1), use_container_width=True)
    
    st.write(f"✅ Last Update: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("Searching for stocks...")
