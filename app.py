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
    
    # --- RSI ---
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # --- EMA ---
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # --- VWAP ---
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    
    # --- VOLUME ANALYSIS ---
    # సగటు వాల్యూమ్ (గత 20 క్యాండిల్స్)
    avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
    last_vol = df['Volume'].iloc[-1]
    
    # --- SUPPORT & RESISTANCE ---
    res = df['High'].iloc[-20:].max()
    sup = df['Low'].iloc[-20:].min()
    
    return df, round(float(res), 2), round(float(sup), 2), last_vol / avg_vol

# =============================
# 3. NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"]
}

# =============================
# 4. INTERFACE
# =============================
st.title("🛡️ NSE Pro Scanner (Volume & Breakout)")

with st.sidebar:
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Trend Filter", ["UPTREND", "DOWNTREND"], default=["UPTREND", "DOWNTREND"])

# =============================
# 5. SCANNER FUNCTION
# =============================
def process_scanner(tickers):
    data = yf.download(tickers, period="10d", interval="5m", group_by='ticker', progress=False)
    results = []
    
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            df, res, sup, vol_ratio = analyze_stock(df)
            last = df.iloc[-1]
            
            ltp = round(float(last['Close']), 2)
            rsi = round(float(last['RSI']), 1)
            p_change = round(((ltp - df.iloc[0]['Open']) / df.iloc[0]['Open']) * 100, 2)
            trend = "UPTREND" if last['EMA20'] >= last['EMA50'] else "DOWNTREND"
            
            # --- VOLUME STRENGTH LOGIC ---
            if vol_ratio >= 1.5: vol_str = "🔥 STRONG"
            elif vol_ratio >= 1.0: vol_str = "AVERAGE"
            else: vol_str = "📉 WEAK"
            
            # --- STATUS ALERT ---
            status = "NORMAL"
            if ltp >= res:
                status = "🚀 BREAKOUT" if vol_ratio > 1.2 else "⚠️ FAKE (Low Vol)"
            elif ltp <= sup:
                status = "📉 BREAKDOWN" if vol_ratio > 1.2 else "⚠️ FAKE (Low Vol)"
            
            # --- SIGNAL ---
            signal = "BUY" if ltp > last['VWAP'] and trend == "UPTREND" and vol_ratio > 1 else \
                     "SELL" if ltp < last['VWAP'] and trend == "DOWNTREND" and vol_ratio > 1 else "WAIT"

            results.append({
                "Stock": t.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi,
                "Vol Strength": vol_str,
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
    
    def style_table(row):
        styles = [''] * len(row)
        # Status styling
        if "BREAKOUT" in str(row.Status):
            styles = ['background-color: #004d1a; color: white'] * len(row)
        elif "BREAKDOWN" in str(row.Status):
            styles = ['background-color: #4d0000; color: white'] * len(row)
        
        # Volume Strength color
        v_idx = res_df.columns.get_loc('Vol Strength')
        if "STRONG" in row['Vol Strength']: styles[v_idx] = 'color: #ffaa00; font-weight: bold'
        elif "WEAK" in row['Vol Strength']: styles[v_idx] = 'color: #777777'

        # LTP Near Levels
        ltp_idx = res_df.columns.get_loc('LTP')
        if abs(row.LTP - row.Support) / row.Support < 0.001: styles[ltp_idx] = 'color: #00ffff; font-weight: bold'
        elif abs(row.LTP - row.Resistance) / row.Resistance < 0.001: styles[ltp_idx] = 'color: #ff3131; font-weight: bold'

        return styles

    styled_df = res_df.style.apply(style_table, axis=1)\
        .set_properties(subset=['Support'], **{'color': '#ff4d4d', 'font-weight': 'bold'})\
        .set_properties(subset=['Resistance'], **{'color': '#00ff41', 'font-weight': 'bold'})

    st.dataframe(styled_df, use_container_width=True, height=500)
    st.success(f"Updated: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.info("No data found.")
