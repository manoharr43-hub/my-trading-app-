import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import io

# =========================
# CONFIGURATION
# =========================
st.set_page_config(page_title="NSE AI BACKTEST", layout="wide")
IST = pytz.timezone("Asia/Kolkata")
today = datetime.now(IST).date()

st.title("🚀 NSE AI BACKTEST (IST 9:15AM - 3:30PM)")

# =========================
# STOCKS LIST
# =========================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
    "LT","ITC","HINDUNILVR","ASIANPAINT","MARUTI","SUNPHARMA","ONGC","NTPC"
]

# =========================
# INDICATORS
# =========================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

# =========================
# SIGNAL ENGINE
# =========================
def get_signal(row):
    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']
    trend_up = row['EMA20'] > row['EMA50']
    trend_down = row['EMA20'] < row['EMA50']
    if dist < 0.004:
        if row['Close'] > row['VWAP'] and trend_up:
            return "BUY"
        elif row['Close'] < row['VWAP'] and trend_down:
            return "SELL"
    return None

# =========================
# EXCEL DOWNLOAD
# =========================
def df_to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =========================
# BACKTEST UI
# =========================
st.header("📊 Backtest")
bt_date = st.date_input("Select Backtest Date", value=(today - timedelta(days=1)),
                        min_value=today - timedelta(days=365), max_value=today - timedelta(days=1))

if st.button("RUN BACKTEST"):
    logs = []
    cooldown = timedelta(minutes=45)
    start = datetime.combine(bt_date, datetime.min.time()).replace(tzinfo=IST)
    end = start + timedelta(days=1)

    progress = st.progress(0)
    for stock_idx, s in enumerate(stocks):
        try:
            df = yf.download(s + ".NS", start=start, end=end, interval="5m", progress=False)
            if df is None or df.empty:
                continue

            # Always localize to UTC first, then convert to IST
            df.index = pd.to_datetime(df.index)
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC').tz_convert(IST)
            else:
                df.index = df.index.tz_convert(IST)

            df = add_indicators(df).dropna()
            last_trade_time = None
            in_trade = False

            for row_idx in range(1, len(df)):
                row = df.iloc[row_idx]
                time = df.index[row_idx]

                # Filter for NSE market hours (IST 09:15 - 15:30)
                if time.hour < 9 or (time.hour == 9 and time.minute < 15):
                    continue
                if time.hour > 15 or (time.hour == 15 and time.minute > 30):
                    continue

                if last_trade_time and (time - last_trade_time < cooldown):
                    continue

                signal = get_signal(row)

                if not in_trade and signal:
                    entry_price = row['Close']
                    atr = row['ATR']
                    sl = entry_price - atr*1.5 if signal == "BUY" else entry_price + atr*1.5
                    target = entry_price + atr*3 if signal == "BUY" else entry_price - atr*3
                    in_trade = True
                    entry_time = time
                    trade_type = signal

                elif in_trade:
                    high = row['High']
                    low = row['Low']
                    exit_price = None
                    exit_reason = None

                    if trade_type == "BUY":
                        if low <= sl:
                            exit_price = sl; exit_reason = "SL HIT"
                        elif high >= target:
                            exit_price = target; exit_reason = "TARGET HIT"
                    elif trade_type == "SELL":
                        if high >= sl:
                            exit_price = sl; exit_reason = "SL HIT"
                        elif low <= target:
                            exit_price = target; exit_reason = "TARGET HIT"

                    if exit_reason:
                        pnl = round(exit_price - entry_price,2) if trade_type=="BUY" else round(entry_price - exit_price,2)
                        logs.append({
                            "STOCK": s,
                            "TYPE": trade_type,
                            "ENTRY TIME": entry_time.strftime('%H:%M'),
                            "EXIT TIME": time.strftime('%H:%M'),
                            "MARKET TIME": time.strftime('%I:%M %p'),
                            "ENTRY": round(entry_price,2),
                            "EXIT": round(exit_price,2),
                            "P&L": pnl,
                            "RESULT": exit_reason
                        })
                        in_trade = False
                        last_trade_time = time

        except Exception as e:
            st.warning(f"{s}: {e}")
            continue

        progress.progress((stock_idx+1)/len(stocks))

    st.success("Backtest Complete!")

    df_logs = pd.DataFrame(logs)
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
        st.success(f"Total Trades: {len(df_logs)} | Wins: {len(df_logs[df_logs['P&L']>0])} | Loss: {len(df_logs[df_logs['P&L']<=0])}")
        st.download_button("📥 Download Excel", df_to_excel(df_logs), file_name="backtest.xlsx")
    else:
        st.warning("No trades found on this day.")
