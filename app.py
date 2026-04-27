import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # RSI కోసం
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# 1. CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL V2", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL (ULTRA SPEED)")
st.markdown("---")

# =============================
# 2. STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT",
    "AXISBANK","BHARTIARTL","KOTAKBANK","MARUTI","M&M","TATAMOTORS",
    "SUNPHARMA","DRREDDY","CIPLA","HCLTECH","WIPRO","TECHM",
    "JSWSTEEL","TATASTEEL","HINDALCO"
]
tickers = [s + ".NS" for s in stocks]

# =============================
# 3. ANALYSIS ENGINE (RSI + VOLUME ADDED)
# =============================
def analyze_data(df):
    if df is None or len(df) < 50:
        return None

    # Indicators
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    rsi = ta.rsi(df['Close'], length=14)
    
    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()

    curr_close = df['Close'].iloc[-1]
    curr_rsi = rsi.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]

    trend = "CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "PUT STRONG"

    signal = "WAIT"
    # Strong Buy with Volume & RSI confirmation
    if e20.iloc[-1] > e50.iloc[-1] and curr_vol > (curr_avg_vol * 1.2):
        if curr_rsi > 50 and curr_rsi < 70: # Not overbought
            signal = "🚀 STRONG BUY"
    
    # Strong Sell with Volume & RSI confirmation
    elif e20.iloc[-1] < e50.iloc[-1] and curr_vol > (curr_avg_vol * 1.2):
        if curr_rsi < 50 and curr_rsi > 30: # Not oversold
            signal = "💀 STRONG SELL"

    return trend, signal, round(curr_rsi, 2)

# =============================
# 4. BREAKOUT ENGINE (REFINED)
# =============================
def breakout_engine(df, stock):
    results = []
    opening = df.between_time("09:15", "09:30")
    if opening.empty: return results

    high = opening['High'].max()
    low = opening['Low'].min()

    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        t = df.index[i]

        # BUY BREAKOUT
        if prev['Close'] <= high and curr['Close'] > high:
            status = "⏳ PENDING"
            if i + 3 < len(df):
                future = df.iloc[i+1:i+4]
                status = "🚀 CONFIRMED BUY" if sum(future['Close'] > curr['Close']) > 1 else "⚠️ FAILED BUY"
            
            target = round(curr['Close'] * 1.01, 2) # 1% Target
            sl = round(high * 0.995, 2)            # 0.5% SL
            
            results.append({"Time": t, "Stock": stock, "Type": status, "Level": round(high,2), "Target": target, "SL": sl})
            break

        # SELL BREAKOUT
        elif prev['Close'] >= low and curr['Close'] < low:
            status = "⏳ PENDING"
            if i + 3 < len(df):
                future = df.iloc[i+1:i+4]
                status = "💀 CONFIRMED SELL" if sum(future['Close'] < curr['Close']) > 1 else "⚠️ FAILED SELL"
            
            target = round(curr['Close'] * 0.99, 2)
            sl = round(low * 1.005, 2)
            
            results.append({"Time": t, "Stock": stock, "Type": status, "Level": round(low,2), "Target": target, "SL": sl})
            break
    return results

# =============================
# 5. EXECUTION LOGIC (BULK DOWNLOAD)
# =============================
if st.button("🔍 START PRO SCANNER"):
    with st.spinner("Fetching NSE Data..."):
        all_data = yf.download(tickers, period="2d", interval="15m", group_by='ticker', progress=False)
        
        live_results = []
        breakout_results = []

        for s in stocks:
            df = all_data[s + ".NS"].dropna()
            if df.empty: continue
            
            # Live Analysis
            res = analyze_data(df)
            if res:
                live_results.append({
                    "Stock": s,
                    "Price": round(df['Close'].iloc[-1], 2),
                    "Trend": res[0],
                    "Signal": res[1],
                    "RSI": res[2],
                    "Time": df.index[-1].strftime("%H:%M")
                })
            
            # Breakout Analysis (Today's data only)
            today_df = df.between_time("09:15", "15:30")
            breakout_results += breakout_engine(today_df, s)

        # UI Tables
        st.subheader("📊 LIVE SIGNALS (RSI & VOLUME FILTERED)")
        st.dataframe(pd.DataFrame(live_results), use_container_width=True)

        st.subheader("🔥 PRO BREAKOUT (WITH TARGET & SL)")
        df_brk = pd.DataFrame(breakout_results)
        if not df_brk.empty:
            df_brk['Time'] = pd.to_datetime(df_brk['Time']).dt.strftime('%H:%M')
            st.dataframe(df_brk, use_container_width=True)
        else:
            st.info("No breakouts detected yet.")

# =============================
# 6. BACKTEST PANEL
# =============================
st.markdown("---")
bt_date = st.sidebar.date_input("📅 Backtest Date", datetime.now() - timedelta(days=1))

if st.button("📊 RUN FULL BACKTEST"):
    with st.spinner("Testing Strategy..."):
        bt_signals = []
        bt_breakout = []
        
        # Backtest కోసం కూడా bulk data వాడొచ్చు, కానీ ఇక్కడ క్లారిటీ కోసం loop ఉంచాను
        for s in stocks:
            df_bt = yf.download(s + ".NS", start=bt_date, end=bt_date + timedelta(days=1), interval="15m", progress=False)
            df_bt = df_bt.between_time("09:15", "15:30").dropna()
            if df_bt.empty: continue

            # Signal Test
            for i in range(20, len(df_bt)):
                sub = df_bt.iloc[:i+1]
                res = analyze_data(sub)
                if res and res[1] != "WAIT":
                    bt_signals.append({"Time": sub.index[-1], "Stock": s, "Signal": res[1], "RSI": res[2]})

            # Breakout Test
            bt_breakout += breakout_engine(df_bt, s)

        # UI for Backtest
        st.subheader("📊 BACKTEST RESULTS")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Signals")
            st.dataframe(pd.DataFrame(bt_signals))
        with col2:
            st.write("Breakouts")
            st.dataframe(pd.DataFrame(bt_breakout))
