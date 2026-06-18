# ============================================
# NSE PRO INSTITUTIONAL SCANNER V11
# PART 1
# ============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import io

from datetime import datetime
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

# --------------------------------------------
# PAGE CONFIG
# --------------------------------------------
st.set_page_config(
    page_title="NSE PRO SCANNER V11",
    page_icon="🚀",
    layout="wide"
)

# --------------------------------------------
# CUSTOM CSS
# --------------------------------------------
st.markdown("""
<style>

.stApp {
    background-color:#050816;
    color:white;
}

[data-testid="stSidebar"]{
    background:#111827;
}

h1,h2,h3,h4{
    color:white;
}

.stButton>button{
    width:100%;
    height:50px;
    border-radius:10px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------
# HEADER
# --------------------------------------------
st.title("🚀 NSE PRO INSTITUTIONAL SCANNER V11")

st.caption(
    f"Live Time : "
    f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
)

# --------------------------------------------
# SIDEBAR
# --------------------------------------------
st.sidebar.header("⚙ Scanner Settings")

timeframe = st.sidebar.selectbox(
    "Timeframe",
    [
        "5m",
        "15m",
        "30m",
        "1h",
        "1d"
    ],
    index=1
)

period = st.sidebar.selectbox(
    "Period",
    [
        "5d",
        "1mo",
        "3mo",
        "6mo"
    ],
    index=1
)

min_ai_score = st.sidebar.slider(
    "Minimum AI Score",
    0,
    100,
    20
)

min_rvol = st.sidebar.slider(
    "Minimum RVOL",
    0.5,
    5.0,
    1.0,
    0.1
)

# --------------------------------------------
# NSE SYMBOLS
# --------------------------------------------
NSE_SYMBOLS = [

    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "LT.NS",
    "ITC.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",

    "BAJFINANCE.NS",
    "ASIANPAINT.NS",
    "MARUTI.NS",
    "TITAN.NS",
    "ULTRACEMCO.NS",

    "WIPRO.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "TATAMOTORS.NS",
    "SUNPHARMA.NS",

    "HCLTECH.NS",
    "TECHM.NS",
    "ADANIPORTS.NS",
    "ADANIENT.NS",
    "INDUSINDBK.NS",

    "BHARTIARTL.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "HINDUNILVR.NS",
    "NESTLEIND.NS",

    "BAJAJFINSV.NS",
    "EICHERMOT.NS",
    "JSWSTEEL.NS",
    "TATASTEEL.NS",
    "GRASIM.NS",

    "BPCL.NS",
    "BRITANNIA.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "HEROMOTOCO.NS",

    "HDFCLIFE.NS",
    "SBILIFE.NS",
    "DIVISLAB.NS",
    "APOLLOHOSP.NS",
    "SHRIRAMFIN.NS",

    "M&M.NS",
    "PIDILITIND.NS",
    "DABUR.NS",
    "DLF.NS",
    "GODREJCP.NS"
]

st.sidebar.success(
    f"Loaded Symbols: {len(NSE_SYMBOLS)}"
)# ============================================
# PART 2
# INDICATORS + AI ENGINE
# ============================================

# --------------------------------------------
# RSI
# --------------------------------------------
def calculate_rsi(df, period=14):

    delta = df["Close"].diff()

    gain = delta.where(
        delta > 0,
        0
    )

    loss = -delta.where(
        delta < 0,
        0
    )

    avg_gain = gain.rolling(
        period
    ).mean()

    avg_loss = loss.rolling(
        period
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return float(
        rsi.iloc[-1]
    )


# --------------------------------------------
# VWAP
# --------------------------------------------
def calculate_vwap(df):

    tp = (
        df["High"] +
        df["Low"] +
        df["Close"]
    ) / 3

    vwap = (
        tp * df["Volume"]
    ).cumsum() / (
        df["Volume"]
    ).cumsum()

    return float(
        vwap.iloc[-1]
    )


# --------------------------------------------
# ATR
# --------------------------------------------
def calculate_atr(
    df,
    period=14
):

    high_low = (
        df["High"] -
        df["Low"]
    )

    high_close = np.abs(
        df["High"] -
        df["Close"].shift()
    )

    low_close = np.abs(
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

    atr = tr.rolling(
        period
    ).mean()

    return float(
        atr.iloc[-1]
    )


# --------------------------------------------
# RVOL
# --------------------------------------------
def calculate_rvol(df):

    current_volume = (
        df["Volume"].iloc[-1]
    )

    avg_volume = (
        df["Volume"]
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    if avg_volume <= 0:
        return 0

    return float(
        current_volume /
        avg_volume
    )


# --------------------------------------------
# EMA
# --------------------------------------------
def ema(
    series,
    period
):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()


# --------------------------------------------
# SMA
# --------------------------------------------
def sma(
    series,
    period
):

    return (
        series
        .rolling(period)
        .mean()
    )


# --------------------------------------------
# AI SCORE ENGINE
# --------------------------------------------
def calculate_ai_score(
    close,
    ema20,
    ema50,
    rsi,
    rvol,
    vwap,
    atr_pct
):

    score = 0

    # Trend
    if close > ema20:
        score += 20

    if close > ema50:
        score += 20

    # RSI
    if rsi > 50:
        score += 10

    if rsi > 60:
        score += 10

    if rsi > 70:
        score += 10

    # Volume
    if rvol > 1.2:
        score += 10

    if rvol > 1.5:
        score += 10

    if rvol > 2:
        score += 10

    # VWAP
    if close > vwap:
        score += 5

    # Volatility
    if atr_pct > 2:
        score += 5

    return min(
        score,
        100
    )


# --------------------------------------------
# SIGNAL ENGINE
# --------------------------------------------
def generate_signal(
    close,
    ema20,
    ema50,
    rsi,
    rvol
):

    if (
        close > ema20 and
        close > ema50 and
        rsi > 65 and
        rvol > 1.5
    ):
        return "STRONG BUY"

    if (
        close > ema20 and
        rsi > 50
    ):
        return "BUY"

    if (
        close < ema20 and
        rsi < 40
    ):
        return "SELL"

    return "NEUTRAL"# ============================================
# PART 3
# SCANNER ENGINE
# ============================================

# --------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------
def get_stock_data(symbol):

    try:

        actual_period = period

        if timeframe in [
            "5m",
            "15m",
            "30m"
        ]:
            actual_period = "5d"

        df = yf.download(
            symbol,
            period=actual_period,
            interval=timeframe,
            progress=False,
            auto_adjust=True,
            threads=False
        )

        # MultiIndex Fix
        if isinstance(
            df.columns,
            pd.MultiIndex
        ):
            df.columns = (
                df.columns
                .get_level_values(0)
            )

        return df

    except Exception:
        return pd.DataFrame()


# --------------------------------------------
# SCAN SINGLE STOCK
# --------------------------------------------
def scan_stock(symbol):

    try:

        df = get_stock_data(symbol)

        if df.empty:
            return None

        if len(df) < 50:
            return None

        close = float(
            df["Close"].iloc[-1]
        )

        high = float(
            df["High"].iloc[-1]
        )

        low = float(
            df["Low"].iloc[-1]
        )

        volume = float(
            df["Volume"].iloc[-1]
        )

        rsi = calculate_rsi(df)

        vwap = calculate_vwap(df)

        atr = calculate_atr(df)

        rvol = calculate_rvol(df)

        ema20 = float(
            ema(
                df["Close"],
                20
            ).iloc[-1]
        )

        ema50 = float(
            ema(
                df["Close"],
                50
            ).iloc[-1]
        )

        atr_pct = round(
            (atr / close) * 100,
            2
        )

        ai_score = calculate_ai_score(
            close,
            ema20,
            ema50,
            rsi,
            rvol,
            vwap,
            atr_pct
        )

        signal = generate_signal(
            close,
            ema20,
            ema50,
            rsi,
            rvol
        )

        if (
            ai_score >= min_ai_score
            and
            rvol >= min_rvol
        ):

            return {

                "Symbol":
                    symbol,

                "Price":
                    round(close, 2),

                "High":
                    round(high, 2),

                "Low":
                    round(low, 2),

                "Volume":
                    int(volume),

                "RSI":
                    round(rsi, 2),

                "RVOL":
                    round(rvol, 2),

                "VWAP":
                    round(vwap, 2),

                "ATR%":
                    round(
                        atr_pct,
                        2
                    ),

                "EMA20":
                    round(
                        ema20,
                        2
                    ),

                "EMA50":
                    round(
                        ema50,
                        2
                    ),

                "AI Score":
                    int(
                        ai_score
                    ),

                "Signal":
                    signal
            }

    except Exception as e:

        return {
            "Symbol": symbol,
            "Error": str(e)
        }

    return None


# --------------------------------------------
# MULTI THREAD SCANNER
# --------------------------------------------
def run_scanner():

    results = []

    progress = st.progress(0)

    total = len(
        NSE_SYMBOLS
    )

    completed = 0

    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:

        futures = {

            executor.submit(
                scan_stock,
                symbol
            ): symbol

            for symbol
            in NSE_SYMBOLS
        }

        for future in as_completed(
            futures
        ):

            completed += 1

            progress.progress(
                completed / total
            )

            result = (
                future.result()
            )

            if (
                result
                and
                "AI Score"
                in result
            ):
                results.append(
                    result
                )

    progress.empty()

    return results# ============================================
# PART 4
# FINAL UI
# ============================================

st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Institutional Scanner")

with col2:
    scan_button = st.button(
        "🚀 RUN SCAN"
    )

# --------------------------------------------
# RUN SCAN
# --------------------------------------------
if scan_button:

    start_time = time.time()

    with st.spinner(
        "Scanning NSE Stocks..."
    ):

        results = run_scanner()

    end_time = time.time()

    scan_time = round(
        end_time - start_time,
        2
    )

    # ----------------------------------------
    # RESULTS FOUND
    # ----------------------------------------
    if len(results) > 0:

        df_results = pd.DataFrame(
            results
        )

        df_results = (
            df_results
            .sort_values(
                by="AI Score",
                ascending=False
            )
            .reset_index(
                drop=True
            )
        )

        # ------------------------------------
        # METRICS
        # ------------------------------------
        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "Signals",
            len(df_results)
        )

        m2.metric(
            "Top AI",
            int(
                df_results[
                    "AI Score"
                ].max()
            )
        )

        m3.metric(
            "Scan Time",
            f"{scan_time}s"
        )

        strong_count = len(
            df_results[
                df_results[
                    "Signal"
                ] == "STRONG BUY"
            ]
        )

        m4.metric(
            "Strong Buy",
            strong_count
        )

        st.markdown("---")

        # ------------------------------------
        # TOP 10
        # ------------------------------------
        st.subheader(
            "🔥 Top 10 Institutional Signals"
        )

        st.dataframe(
            df_results.head(10),
            use_container_width=True
        )

        st.markdown("---")

        # ------------------------------------
        # STRONG BUY
        # ------------------------------------
        strong_buy = df_results[
            df_results["Signal"]
            ==
            "STRONG BUY"
        ]

        if len(strong_buy) > 0:

            st.subheader(
                "🚀 Strong Buy Stocks"
            )

            st.dataframe(
                strong_buy,
                use_container_width=True
            )

            st.markdown("---")

        # ------------------------------------
        # ALL RESULTS
        # ------------------------------------
        st.subheader(
            "📋 All Signals"
        )

        st.dataframe(
            df_results,
            use_container_width=True
        )

        # ------------------------------------
        # CSV EXPORT
        # ------------------------------------
        csv = (
            df_results
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=(
                "NSE_PRO_V11_"
                +
                datetime.now().strftime(
                    "%Y%m%d_%H%M"
                )
                +
                ".csv"
            ),
            mime="text/csv"
        )

    # ----------------------------------------
    # NO SIGNALS
    # ----------------------------------------
    else:

        st.warning(
            "⚠ No Institutional Signals Found"
        )

        st.info(
            """
            Suggestions:

            • Reduce AI Score to 10-20

            • Reduce RVOL to 1.0

            • Use 1D timeframe

            • Add more NSE stocks
            """
        )

# ============================================
# FOOTER
# ============================================

st.markdown("---")

st.caption(
    """
    NSE PRO Institutional Scanner V11

    Indicators:
    RSI | VWAP | ATR | RVOL
    EMA20 | EMA50 | AI Score

    Powered by:
    Streamlit + Yahoo Finance
    """
)
