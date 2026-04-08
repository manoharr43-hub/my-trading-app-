import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Advanced Pro Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. INDICATORS LOGIC
# =============================
def analyze_stock(df):
    if df.empty or len(df) < 30: # కనీసం 30 క్యాండిల్స్ ఉండేలా చూస్తాం
        return df, 0, 0
    
    # RSI (రౌండ్ ఆఫ్ చేయబడింది)
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
    
    # Support & Resistance (గత 20 క్యాండిల్స్ హై/లో)
    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()
    
    return df, round(float(res), 2), round(float(sup), 2)

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
# 4. INTERFACE
# =============================
st.title("🛡️ NSE Pro Live Smart Scanner")

with st.sidebar:
    st.header("Filters")
    sector_name = st.selectbox("Select NSE Sector", list(sectors.keys()))
    # ఇక్కడ 'DOWNTREND' ని కూడా డీఫాల్ట్‌గా సెలెక్ట్ అయ్యేలా మార్చాను
    trend_filter = st.multiselect("Filter Trend", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])

# =============================
# 5. CORE SCANNER
# =============================
def process_data(tickers):
    data = yf.download(tickers, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            df, res_p, sup_p = analyze_stock(df)
            last = df.iloc[-1]
            
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            
            # Trend Logic
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Status (Breakout / Fake Alert)
            status = "NORMAL"
            if ltp > res_p:
                status = "🚀 BREAKOUT" if rsi < 70 else "⚠️ FAKE BREAKOUT"
            elif ltp < sup_p:
                status = "📉 BREAKDOWN" if rsi > 30 else "⚠️ FAKE BREAKDOWN"
            
            # Signal
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" else "SELL" if ltp < last['VWAP'] and trend == "DOWNTREND" else "WAIT"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Support": sup_p,
                "Resistance": res_p,
                "Trend": trend,
                "Status": status,
                "Signal": signal
            })
        except: continue
    return pd.DataFrame(results)

# =============================
# 6. DISPLAY & STYLING
# =============================
final_df = process_data(sectors[sector_name])

if not final_df.empty:
    # యూజర్ సెలెక్ట్ చేసిన ఫిల్టర్ ప్రకారం డేటాను చూపిస్తుంది
    final_df = final_df[final_df['Trend'].isin(trend_filter)]
    
    def apply_color(row):
        styles = [''] * len(row)
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color: #004d1a; color: white'] * len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color: #4d0000; color: white'] * len(row)
        elif "FAKE" in str(row.Status):
            styles = ['background-color: #634a00; color: white'] * len(row)
        return styles

    # కాలమ్ వైజ్ కలర్స్ (Support: Red, Resistance: Green)
    styled_df = final_df.style.apply(apply_color, axis=1)\
        .set_properties(subset=['Support'], **{'color': '#ff4d4d', 'font-weight': 'bold'})\
        .set_properties(subset=['Resistance'], **{'color': '#00ff41', 'font-weight': 'bold'})

    st.dataframe(styled_df, use_container_width=True, height=500)
    
    st.success(f"Updated at: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("No stocks matching your filters at the moment.")
