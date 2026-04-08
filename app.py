import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Advanced Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. INDICATORS LOGIC
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 20:
        return df, 0, 0
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # Support & Resistance (Pivot Points last 20 bars)
    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()
    
    return df, float(res), float(sup)

# =============================
# 3. NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS"]
}

# =============================
# 4. MAIN INTERFACE
# =============================
st.title("🛡️ NSE Pro Live Smart Scanner")

with st.sidebar:
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Trend Filter", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])

# =============================
# 5. SCANNER FUNCTION
# =============================
def process_scanner(tickers):
    data = yf.download(tickers, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            df, res_p, sup_p = analyze_stock(df)
            last = df.iloc[-1]
            
            # --- ROUNDING LOGIC ---
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            res = round(res_p, 2)
            sup = round(sup_p, 2)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            
            # Trend
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Status
            status = "NORMAL"
            if ltp >= res:
                status = "🚀 STRONG BUY" if rsi < 70 else "⚠️ POSSIBLE FAKE"
            elif ltp <= sup:
                status = "📉 STRONG SELL" if rsi > 30 else "⚠️ POSSIBLE FAKE"
            
            # Signal
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" else "SELL" if ltp < last['VWAP'] and trend == "DOWNTREND" else "WAIT"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Support": sup,
                "Resistance": res,
                "Trend": trend,
                "Status": status,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# =============================
# 6. DISPLAY & STYLING
# =============================
res_df = process_scanner(sectors[sector_name])

if not res_df.empty:
    res_df = res_df[res_df['Trend'].isin(trend_filter)]
    
    # --- STYLING ---
    def style_table(row):
        styles = [''] * len(row)
        
        # Row Background based on strong Status only
        if "STRONG BUY" in str(row.Status):
            styles = ['background-color: #004d1a; color: white'] * len(row)
        elif "STRONG SELL" in str(row.Status):
            styles = ['background-color: #4d0000; color: white'] * len(row)
            
        # LTP proximity to Support/Resistance (visual cue only)
        ltp_idx = res_df.columns.get_loc('LTP')
        if abs(row.LTP - row.Support) / row.Support < 0.001:
            styles[ltp_idx] = 'color: #00ffff; font-weight: bold; font-size: 18px'
        elif abs(row.LTP - row.Resistance) / row.Resistance < 0.001:
            styles[ltp_idx] = 'color: #ff3131; font-weight: bold; font-size: 18px'
            
        return styles

    styled_df = res_df.style.apply(style_table, axis=1)\
        .set_properties(subset=['Support'], **{'color': '#00ffff', 'font-weight': 'bold'})\
        .set_properties(subset=['Resistance'], **{'color': '#ff3131', 'font-weight': 'bold'})

    st.dataframe(styled_df, use_container_width=True, height=500)
    
    st.success(f"Updated at: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("Searching for stocks...")
