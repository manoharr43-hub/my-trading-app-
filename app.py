import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import io
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 🚀 NSE AI QUANT PRO V7 ULTRA
# EMA9 VWAP CROSS + RSI + RVOL + EMA20
# =========================================================

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V7 ULTRA",
    layout="wide"
)

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=60000, key="refresh")

# =========================================================
# TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# TITLE
# =========================================================
st.title("🚀 NSE AI QUANT PRO V7 ULTRA")
st.subheader(f"🕒 LIVE TIME : {now.strftime('%H:%M:%S')} IST")

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","AXISBANK","ITC","LT","BHARTIARTL",
    "KOTAKBANK","ASIANPAINT","MARUTI","TITAN","WIPRO",
    "ULTRACEMCO","BAJFINANCE","BAJAJFINSV","HINDUNILVR",
    "SUNPHARMA","TATAMOTORS","TATASTEEL","POWERGRID",
    "NTPC","ONGC","COALINDIA","JSWSTEEL","HCLTECH",
    "TECHM","INDUSINDBK","ADANIENT","ADANIPORTS",
    "ADANIGREEN","HAL","BEL","BHEL","DLF","LODHA",
    "IRCTC","PFC","RECLTD","BANKBARODA","PNB",
    "CANBK","IDFCFIRSTB","YESBANK","IOC","BPCL"
]

# =========================================================
# INDICATORS
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty:
        return df

    # VWAP
    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby('Date')['PV'].cumsum()
        /
        df.groupby('Date')['Volume'].cumsum()
    )

    # EMA
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()

    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # RVOL
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)

    # ATR
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()

    df['MACD'] = ema12 - ema26
    df['MACD_SIGNAL'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df

# =========================================================
# DOWNLOAD DATA
# =========================================================
@st.cache_data(ttl=60)
def fetch_data(period="5d"):

    tickers = [s + ".NS" for s in stocks] + ["^NSEI"]

    data = yf.download(
        tickers=tickers,
        period=period,
        interval="15m",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True
    )

    return data

# =========================================================
# SIGNAL ENGINE
# =========================================================
def generate_signal(df, nifty_df, i, stock):

    row = df.iloc[i]
    prev = df.iloc[i - 1]

    # NIFTY TREND
    nifty_sync = nifty_df.reindex(df.index).ffill()

    if i >= len(nifty_sync):
        return None

    n_row = nifty_sync.iloc[i]

    market_bullish = n_row['Close'] > n_row['EMA20']
    market_bearish = n_row['Close'] < n_row['EMA20']

    # EMA9 VWAP CROSS
    buy_cross = (
        prev['EMA9'] < prev['VWAP']
        and
        row['EMA9'] > row['VWAP']
    )

    sell_cross = (
        prev['EMA9'] > prev['VWAP']
        and
        row['EMA9'] < row['VWAP']
    )

    # MACD
    macd_bullish = row['MACD'] > row['MACD_SIGNAL']
    macd_bearish = row['MACD'] < row['MACD_SIGNAL']

    # BUY
    buy_signal = (
        buy_cross
        and
        row['RSI'] > 60
        and
        row['RVOL'] > 1.5
        and
        row['Close'] > row['EMA20']
        and
        macd_bullish
        and
        market_bullish
    )

    # SELL
    sell_signal = (
        sell_cross
        and
        row['RSI'] < 40
        and
        row['RVOL'] > 1.5
        and
        row['Close'] < row['EMA20']
        and
        macd_bearish
        and
        market_bearish
    )

    # AI SCORE
    score = round(
        (
            row['RVOL'] * 20
            +
            row['RSI']
        ) / 2,
        2
    )

    # BUY RETURN
    if buy_signal:

        return {
            "TIME": row.name.astimezone(IST).strftime('%d-%m %H:%M'),
            "STOCK": stock,
            "SIGNAL": "BUY",
            "PRICE": round(row['Close'], 2),
            "RSI": round(row['RSI'], 2),
            "RVOL": round(row['RVOL'], 2),
            "AI_SCORE": score
        }

    # SELL RETURN
    if sell_signal:

        return {
            "TIME": row.name.astimezone(IST).strftime('%d-%m %H:%M'),
            "STOCK": stock,
            "SIGNAL": "SELL",
            "PRICE": round(row['Close'], 2),
            "RSI": round(row['RSI'], 2),
            "RVOL": round(row['RVOL'], 2),
            "AI_SCORE": score
        }

    return None

# =========================================================
# UI TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔍 LIVE SCANNER",
    "📊 BACKTEST"
])

# =========================================================
# LIVE SCANNER
# =========================================================
with tab1:

    st.info("15 MIN EMA9 VWAP AI SCANNER")

    if st.button("🚀 START LIVE SCAN"):

        with st.spinner("Scanning NSE Stocks..."):

            all_data = fetch_data("5d")

            nifty = add_indicators(
                all_data["^NSEI"].dropna()
            )

            results = []

            for stock in stocks:

                try:

                    ticker = stock + ".NS"

                    if ticker not in all_data:
                        continue

                    raw = all_data[ticker].dropna()

                    if raw.empty or len(raw) < 30:
                        continue

                    df = add_indicators(raw)

                    for i in range(25, len(df)):

                        signal = generate_signal(
                            df,
                            nifty,
                            i,
                            stock
                        )

                        if signal:
                            results.append(signal)

                except:
                    continue

            # =================================================
            # RESULTS
            # =================================================
            if results:

                df_res = pd.DataFrame(results)

                df_res = df_res.drop_duplicates(
                    subset=["STOCK", "SIGNAL"],
                    keep="last"
                )

                df_res = df_res.sort_values(
                    by="AI_SCORE",
                    ascending=False
                )

                # MARKET TREND
                nifty_last = nifty.iloc[-1]

                if nifty_last['Close'] > nifty_last['EMA20']:
                    st.success("📈 MARKET TREND : BULLISH")
                else:
                    st.error("📉 MARKET TREND : BEARISH")

                # METRICS
                total_buy = len(df_res[df_res['SIGNAL'] == "BUY"])
                total_sell = len(df_res[df_res['SIGNAL'] == "SELL"])

                c1, c2, c3 = st.columns(3)

                c1.metric("TOTAL SIGNALS", len(df_res))
                c2.metric("BUY SIGNALS", total_buy)
                c3.metric("SELL SIGNALS", total_sell)

                # COLOR STYLE
                def color_signal(val):

                    if val == "BUY":
                        return "background-color: green; color:white"

                    if val == "SELL":
                        return "background-color: red; color:white"

                    return ""

                st.dataframe(
                    df_res.style.applymap(
                        color_signal,
                        subset=['SIGNAL']
                    ),
                    use_container_width=True
                )

                # DOWNLOAD
                output = io.BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine='xlsxwriter'
                ) as writer:

                    df_res.to_excel(
                        writer,
                        index=False,
                        sheet_name='Signals'
                    )

                st.download_button(
                    "📥 DOWNLOAD SIGNALS EXCEL",
                    output.getvalue(),
                    file_name="NSE_AI_SIGNALS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.warning("No Strong Signals Found")

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    st.info("AI BACKTEST ENGINE")

    if st.button("📊 RUN BACKTEST"):

        with st.spinner("Running Backtest..."):

            bt_data = fetch_data("10d")

            nifty = add_indicators(
                bt_data["^NSEI"].dropna()
            )

            bt_results = []

            for stock in stocks:

                try:

                    ticker = stock + ".NS"

                    if ticker not in bt_data:
                        continue

                    raw = bt_data[ticker].dropna()

                    if raw.empty or len(raw) < 50:
                        continue

                    df = add_indicators(raw)

                    for i in range(30, len(df)-20):

                        signal = generate_signal(
                            df,
                            nifty,
                            i,
                            stock
                        )

                        if signal:

                            entry = signal['PRICE']

                            atr = df.iloc[i]['ATR']

                            if signal['SIGNAL'] == "BUY":

                                sl = entry - (atr * 1.5)
                                tp = entry + (atr * 2.5)

                            else:

                                sl = entry + (atr * 1.5)
                                tp = entry - (atr * 2.5)

                            result = "OPEN"

                            # CHECK FUTURE CANDLES
                            for j in range(i+1, min(i+20, len(df))):

                                nxt = df.iloc[j]

                                # BUY
                                if signal['SIGNAL'] == "BUY":

                                    if nxt['Low'] <= sl:
                                        result = "LOSS"
                                        break

                                    if nxt['High'] >= tp:
                                        result = "PROFIT"
                                        break

                                # SELL
                                else:

                                    if nxt['High'] >= sl:
                                        result = "LOSS"
                                        break

                                    if nxt['Low'] <= tp:
                                        result = "PROFIT"
                                        break

                            bt_results.append({
                                "STOCK": stock,
                                "SIGNAL": signal['SIGNAL'],
                                "RESULT": result
                            })

                except:
                    continue

            # =================================================
            # BACKTEST RESULTS
            # =================================================
            if bt_results:

                df_bt = pd.DataFrame(bt_results)

                wins = len(
                    df_bt[df_bt['RESULT'] == "PROFIT"]
                )

                losses = len(
                    df_bt[df_bt['RESULT'] == "LOSS"]
                )

                total = wins + losses

                if total > 0:
                    winrate = round(
                        (wins / total) * 100,
                        2
                    )
                else:
                    winrate = 0

                st.success("✅ BACKTEST COMPLETE")

                a1, a2, a3, a4 = st.columns(4)

                a1.metric("TOTAL TRADES", total)
                a2.metric("PROFIT", wins)
                a3.metric("LOSS", losses)
                a4.metric("WIN RATE", f"{winrate}%")

                st.dataframe(
                    df_bt,
                    use_container_width=True
                )

                # DOWNLOAD
                bt_output = io.BytesIO()

                with pd.ExcelWriter(
                    bt_output,
                    engine='xlsxwriter'
                ) as writer:

                    df_bt.to_excel(
                        writer,
                        index=False,
                        sheet_name='Backtest'
                    )

                st.download_button(
                    "📥 DOWNLOAD BACKTEST",
                    bt_output.getvalue(),
                    file_name="BACKTEST_REPORT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.warning("No Backtest Trades Found")
