import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG & UI SETUP
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")

# ఆటో రిఫ్రెష్ (ప్రతి 15 సెకన్లకు)
st_autorefresh(interval=15000, key="refresh")

# CSS - ఇక్కడ ఎర్రర్ సరిచేయబడింది (unsafe_allow_html=True)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e212b; padding: 10px; border-radius: 10px; border: 1px solid #30363d; }
    .stDataFrame { border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 2. INDICATORS LOGIC
# =============================
def get_indicators(df):
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMAs for Trend
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df

# =============================
# 3. STOCK SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS","BHARTIARTL.NS","LT.NS","ITC.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","INDUSINDBK.NS","AUBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","EICHERMOT.NS"]
}

# =============================
# 4. SIDEBAR & FILTERS
# =============================
st.title("⚡ NSE Pro Smart Scanner")

with st.sidebar:
    st.header("Settings")
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.radio("Trend Filter", ["ALL", "UPTREND", "DOWNTREND"])
    min_rsi = st.slider("Min RSI Level", 0, 100, 40)
    st.info("Scanner refreshes every 15 seconds.")

# =============================
# 5. DATA PROCESSING
# =============================
def process_data(ticker_list):
    results = []
    # Fetch data for all stocks in one go (Faster)
    data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
    
    for ticker in ticker_list:
        try:
            df = data[ticker].dropna()
            if len(df) < 20: continue
            
            df = get_indicators(df)
            last = df.iloc[-1]
            
            ltp = round(last['Close'], 2)
            rsi_val = round(last['RSI'], 1)
            vwap_val = round(last['VWAP'], 2)
            
            # Trend Logic
            trend = "UPTREND" if last['EMA20'] > last['EMA50'] else "DOWNTREND"
            
            # Signal Logic
            if ltp > vwap_val and rsi_val > 55:
                signal = "🚀 STRONG BUY"
            elif ltp > vwap_val:
                signal = "BUY"
            elif ltp < vwap_val and rsi_val < 45:
                signal = "⚠️ STRONG SELL"
            else:
                signal = "SELL"
                
            # % Change calculation
            day_open = df.iloc[0]['Open']
            p_change = round(((ltp - day_open) / day_open) * 100, 2)

            results.append({
                "Ticker": ticker.replace(".NS",""),
                "LTP": ltp,
                "Change %": p_change,
                "RSI": rsi_val,
                "Trend": trend,
                "Signal": signal,
                "VWAP": vwap_val
            })
        except:
            continue
    return pd.DataFrame(results)

# =============================
# 6. DISPLAY RESULTS
# =============================
res_df = process_data(sectors[sector_name])

if not res_df.empty:
    # Applying Filters
    if trend_filter != "ALL":
        res_df = res_df[res_df['Trend'] == trend_filter]
    res_df = res_df[res_df['RSI'] >= min_rsi]

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    top_stock = res_df.loc[res_df['Change %'].idxmax()]
    m1.metric("Top Gainer", top_stock['Ticker'], f"{top_stock['Change %']}%")
    m2.metric("Market Sentiment", "Bullish" if top_stock['Change %'] > 0 else "Bearish")
    m3.metric("Total Stocks", len(res_df))

    # Styling Table
    def style_signal(val):
        color = '#00ff41' if 'BUY' in val else '#ff3131' if 'SELL' in val else 'white'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        res_df.style.applymap(style_signal, subset=['Signal'])
        .background_gradient(cmap='RdYlGn', subset=['Change %']),
        use_container_width=True, height=500
    )
    
    if any("STRONG BUY" in s for s in res_df['Signal']):
        st.success("🔥 High Probability Breakout Detected!")
else:
    st.warning("No stocks matching the current filters.")
