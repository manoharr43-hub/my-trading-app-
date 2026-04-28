import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz, io, os
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V53", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

EXPORT_FOLDER = "exports"
os.makedirs(EXPORT_FOLDER, exist_ok=True)

st.title("🚀 NSE AI PRO V53 - AUTO ENGINE")

# =============================
# STOCK LIST
# =============================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC",
    "POWERGRID","TATASTEEL","JSWSTEEL","BAJFINANCE","BAJAJFINSV","ADANIENT",
    "ADANIPORTS","ULTRACEMCO","GRASIM","TECHM","WIPRO","HCLTECH","NESTLEIND",
    "BRITANNIA","CIPLA","DIVISLAB","DRREDDY","BPCL","IOC","BHARTIARTL","TITAN",
    "M&M","HEROMOTOCO","EICHERMOT","TATAMOTORS","COALINDIA","HAVELLS",
    "SIEMENS","PIDILITIND","BEL","DLF","INDUSINDBK","PNB","BANKBARODA",
    "CANBK","FEDERALBNK","IDFCFIRSTB","YESBANK","ZEEL","ZOMATO"
]

# =============================
# INDICATORS (FIXED VWAP)
# =============================
def add_indicators(df):
    if df is None or len(df) < 50:
        return None
    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    # ✅ DAILY VWAP FIX
    df['VWAP'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum() / \
                 df['Volume'].groupby(df.index.date).cumsum()

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df.dropna()

# =============================
# SIGNAL ENGINE
# =============================
def analyze(row):
    try:
        dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
        trend_up = row['EMA20'] > row['EMA50']
        trend_down = row['EMA20'] < row['EMA50']

        signal = None

        if dist < 0.006:
            if row['Close'] > row['VWAP'] and trend_up:
                signal = "BUY"
            elif row['Close'] < row['VWAP'] and trend_down:
                signal = "SELL"

        big_player = (row['Volume'] > row['VolAvg'] * 2 and abs(row['Close'] - row['Open']) > row['ATR'] * 0.5)
        big_move   = (row['Volume'] > row['VolAvg'] * 2 and abs(row['Close'] - row['Open']) > row['ATR'] * 0.7)

        return signal, big_player, big_move
    except:
        return None, False, False

# =============================
# EXCEL MULTI SHEET
# =============================
def to_excel_multi(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='ALL', index=False)

        df[df["SIGNAL"]=="BUY"].to_excel(writer, sheet_name='BUY', index=False)
        df[df["SIGNAL"]=="SELL"].to_excel(writer, sheet_name='SELL', index=False)
        df[df["BIG PLAYER"]=="🔥"].to_excel(writer, sheet_name='BIG_PLAYER', index=False)

    return output.getvalue()

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=300)
def fetch_live():
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False)

# =============================
# UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE AUTO", "📊 BACKTEST"])

# =============================
# LIVE AUTO SCAN + EXPORT
# =============================
with tab1:

    data = fetch_live()
    results = []

    for s in stocks:
        try:
            df = data.get(s + ".NS")
            df = add_indicators(df)
            if df is None:
                continue

            row = df.iloc[-1]
            signal, bp, bm = analyze(row)

            if signal:
                t = pd.to_datetime(df.index[-1])
                if t.tz is None:
                    t = t.tz_localize("UTC")
                t = t.tz_convert(IST)

                if not (t.hour > 9 or (t.hour == 9 and t.minute >= 15)):
                    continue
                if t.hour >= 15 and t.minute > 30:
                    continue

                atr = row['ATR']

                results.append({
                    "TIME": t.strftime('%H:%M'),
                    "STOCK": s,
                    "SIGNAL": signal,
                    "BIG PLAYER": "🔥" if bp else "-",
                    "BIG MOVE": "🚀" if bm else "-",
                    "ENTRY": round(row['Close'], 2),
                    "SL": round(row['Close'] - atr*1.5 if signal=="BUY" else row['Close'] + atr*1.5, 2),
                    "TARGET": round(row['Close'] + atr*3 if signal=="BUY" else row['Close'] - atr*3, 2)
                })
        except:
            continue

    df_live = pd.DataFrame(results)

    if not df_live.empty:
        st.dataframe(df_live, use_container_width=True)

        filename = f"live_{now.strftime('%Y%m%d_%H%M')}.xlsx"
        filepath = os.path.join(EXPORT_FOLDER, filename)

        excel_data = to_excel_multi(df_live)

        with open(filepath, "wb") as f:
            f.write(excel_data)

        st.success(f"Auto saved: {filepath}")

        st.download_button("📥 Download Now", excel_data, file_name=filename)

    else:
        st.warning("No signals")

# =============================
# BACKTEST (REALISTIC)
# =============================
with tab2:

    bt_date = st.date_input("Select Date", value=now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST"):

        logs = []
        cooldown = timedelta(minutes=45)

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
                if df is None:
                    continue

                in_trade = False
                last_trade_time = None

                for i in range(1, len(df)):

                    prev = df.iloc[i-1]
                    row = df.iloc[i]
                    time = df.index[i]

                    if not (time.hour > 9 or (time.hour == 9 and time.minute >= 15)):
                        continue
                    if time.hour >= 15 and time.minute > 30:
                        continue

                    if last_trade_time and (time - last_trade_time < cooldown):
                        continue

                    signal, _, _ = analyze(prev)

                    if not in_trade and signal:

                        entry_price = row['Close']
                        atr = row['ATR']

                        sl = entry_price - atr*1.5 if signal=="BUY" else entry_price + atr*1.5
                        target = entry_price + atr*3 if signal=="BUY" else entry_price - atr*3

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
                                reason = "SL HIT"
                            elif high >= target:
                                exit_price = target
                                reason = "TARGET HIT"

                        else:
                            if high >= sl:
                                exit_price = sl
                                reason = "SL HIT"
                            elif low <= target:
                                exit_price = target
                                reason = "TARGET HIT"

                        # ✅ Day Exit
                        if time.hour == 15 and time.minute >= 25:
                            exit_price = row['Close']
                            reason = "DAY EXIT"

                        if reason:
                            pnl = round(exit_price - entry_price,2) if trade_type=="BUY" else round(entry_price - exit_price,2)

                            logs.append({
                                "STOCK": s,
                                "TYPE": trade_type,
                                "ENTRY TIME": entry_time.strftime('%H:%M'),
                                "EXIT TIME": time.strftime('%H:%M'),
                                "ENTRY": round(entry_price,2),
                                "EXIT": round(exit_price,2),
                                "P&L": pnl,
                                "RESULT": reason
                            })

                            in_trade = False
                            last_trade_time = time

            except:
                continue

        df_logs = pd.DataFrame(logs)

        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)

            total = len(df_logs)
            wins = len(df_logs[df_logs["P&L"] > 0])
            loss = total - wins
            acc = round((wins/total)*100,2)

            st.success(f"Trades: {total} | Wins: {wins} | Loss: {loss} | Accuracy: {acc}%")

            st.download_button("📥 Download Backtest", to_excel_multi(df_logs), file_name="backtest.xlsx")

        else:
            st.warning("No trades found")
