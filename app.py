import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO TERMINAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 NSE AI PRO TERMINAL")
st.markdown("---")

# =============================
# NSE SECTOR LIST
# =============================
sectors = {
    "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
    "IT": ["TCS","INFY","HCLTECH","WIPRO","TECHM"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA"],
    "Auto": ["MARUTI","M&M","TATAMOTORS"],
    "Metal": ["JSWSTEEL","TATASTEEL","HINDALCO"],
    "Diversified": ["RELIANCE","ITC","LT","BHARTIARTL"]
}

sector_choice = st.sidebar.selectbox("📂 Select NSE Sector", list(sectors.keys()))
stocks = sectors[sector_choice]

# =============================
# ANALYSIS ENGINE
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None
    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()
    vol = df['Volume']
    avg_vol = vol.rolling(20).mean()
    if pd.isna(avg_vol.iloc[-1]):
        return None
    trend = "CALL STRONG" if e20.iloc[-1] > e50.iloc[-1] else "PUT STRONG"
    signal = "WAIT"
    if e20.iloc[-1] > e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "🚀 STRONG BUY"
    elif e20.iloc[-1] < e50.iloc[-1] and vol.iloc[-1] > avg_vol.iloc[-1]:
        signal = "💀 STRONG SELL"
    return trend, signal

# =============================
# BREAKOUT ENGINE
# =============================
def breakout_engine(df, stock):
    results = []
    opening = df.between_time("09:15", "09:30")
    if opening.empty: return results
    high = opening['High'].max()
    low = opening['Low'].min()
    for i in range(1, len(df)-3):
        prev = df.iloc[i-1]; curr = df.iloc[i]; t = df.index[i]
        if prev['Close'] <= high and curr['Close'] > high:
            future = df.iloc[i+1:i+4]
            if future.empty: continue
            up = sum(future['Close'] > curr['Close']); down = sum(future['Close'] <= curr['Close'])
            status = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"
            results.append({"Time": t, "Stock": stock, "Type": status, "Level": round(high,2)})
            break
        elif prev['Close'] >= low and curr['Close'] < low:
            future = df.iloc[i+1:i+4]
            if future.empty: continue
            down = sum(future['Close'] < curr['Close']); up = sum(future['Close'] >= curr['Close'])
            status = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"
            results.append({"Time": t, "Stock": stock, "Type": status, "Level": round(low,2)})
            break
    return results

# =============================
# LIVE SCANNER
# =============================
if st.button("🔍 START LIVE SCANNER (9:15–3:30)"):
    live_results, breakout_results = [], []
    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")
            if df.empty: continue
            df = df.between_time("09:15", "15:30")
            res = analyze_data(df)
            if res:
                live_results.append({
                    "Stock": s,
                    "Price": round(df['Close'].iloc[-1],2),
                    "Trend": res[0],
                    "Signal": res[1],
                    "Time": df.index[-1].strftime("%H:%M")
                })
            breakout_results += breakout_engine(df, s)
        except: continue

    breakout_results = sorted(breakout_results, key=lambda x: x["Time"])
    for x in breakout_results: x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    st.subheader(f"📊 LIVE SIGNALS ({sector_choice})")
    st.write(pd.DataFrame(live_results).style.applymap(
        lambda v: "background-color:lightgreen" if "BUY" in str(v) else
                  "background-color:salmon" if "SELL" in str(v) else
                  "background-color:khaki" if "FAILED" in str(v) else ""
    , subset=["Signal"]))

    st.markdown("---")
    st.subheader(f"🔥 SMART BREAKOUT ({sector_choice})")
    st.write(pd.DataFrame(breakout_results).style.applymap(
        lambda v: "background-color:lightgreen" if "BUY" in str(v) else
                  "background-color:salmon" if "SELL" in str(v) else
                  "background-color:khaki" if "FAILED" in str(v) else ""
    , subset=["Type"]))

# =============================
# BACKTEST PANEL (UNCHANGED DATE)
# =============================
st.markdown("---")
bt_date = st.sidebar.date_input("📅 Select Backtest Date", datetime.now() - timedelta(days=1))

if st.button("📊 RUN BACKTEST"):
    bt_signals, bt_breakout = [], []
    for s in stocks:
        try:
            df = yf.Ticker(s + ".NS").history(start=bt_date, end=bt_date + timedelta(days=1), interval="15m")
            df = df.between_time("09:15", "15:30")
            if df.empty: continue
            for i in range(20, len(df)):
                sub = df.iloc[:i+1]; res = analyze_data(sub)
                if res and res[1] != "WAIT":
                    bt_signals.append({"Time": sub.index[-1], "Stock": s, "Signal": res[1]})
            bt_breakout += breakout_engine(df, s)
        except: continue

    bt_breakout = sorted(bt_breakout, key=lambda x: x["Time"])
    bt_signals = sorted(bt_signals, key=lambda x: x["Time"])
    for x in bt_breakout: x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")
    for x in bt_signals: x["Time"] = pd.to_datetime(x["Time"]).strftime("%H:%M")

    st.subheader(f"📊 BACKTEST SIGNALS ({sector_choice})")
    st.write(pd.DataFrame(bt_signals).style.applymap(
        lambda v: "background-color:lightgreen" if "BUY" in str(v) else
                  "background-color:salmon" if "SELL" in str(v) else
                  "background-color:khaki" if "FAILED" in str(v) else ""
    , subset=["Signal"]))

    st.markdown("---")
    st.subheader(f"🔥 BACKTEST SMART BREAKOUT ({sector_choice})")
    st.write(pd.DataFrame(bt_breakout).style.applymap(
        lambda v: "background-color:lightgreen" if "BUY" in str(v) else
                  "background-color:salmon" if "SELL" in str(v) else
                  "background-color:khaki" if "FAILED" in str(v) else ""
    , subset=["Type"]))
