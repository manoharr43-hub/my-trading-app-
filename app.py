import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Volume Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. INDICATORS LOGIC
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 50:
        return df, 0, 0, 0
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # Volume Strength Calculation
    avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    vol_ratio = last_vol / (avg_vol + 1e-9)
    
    # Support & Resistance
    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()
    
    return df, round(float(res), 2), round(float(sup), 2), vol_ratio

# =============================
# 3. NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS"]
}

# =============================
# 4. INTERFACE - Sector ఇక్కడ ఉంటుంది
# =============================
st.title("🛡️ NSE Pro Live Smart Scanner")

# Sidebar లో Sector కనిపించేలా స్పష్టంగా మార్చాను
with st.sidebar:
    st.header("Select Market Filter")
    sector_name = st.selectbox("Current Sector", list(sectors.keys()), index=0)
    trend_filter = st.multiselect("Select Trend", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])
    st.info("యాప్ ఎడమ వైపున ఈ బాక్స్ ఉంటుంది.")

# =============================
# 5. SCANNER FUNCTION
# =============================
def run_scanner(tickers):
    # 10 Days data for better EMA calculation
    data = yf.download(tickers, period="10d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            df, res_p, sup_p, vol_ratio = analyze_stock(df)
            last = df.iloc[-1]
            
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Volume Strength Status
            if vol_ratio >= 1.5: vol_str = "🔥 STRONG"
            elif vol_ratio >= 1.0: vol_str = "AVERAGE"
            else: vol_str = "📉 WEAK"
            
            # Status Alerts
            status = "NORMAL"
            if ltp >= res_p:
                status = "🚀 BREAKOUT" if vol_ratio > 1.1 else "⚠️ FAKE (Low Vol)"
            elif ltp <= sup_p:
                status = "📉 BREAKDOWN" if vol_ratio > 1.1 else "⚠️ FAKE (Low Vol)"
            
            # Signal
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" else \
                     "SELL" if ltp < last['VWAP'] and trend == "DOWNTREND" else "WAIT"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Vol Strength": vol_str,
                "Support": sup_p,
                "Resistance": res_p,
                "Trend": trend,
                "Status": status,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# =============================
# 6. RESULTS
# =============================
final_results = run_scanner(sectors[sector_name])

if not final_results.empty:
    final_results = final_results[final_results['Trend'].isin(trend_filter)]
    
    def apply_styles(row):
        styles = [''] * len(row)
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color: #004d1a; color: white'] * len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color: #4d0000; color: white'] * len(row)
            
        ltp_idx = final_results.columns.get_loc('LTP')
        if abs(row.LTP - row.Support) / row.Support < 0.001:
            styles[ltp_idx] = 'color: #00ffff; font-weight: bold'
        elif abs(row.LTP - row.Resistance) / row.Resistance < 0.001:
            styles[ltp_idx] = 'color: #ff3131; font-weight: bold'
            
        return styles

    styled_table = final_results.style.apply(apply_styles, axis=1)\
        .set_properties(subset=['Support'], **{'color': '#ff4d4d', 'font-weight': 'bold'})\
        .set_properties(subset=['Resistance'], **{'color': '#00ff41', 'font-weight': 'bold'})

    st.dataframe(styled_table, use_container_width=True, height=500)
    st.write(f"📊 Sector: {sector_name} | Updated: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("సైడ్ బార్ లో సెక్టార్ ని ఎంచుకోండి మరియు డేటా లోడ్ అయ్యే వరకు వేచి ఉండండి.")
