import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Smart Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. INDICATORS LOGIC
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 50:
        return df, 0, 0
    
    # --- RSI Calculation ---
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # --- EMA Calculation ---
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # --- VWAP Calculation ---
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # --- Support & Resistance ---
    recent = df.iloc[-20:] if len(df) >= 20 else df
    sup = recent['Low'].min()
    res = recent['High'].max()
    
    return df, round(res, 2), round(sup, 2)

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
    sector_name = st.selectbox("Select NSE Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Select Trend", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])

# =============================
# 5. SCANNER FUNCTION
# =============================
def process_scanner(tickers):
    data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            df, res, sup = analyze_stock(df)
            last = df.iloc[-1]
            
            # --- LTP & Other Values Round & Shorten ---
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            
            # Trend Detection
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Status Alerts
            status = "NORMAL"
            if ltp >= res:
                status = "🚀 BREAKOUT" if rsi < 70 else "⚠️ FAKE BREAKOUT"
            elif ltp <= sup:
                status = "📉 BREAKDOWN" if rsi > 30 else "⚠️ FAKE BREAKDOWN"
            
            # Signal
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" else \
                     "SELL" if ltp < last['VWAP'] and trend == "DOWNTREND" else "WAIT"
            
            # --- Shortened numbers for LTP vs Resistance ---
            if len(str(ltp)) > 6:  # e.g., 1234.5678 → 1234.57
                ltp = float(f"{ltp:.2f}")
            if len(str(res)) > 6:
                res = float(f"{res:.2f}")
            if len(str(sup)) > 6:
                sup = float(f"{sup:.2f}")
            
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
    # Trend Filter Apply
    res_df = res_df[res_df['Trend'].isin(trend_filter)]
    
    def style_table(row):
        styles = [''] * len(row)
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color:#004d1a; color:white']*len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color:#4d0000; color:white']*len(row)
        elif "FAKE" in str(row.Status):
            styles = ['background-color:#634a00; color:white']*len(row)
        
        # Highlight LTP near Support/Resistance
        ltp_idx = res_df.columns.get_loc('LTP')
        if abs(row.LTP - row.Support) / row.Support < 0.001:
            styles[ltp_idx] = 'color:#00ffff; font-weight:bold; font-size:18px'
        elif abs(row.LTP - row.Resistance) / row.Resistance < 0.001:
            styles[ltp_idx] = 'color:#ff3131; font-weight:bold; font-size:18px'
        
        return styles
    
    styled_df = res_df.style.apply(style_table, axis=1)\
        .set_properties(subset=['Support'], **{'color':'#ff4d4d','font-weight':'bold'})\
        .set_properties(subset=['Resistance'], **{'color':'#00ff41','font-weight':'bold'})
