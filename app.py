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

# CSS - ఎర్రర్స్ లేకుండా డిజైన్ సెట్ చేయడం
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 25px; color: #00ff41; }
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
    st.header("Scanner Settings")
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.radio("Trend Filter", ["ALL", "UPTREND", "DOWNTREND"])
    min_rsi = st.slider("Min RSI Level", 0, 100, 30)
    st.write("---")
    st.info("Scanner updates every 15s")

# =============================
# 5. DATA PROCESSING
# =============================
@st.cache_data(ttl=10) # 10 సెకన్ల వరకు డేటాను క్యాష్ చేస్తుంది
def fetch_data(ticker_list):
    try:
        data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
        return data
    except Exception as e:
        st.error(f"Data fetch error: {e}")
        return None

def process_results(ticker_list):
    data = fetch_data(ticker_list)
    if data is None: return pd.DataFrame()
    
    results = []
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
                "Price": ltp,
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
res_df = process_results(sectors[sector_name])

if not res_df.empty:
    # Applying Filters
    if trend_filter != "ALL":
        res_df = res_df[res_df['Trend'] == trend_filter]
    res_df = res_df[res_df['RSI'] >= min_rsi]

    if not res_df.empty:
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        top_stock = res_df.loc[res_df['Change %'].idxmax()]
        m1.metric("Top Gainer", top_stock['Ticker'], f"{top_stock['Change %']}%")
        m2.metric("Market", "Live")
        m3.metric("Stocks Count", len(res_df))

        # Styling Table - Updated applymap to map for Pandas 2.0+
        def style_signal(val):
            if 'BUY' in str(val): color = '#00ff41'
            elif 'SELL' in str(val): color = '#ff3131'
            else: color = 'white'
            return f'color: {color}; font-weight: bold'

        # FIX: map() function used instead of applymap()
        styled_df = res_df.style.map(style_signal, subset=['Signal']) \
                                .background_gradient(cmap='RdYlGn', subset=['Change %'])

        st.dataframe(styled_df, use_container_width=True, height=500)
    else:
        st.warning("No stocks match the filter criteria.")
else:
    st.error("Waiting for data... Please check your internet or Ticker symbols.")
