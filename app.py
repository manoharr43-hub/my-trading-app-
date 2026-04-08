import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")
st_autorefresh(interval=15000, key="refresh")

# CSS for better UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stDataFrame { border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_input=True)

# =============================
# INDICATORS (Faster Version)
# =============================
def get_indicators(df):
    # RSI (Vectorized)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df

# =============================
# UI & DATA LOADING
# =============================
st.title("⚡ NSE Pro Smart Scanner")

sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","SBIN.NS","BHARTIARTL.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","AUBANK.NS"],
    "IT": ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS","LTIM.NS"]
}

c1, c2, c3 = st.columns(3)
with c1: sector = st.selectbox("Sector", list(sectors.keys()))
with c2: trend_filter = st.selectbox("Trend Filter", ["ALL","UPTREND","DOWNTREND"])
with c3: rsi_filter = st.slider("Min RSI", 0, 100, 30)

# =============================
# CORE ANALYSIS
# =============================
def process_stocks(ticker_list):
    all_results = []
    # Fetching all stocks at once is faster
    data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
    
    for ticker in ticker_list:
        try:
            df = data[ticker].dropna()
            if len(df) < 50: continue
            
            df = get_indicators(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # Logic
            ltp = round(last_row['Close'], 2)
            rsi_val = round(last_row['RSI'], 1)
            vwap_val = round(last_row['VWAP'], 2)
            
            # Trend & Signal
            trend = "UPTREND" if last_row['EMA20'] > last_row['EMA50'] else "DOWNTREND"
            signal = "🚀 BUY" if ltp > vwap_val and rsi_val > 50 else "⚠️ SELL" if ltp < vwap_val else "HOLD"
            
            # Price Change %
            day_open = df.iloc[0]['Open']
            p_change = round(((ltp - day_open) / day_open) * 100, 2)

            all_results.append({
                "Stock": ticker.replace(".NS",""),
                "Price": ltp,
                "Change %": p_change,
                "RSI": rsi_val,
                "Trend": trend,
                "Signal": signal,
                "VWAP": vwap_val
            })
        except:
            continue
    return pd.DataFrame(all_results)

# Execution
if st.button("Manual Refresh"):
    st.rerun()

results_df = process_stocks(sectors[sector])

if not results_df.empty:
    # Filtering
    if trend_filter != "ALL":
        results_df = results_df[results_df['Trend'] == trend_filter]
    
    results_df = results_df[results_df['RSI'] >= rsi_filter]

    # Styling for Table
    def color_signal(val):
        color = '#2ecc71' if 'BUY' in val else '#e74c3c' if 'SELL' in val else 'white'
        return f'color: {color}; font-weight: bold'

    styled_df = results_df.style.applymap(color_signal, subset=['Signal']) \
                                .background_gradient(cmap='RdYlGn', subset=['Change %'])

    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Summary Metrics
    m1, m2 = st.columns(2)
    m1.metric("Top Gainer", results_df.loc[results_df['Change %'].idxmax()]['Stock'], f"{results_df['Change %'].max()}%")
    m2.metric("Strongest RSI", results_df.loc[results_df['RSI'].idxmax()]['Stock'], results_df['RSI'].max())

else:
    st.error("No data found for selected criteria.")
