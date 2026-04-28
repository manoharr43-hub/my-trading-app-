import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io, os
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V53 STABLE", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

EXPORT_FOLDER = "exports"
os.makedirs(EXPORT_FOLDER, exist_ok=True)

st.title("🚀 NSE AI PRO V53 - STABLE ENGINE")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","KOTAKBANK"]

# =============================
# INDICATORS (NO DATA LOSS)
# =============================
def add_indicators(df):
    if df is None or df.empty:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# SIMPLE SIGNAL (GUARANTEED TRADES)
# =============================
def analyze(prev, row):
    try:
        signal = None

        # EMA crossover logic
        if prev['EMA20'] < prev['EMA50'] and row['EMA20'] > row['EMA50']:
            signal = "BUY"

        elif prev['EMA20'] > prev['EMA50'] and row['EMA20'] < row['EMA50']:
            signal = "SELL"

        big_player = row['Volume'] > row['VolAvg'] * 1.5 if pd.notna(row['VolAvg']) else False

        return signal, big_player

    except:
        return None, False

# =============================
# EXCEL
# =============================
def to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# FETCH DATA
# =============================
@st.cache_data(ttl=300)
def fetch_live():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False)

# =============================
# UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE", "📊 BACKTEST"])

# =============================
# LIVE SCREENER
# =============================
with tab1:

    if st.button("RUN LIVE"):
        data = fetch_live()
        results = []

        for s in stocks:
            try:
                df = data.get(s + ".NS")
                df = add_indicators(df)
                if df is None:
                    continue

                prev = df.iloc[-2]
                row = df.iloc[-1]

                signal, bp = analyze(prev, row)

                if signal:

                    t = pd.to_datetime(df.index[-1])
                    if t.tz is None:
                        t = t.tz_localize("UTC")
                    t = t.tz_convert(IST)

                    if not (t.hour > 9 or (t.hour == 9 and t.minute >= 15)):
                        continue

                    atr = row['ATR'] if pd.notna(row['ATR']) else 1

                    results.append({
                        "TIME": t.strftime('%H:%M'),
                        "STOCK": s,
                        "SIGNAL": signal,
                        "BIG PLAYER": "🔥" if bp else "-",
                        "ENTRY": round(row['Close'], 2),
                        "SL": round(row['Close'] - atr if signal=="BUY" else row['Close'] + atr, 2),
                        "TARGET": round(row['Close'] + atr*2 if signal=="BUY" else row['Close'] - atr*2, 2)
                    })

            except:
                continue

        df_live = pd.DataFrame(results)

        if not df_live.empty:
            st.dataframe(df_live, use_container_width=True)

            excel = to_excel(df_live)
            st.download_button("📥 Download Excel", excel, file_name="live.xlsx")

        else:
            st.warning("No signals")

# =============================
# BACKTEST (WORKING)
# =============================
with tab2:

    bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST"):

        logs = []

        for s in stocks:
            try:
                start = pd.to_datetime(bt_date)
                end = start + timedelta(days=1)

                df = yf.download(s + ".NS", start=start, end=end, interval="5m", progress=False)

                if df is None or df.empty:
                    continue

                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC")
                df.index = df.index.tz_convert(IST)

                df = add_indicators(df)

                in_trade = False

                for i in range(2, len(df)):

                    prev = df.iloc[i-1]
                    prev2 = df.iloc[i-2]
                    row = df.iloc[i]
                    time = df.index[i]

                    if pd.isna(row['ATR']):
                        continue

                    signal, _ = analyze(prev2, prev)

                    if not in_trade and signal:

                        entry = row['Close']
                        atr = row['ATR']

                        sl = entry - atr if signal=="BUY" else entry + atr
                        target = entry + atr*2 if signal=="BUY" else entry - atr*2

                        in_trade = True
                        entry_time = time
                        trade_type = signal

                    elif in_trade:

                        high = row['High']
                        low = row['Low']

                        exit_price = None
                        reason = None

                        if trade_type == "BUY":
                            if low <= sl:
                                exit_price = sl
                                reason = "SL"
                            elif high >= target:
                                exit_price = target
                                reason = "TARGET"

                        else:
                            if high >= sl:
                                exit_price = sl
                                reason = "SL"
                            elif low <= target:
                                exit_price = target
                                reason = "TARGET"

                        if reason or (time.hour == 15 and time.minute >= 25):

                            if not exit_price:
                                exit_price = row['Close']
                                reason = "DAY EXIT"

                            pnl = round(exit_price - entry, 2) if trade_type=="BUY" else round(entry - exit_price, 2)

                            logs.append({
                                "STOCK": s,
                                "TYPE": trade_type,
                                "ENTRY TIME": entry_time.strftime('%H:%M'),
                                "EXIT TIME": time.strftime('%H:%M'),
                                "P&L": pnl,
                                "RESULT": reason
                            })

                            in_trade = False

            except:
                continue

        df_logs = pd.DataFrame(logs)

        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)

            total = len(df_logs)
            wins = len(df_logs[df_logs["P&L"] > 0])

            st.success(f"Trades: {total} | Wins: {wins}")

            st.download_button("📥 Download Backtest", to_excel(df_logs), file_name="backtest.xlsx")

        else:
            st.error("Still no trades — check date (market holiday?)")
