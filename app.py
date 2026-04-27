import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V19 - LIVE+BACKTEST", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V19 - ULTIMATE DASHBOARD")
st.write(f"🕒 **System Sync (IST):** {current_time}")

# =============================
# STOCK SECTORS
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT"],
    "ENERGY": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL"],
    "OTHERS": ["ITC", "LT", "BAJFINANCE", "TATASTEEL", "BHARTIARTL"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# FUNCTIONS
# =============================
@st.cache_data(ttl=60)
def get_data(stock, period="1y", interval="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty:
            return None
        df.index = df.index.tz_localize(None)
        return df.dropna()
    except:
        return None

def add_indicators(df):
    df = df.copy()

    # EMA
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # VWAP
    df['CumVol'] = df['Volume'].groupby(df.index.date).cumsum()
    df['CumPV'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum()
    df['VWAP'] = df['CumPV'] / df['CumVol']

    # Volume
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 2.5)

    # Reversal
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    df['Bear_Rev'] = (df['RSI'].shift(1) > 70) & (df['RSI'] < 70)

    return df

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST", "📈 CHART"])

# =============================
# TAB 1 - LIVE SCANNER
# =============================
with tab1:
    if st.button("🚀 SCAN MARKET"):
        results = []

        with st.spinner("Scanning Stocks..."):
            for s in all_stocks:
                df = get_data(s, period="2d", interval="15m")

                if df is None or df.empty:
                    continue

                df.index = df.index.tz_convert(IST)
                df = add_indicators(df)

                last = df.iloc[-1]
                price = round(last['Close'], 2)

                signal = "WAIT"
                sl, tgt = 0, 0

                # BUY LOGIC
                if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
                    signal = "🚀 STRONG BUY"
                    sl = round(price * 0.99, 2)
                    tgt = round(price * 1.02, 2)

                # SELL LOGIC
                elif last['Close'] < last['VWAP'] and last['EMA20'] < last['EMA50']:
                    signal = "🔻 STRONG SELL"
                    sl = round(price * 1.01, 2)
                    tgt = round(price * 0.98, 2)

                # REVERSAL
                elif last['Bull_Rev']:
                    signal = "🔄 BUY REVERSAL"
                elif last['Bear_Rev']:
                    signal = "🔄 SELL REVERSAL"

                results.append({
                    "Stock": s,
                    "Time": df.index[-1].strftime('%H:%M'),
                    "Price": price,
                    "Signal": signal,
                    "SL": sl,
                    "Target": tgt,
                    "Volume": "🐋" if last['Big_Player'] else "-"
                })

        st.dataframe(pd.DataFrame(results), use_container_width=True)

# =============================
# TAB 2 - BACKTEST
# =============================
with tab2:
    if st.button("📊 RUN BACKTEST"):
        logs = []

        with st.spinner("Running Backtest..."):
            for s in all_stocks:
                df = get_data(s, period="2mo", interval="1d")

                if df is None:
                    continue

                df = add_indicators(df)

                for i in range(1, len(df)):
                    row = df.iloc[i]

                    if row['Big_Player'] or row['Bull_Rev'] or row['Bear_Rev']:
                        logs.append({
                            "Date": df.index[i].strftime('%Y-%m-%d'),
                            "Stock": s,
                            "Price": round(row['Close'], 2),
                            "Signal": "BIG PLAYER" if row['Big_Player'] else "REVERSAL"
                        })

        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
        else:
            st.warning("No Signals Found")

# =============================
# TAB 3 - CHART
# =============================
with tab3:
    stock = st.selectbox("Select Stock", all_stocks)
    df = get_data(stock)

    if df is not None:
        df = add_indicators(df)

        last_price = df.iloc[-1]['Close']

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        ))

        # SL / TARGET
        fig.add_hline(y=last_price * 1.02, line_dash="dash", line_color="green")
        fig.add_hline(y=last_price * 0.99, line_dash="dash", line_color="red")

        # BIG PLAYER MARK
        bp = df[df['Big_Player']]
        fig.add_trace(go.Scatter(
            x=bp.index,
            y=bp['Low'] * 0.98,
            mode='markers',
            marker=dict(size=10, color='yellow'),
            name="Big Player"
        ))

        fig.update_layout(height=600, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
