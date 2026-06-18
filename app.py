# =========================================================
# 🚀 NSE PRO INSTITUTIONAL SCANNER V10
# PART 1
# =========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import io
import time
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="🚀 NSE PRO INSTITUTIONAL SCANNER V10",
    layout="wide"
)

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE PRO INSTITUTIONAL SCANNER V10")
st.caption(f"Live Time : {now.strftime('%d-%m-%Y %H:%M:%S')}")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙ Scanner Settings")

    interval = st.selectbox(
        "Timeframe",
        ["15m", "30m", "1h"],
        index=0
    )

    period = st.selectbox(
        "Period",
        ["5d", "1mo", "3mo"],
        index=0
    )

    min_ai_score = st.slider(
        "Minimum AI Score",
        0,
        100,
        60
    )

    rvol_filter = st.slider(
        "Minimum RVOL",
        1.0,
        5.0,
        1.5
    )

# =========================================================
# NSE500 LIST
# =========================================================

@st.cache_data(ttl=86400)
def load_nse500():

    try:

        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

        df = pd.read_csv(url)

        stocks = sorted(
            df["Symbol"]
            .dropna()
            .unique()
            .tolist()
        )

        return stocks

    except:

        return [
            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "LT",
            "ITC"
        ]

stocks = load_nse500()

# =========================================================
# INDICATORS
# =========================================================

def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_vwap(df):

    tp = (
        df["High"] +
        df["Low"] +
        df["Close"]
    ) / 3

    vwap = (
        (tp * df["Volume"]).cumsum()
        /
        df["Volume"].cumsum()
    )

    return vwap


def calculate_atr(df, period=14):

    high_low = df["High"] - df["Low"]

    high_close = abs(
        df["High"] -
        df["Close"].shift()
    )

    low_close = abs(
        df["Low"] -
        df["Close"].shift()
    )

    tr = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(period).mean()

    return atr


def calculate_rvol(df):

    avg_vol = df["Volume"].rolling(20).mean()

    rvol = (
        df["Volume"] /
        avg_vol
    )

    return rvol

# =========================================================
# DATA DOWNLOAD
# =========================================================

@st.cache_data(ttl=300)
def get_data(symbol):

    try:

        df = yf.download(
            f"{symbol}.NS",
            interval=interval,
            period=period,
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        return df

    except:
        return None# =========================================================
# PART 2
# CHOCH + BOS + AI ENGINE
# =========================================================

def detect_structure(df, window=8):

    try:

        if len(df) < 50:
            return None

        swing_high = (
            df["High"]
            .rolling(window, center=True)
            .max()
        )

        swing_low = (
            df["Low"]
            .rolling(window, center=True)
            .min()
        )

        last_high = float(
            swing_high.ffill().iloc[-2]
        )

        last_low = float(
            swing_low.ffill().iloc[-2]
        )

        close = float(
            df["Close"].iloc[-1]
        )

        ema20 = (
            df["Close"]
            .ewm(span=20)
            .mean()
            .iloc[-1]
        )

        ema50 = (
            df["Close"]
            .ewm(span=50)
            .mean()
            .iloc[-1]
        )

        bullish_trend = ema20 > ema50

        # BOS UP

        if close > last_high and bullish_trend:
            return "BOS 📈"

        # BOS DOWN

        if close < last_low and not bullish_trend:
            return "BOS 📉"

        # Bullish CHOCH

        if close > last_high and not bullish_trend:
            return "CHOCH 🔄 Bullish"

        # Bearish CHOCH

        if close < last_low and bullish_trend:
            return "CHOCH 🔄 Bearish"

        return None

    except:
        return None


# =========================================================
# AI SCORE
# =========================================================

def calculate_ai_score(df, signal):

    score = 0

    try:

        close = float(df["Close"].iloc[-1])

        ema20 = (
            df["Close"]
            .ewm(span=20)
            .mean()
            .iloc[-1]
        )

        ema50 = (
            df["Close"]
            .ewm(span=50)
            .mean()
            .iloc[-1]
        )

        rsi = calculate_rsi(
            df["Close"]
        ).iloc[-1]

        vwap = calculate_vwap(df).iloc[-1]

        rvol = calculate_rvol(df).iloc[-1]

        # Trend

        if ema20 > ema50:
            score += 20

        # RSI

        if rsi > 60:
            score += 20

        # VWAP

        if close > vwap:
            score += 20

        # RVOL

        if rvol > 1.5:
            score += 20

        # Signal

        if signal is not None:
            score += 20

        return int(score)

    except:
        return 0


# =========================================================
# INSTITUTIONAL SIGNAL
# =========================================================

def generate_signal(df):

    try:

        signal = detect_structure(df)

        if signal is None:
            return None

        close = float(df["Close"].iloc[-1])

        ema20 = (
            df["Close"]
            .ewm(span=20)
            .mean()
            .iloc[-1]
        )

        ema50 = (
            df["Close"]
            .ewm(span=50)
            .mean()
            .iloc[-1]
        )

        rsi = calculate_rsi(
            df["Close"]
        ).iloc[-1]

        vwap = calculate_vwap(df).iloc[-1]

        rvol = calculate_rvol(df).iloc[-1]

        atr = calculate_atr(df).iloc[-1]

        ai_score = calculate_ai_score(
            df,
            signal
        )

        direction = "NEUTRAL"

        # BUY CONDITIONS

        if (
            ema20 > ema50
            and rsi > 60
            and close > vwap
            and rvol > 1.5
        ):

            direction = "BUY 🟢"

        # SELL CONDITIONS

        elif (
            ema20 < ema50
            and rsi < 40
            and close < vwap
            and rvol > 1.5
        ):

            direction = "SELL 🔴"

        stoploss = round(
            close - atr,
            2
        )

        target = round(
            close + (atr * 2),
            2
        )

        return {

            "Signal": signal,

            "Direction": direction,

            "Close": round(close, 2),

            "EMA20": round(ema20, 2),

            "EMA50": round(ema50, 2),

            "RSI": round(rsi, 2),

            "VWAP": round(vwap, 2),

            "RVOL": round(rvol, 2),

            "ATR": round(atr, 2),

            "AI Score": ai_score,

            "Target": target,

            "Stoploss": stoploss

        }

    except:

        return None


# =========================================================
# SINGLE STOCK ANALYSIS
# =========================================================

def analyze_stock(symbol):

    try:

        df = get_data(symbol)

        if df is None:
            return None

        result = generate_signal(df)

        if result is None:
            return None

        result["Stock"] = symbol

        return result

    except:

        return None# =========================================================
# PART 3
# NSE500 SCANNER + BACKTEST + EXCEL
# =========================================================

def scan_all_stocks():

    results = []

    progress = st.progress(0)

    total = len(stocks)

    with ThreadPoolExecutor(max_workers=15) as executor:

        futures = {
            executor.submit(
                analyze_stock,
                symbol
            ): symbol
            for symbol in stocks
        }

        completed = 0

        for future in as_completed(futures):

            completed += 1

            progress.progress(
                completed / total
            )

            try:

                result = future.result()

                if result:

                    if (
                        result["AI Score"]
                        >= min_ai_score
                        and
                        result["RVOL"]
                        >= rvol_filter
                    ):

                        results.append(result)

            except:
                pass

    progress.empty()

    return pd.DataFrame(results)


# =========================================================
# BACKTEST
# =========================================================

def run_backtest(symbol):

    df = get_data(symbol)

    if df is None:
        return None

    trades = []

    for i in range(60, len(df)):

        sub = df.iloc[:i + 1]

        result = generate_signal(sub)

        if result is None:
            continue

        entry = float(
            sub["Close"].iloc[-1]
        )

        atr = float(
            calculate_atr(sub).iloc[-1]
        )

        stoploss = entry - atr

        target = entry + (atr * 2)

        future_close = float(
            df["Close"].iloc[
                min(
                    i + 5,
                    len(df) - 1
                )
            ]
        )

        outcome = "LOSS"

        if future_close >= target:
            outcome = "WIN"

        trades.append({

            "Date":
            str(sub.index[-1]),

            "Entry":
            round(entry, 2),

            "Target":
            round(target, 2),

            "Stoploss":
            round(stoploss, 2),

            "Exit":
            round(future_close, 2),

            "Result":
            outcome

        })

    bt = pd.DataFrame(trades)

    return bt


# =========================================================
# DASHBOARD
# =========================================================

st.divider()

if st.button("🚀 RUN NSE500 INSTITUTIONAL SCAN"):

    with st.spinner(
        "Scanning NSE500..."
    ):

        results_df = scan_all_stocks()

    if results_df.empty:

        st.warning(
            "No Institutional Signals Found"
        )

    else:

        st.success(
            f"{len(results_df)} Signals Found"
        )

        results_df = (
            results_df
            .sort_values(
                "AI Score",
                ascending=False
            )
        )

        # =====================
        # METRICS
        # =====================

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Signals",
            len(results_df)
        )

        c2.metric(
            "Top AI Score",
            int(
                results_df[
                    "AI Score"
                ].max()
            )
        )

        c3.metric(
            "Average RSI",
            round(
                results_df[
                    "RSI"
                ].mean(),
                2
            )
        )

        c4.metric(
            "Average RVOL",
            round(
                results_df[
                    "RVOL"
                ].mean(),
                2
            )
        )

        st.dataframe(
            results_df,
            use_container_width=True
        )

        # =====================
        # EXCEL DOWNLOAD
        # =====================

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="xlsxwriter"
        ) as writer:

            results_df.to_excel(
                writer,
                index=False,
                sheet_name="Scanner"
            )

        st.download_button(
            "📥 Download Scanner Excel",
            excel_buffer.getvalue(),
            file_name="NSE_V10_Scanner.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # =====================
        # STOCK SELECT
        # =====================

        selected_stock = st.selectbox(
            "Select Stock For Backtest",
            results_df["Stock"]
        )

        if st.button(
            "📈 RUN BACKTEST"
        ):

            bt = run_backtest(
                selected_stock
            )

            if bt is None or bt.empty:

                st.warning(
                    "No Backtest Data"
                )

            else:

                wins = len(
                    bt[
                        bt["Result"]
                        == "WIN"
                    ]
                )

                losses = len(
                    bt[
                        bt["Result"]
                        == "LOSS"
                    ]
                )

                total_trades = len(bt)

                win_rate = round(
                    (
                        wins
                        /
                        total_trades
                    ) * 100,
                    2
                )

                st.subheader(
                    f"📊 Backtest : {selected_stock}"
                )

                a, b, c = st.columns(3)

                a.metric(
                    "Trades",
                    total_trades
                )

                b.metric(
                    "Wins",
                    wins
                )

                c.metric(
                    "Win Rate %",
                    win_rate
                )

                st.dataframe(
                    bt,
                    use_container_width=True
                )

                backtest_excel = io.BytesIO()

                with pd.ExcelWriter(
                    backtest_excel,
                    engine="xlsxwriter"
                ) as writer:

                    bt.to_excel(
                        writer,
                        index=False,
                        sheet_name="Backtest"
                    )

                st.download_button(
                    "📥 Download Backtest",
                    backtest_excel.getvalue(),
                    file_name=f"{selected_stock}_Backtest.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# =========================================================
# END OF V10
# =========================================================
