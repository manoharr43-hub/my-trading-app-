import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG
# =============================
st.set_page_config(page_title="NSE Pro Scanner", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# 2. SECTORS
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
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1+rs))

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # VWAP
    df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)

    # Support & Resistance
    res = df['High'].iloc[-20:-1].max()
    sup = df['Low'].iloc[-20:-1].min()

    return df, round(res,2), round(sup,2)

# =============================
# 4. MAIN INTERFACE
# =============================
st.title("🛡️ NSE Advanced Scanner")

with st.sidebar:
    sector_name = st.selectbox("Select Sector", list(sectors.keys()))
    trend_filter = st.multiselect("Trend Filter", ["UPTREND","DOWNTREND"], default=["UPTREND","DOWNTREND"])

# =============================
# 5. SCANNER FUNCTION
# =============================
def process_scanner(ticker_list):
    data = yf.download(ticker_list, period="2d", interval="5m", group_by='ticker', progress=False)
    results = []

    for t in ticker_list:
        try:
            df = data[t].dropna()
            if len(df)<30: continue
            df, res, sup = analyze_stock(df)
            last = df.iloc[-1]

            ltp = round(float(last['Close']),2)
            rsi = round(float(last['RSI']),1)
            p_change = round(((ltp - df.iloc[0]['Open'])/df.iloc[0]['Open'])*100,2)
            trend = "UPTREND" if last['EMA20']>last['EMA50'] else "DOWNTREND"

            # Breakout / Breakdown
            status = "NORMAL"
            if last['Close']>res:
                status = "🚀 BREAKOUT" if rsi<70 else "⚠️ FAKE BREAKOUT"
            elif last['Close']<sup:
                status = "📉 BREAKDOWN" if rsi>30 else "⚠️ FAKE BREAKDOWN"

            signal = "BUY" if ltp>last['VWAP'] and trend=="UPTREND" else "SELL" if ltp<last['VWAP'] else "WAIT"

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

res_df = process_scanner(sectors[sector_name])

# =============================
# 6. DISPLAY & STYLING
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

    # Optional mini-chart for first stock
    first_stock = sectors[sector_name][0]
    df_chart = yf.download(first_stock, period="1d", interval="5m", progress=False)
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index,
                                         open=df_chart['Open'],
                                         high=df_chart['High'],
                                         low=df_chart['Low'],
                                         close=df_chart['Close'])])
    fig.update_layout(title=f"{first_stock.replace('.NS','')} 5-min Chart", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Searching for stocks...")
