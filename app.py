import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V49.1", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V49.1 - STABLE PULLBACK SYSTEM")
st.markdown(f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# STOCK LIST (SAMPLE - FULL LIST ADD CHEYYOCHU)
# ==========================================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT"]

# ==========================================
# SAFE INDICATORS
# ==========================================
def add_indicators(df):
    df = df.copy()

    # Fix multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # Safe VWAP
    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date').apply(
        lambda x: (x['Close'] * x['Volume']).cumsum() / x['Volume'].cumsum()
    ).reset_index(level=0, drop=True)

    # ATR
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# ==========================================
# MARKET TREND (SAFE)
# ==========================================
@st.cache_data(ttl=60)
def get_market_trend():
    try:
        nifty = yf.download("^NSEI", period="1d", interval="5m")

        if nifty.empty or len(nifty) < 20:
            return "UNKNOWN"

        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        nifty['EMA20'] = nifty['Close'].ewm(span=20).mean()

        close = float(nifty['Close'].iloc[-1])
        ema = float(nifty['EMA20'].iloc[-1])

        return "UP" if close > ema else "DOWN"

    except:
        return "UNKNOWN"

# ==========================================
# PULLBACK LOGIC
# ==========================================
def get_pullback(row, prev):
    try:
        dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

        if (dist < 0.004 and row['Close'] > row['EMA20'] and
            row['Close'] > row['VWAP'] and row['Low'] > prev['Low']):
            return "SUPPORT BUY 🟢"

        if (dist < 0.004 and row['Close'] < row['EMA20'] and
            row['Close'] < row['VWAP'] and row['High'] < prev['High']):
            return "RESIST SELL 🔴"

        if prev['Close'] < row['EMA20'] and row['Close'] > row['EMA20']:
            return "RECENT BUY 🔼"

        if prev['Close'] > row['EMA20'] and row['Close'] < row['EMA20']:
            return "RECENT SELL 🔽"

    except:
        return None

    return None

# ==========================================
# SCORING
# ==========================================
def score_trade(row):
    score = 0
    try:
        if row['Volume'] > row['VolAvg'] * 2:
            score += 1
        if abs(row['Close'] - row['EMA20']) < row['ATR']:
            score += 1
        if row['ATR'] > row['Close'] * 0.002:
            score += 1
    except:
        pass
    return score

# ==========================================
# BIG PLAYER
# ==========================================
def big_player(row):
    try:
        return row['Volume'] > row['VolAvg'] * 3 and abs(row['Close'] - row['Open']) > row['ATR']
    except:
        return False

# ==========================================
# DATA
# ==========================================
@st.cache_data(ttl=60)
def get_data():
    try:
        data = yf.download([s+".NS" for s in stocks],
                           period="5d", interval="5m", group_by="ticker")

        return data
    except:
        return {}

def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# ==========================================
# UI
# ==========================================
tab1, tab2 = st.tabs(["📊 LIVE", "📜 BACKTEST"])

data = get_data()
market_trend = get_market_trend()

# ==========================================
# LIVE
# ==========================================
with tab1:
    st.write(f"📊 Market Trend: {market_trend}")

    if st.button("🔍 SCAN"):
        results = []

        for s in stocks:
            try:
                df = data.get(s+".NS")
                if df is None or df.empty:
                    continue

                df = add_indicators(df.dropna())

                if len(df) < 30:
                    continue

                row, prev = df.iloc[-1], df.iloc[-2]

                pull = get_pullback(row, prev)
                if not pull:
                    continue

                sig = "BUY" if "BUY" in pull else "SELL"

                # EMA50 filter
                if sig == "BUY" and row['Close'] < row['EMA50']:
                    continue
                if sig == "SELL" and row['Close'] > row['EMA50']:
                    continue

                # Market filter
                if market_trend == "DOWN" and sig == "BUY":
                    continue
                if market_trend == "UP" and sig == "SELL":
                    continue

                if score_trade(row) < 2:
                    continue

                entry = round(row['Close'], 2)

                results.append({
                    "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": sig,
                    "TYPE": pull,
                    "ENTRY": entry,
                    "SL": round(entry - row['ATR']*1.5 if sig=="BUY" else entry + row['ATR']*1.5, 2),
                    "TGT": round(entry + row['ATR']*3 if sig=="BUY" else entry - row['ATR']*3, 2),
                    "SCORE": score_trade(row),
                    "BIG PLAYER": "YES 🔥" if big_player(row) else "NO"
                })

            except:
                continue

        if results:
            df_out = pd.DataFrame(results)
            st.dataframe(df_out, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_out), "signals.xlsx")
        else:
            st.warning("No trades found")

# ==========================================
# BACKTEST
# ==========================================
with tab2:
    d = st.date_input("Select Date", now.date() - timedelta(days=1))

    if st.button("🔄 RUN BACKTEST"):
        logs = []

        for s in stocks:
            try:
                df_all = data.get(s+".NS")
                if df_all is None:
                    continue

                df_all.index = df_all.index.tz_convert(IST)
                df = add_indicators(df_all[df_all.index.date == d])

                for i in range(20, len(df)):
                    row, prev = df.iloc[i], df.iloc[i-1]
                    pull = get_pullback(row, prev)

                    if not pull:
                        continue

                    sig = "BUY" if "BUY" in pull else "SELL"

                    if score_trade(row) < 2:
                        continue

                    entry = round(row['Close'], 2)

                    logs.append({
                        "TIME": df.index[i].strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": sig,
                        "TYPE": pull,
                        "ENTRY": entry,
                        "SL": round(entry - row['ATR']*1.5 if sig=="BUY" else entry + row['ATR']*1.5, 2),
                        "TGT": round(entry + row['ATR']*3 if sig=="BUY" else entry - row['ATR']*3, 2),
                        "SCORE": score_trade(row),
                        "BIG PLAYER": "YES 🔥" if big_player(row) else "NO"
                    })

            except:
                continue

        if logs:
            df_log = pd.DataFrame(logs)
            st.dataframe(df_log, use_container_width=True)
            st.download_button("📥 Download", to_excel(df_log), "backtest.xlsx")
        else:
            st.info("No signals found")
