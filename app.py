import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V22",
    layout="wide"
)

# =========================================================
# TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# TITLE
# =========================================================
st.markdown(
    """
    <h1 style='text-align:center;color:#22c55e;'>
    🚀 NSE AI QUANT PRO V22
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <h4 style='text-align:center;'>
    🕒 IST TIME : {now.strftime("%Y-%m-%d %H:%M:%S")}
    <br>
    EMA + VWAP + RSI + BB + REAL BACKTEST + SCORE ENGINE
    <br>
    FULL MARKET SESSION : 9:15 AM → 3:30 PM
    </h4>
    """,
    unsafe_allow_html=True
)

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN",
    "ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
    "ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY",
    "ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE",
    "BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK",
    "CIPLA","COALINDIA","DLF","DRREDDY","GAIL","HDFCBANK",
    "HCLTECH","HINDALCO","ICICIBANK","INFY","ITC",
    "JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC",
    "ONGC","RELIANCE","SBIN","SUNPHARMA","TATASTEEL",
    "TCS","TECHM","TITAN","WIPRO","ZOMATO"
]

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=300)
def fetch_data():

    tickers = [s + ".NS" for s in stocks]

    data = yf.download(
        tickers,
        period="10d",
        interval="15m",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True
    )

    return data

data_pool = fetch_data()

# =========================================================
# INDICATORS
# =========================================================
def get_indicators(df):

    df = df.copy()

    if len(df) < 50:
        return pd.DataFrame()

    # EMA
    df['EMA9'] = df['Close'].ewm(
        span=9,
        adjust=False
    ).mean()

    df['EMA21'] = df['Close'].ewm(
        span=21,
        adjust=False
    ).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby(df.index.date)['PV'].cumsum() /
        (
            df.groupby(df.index.date)['Volume'].cumsum()
            + 1e-9
        )
    )

    # BOLLINGER BANDS
    df['BB_MID'] = (
        df['Close']
        .rolling(20)
        .mean()
    )

    df['BB_STD'] = (
        df['Close']
        .rolling(20)
        .std()
    )

    df['BB_UPPER'] = (
        df['BB_MID'] +
        (df['BB_STD'] * 2)
    )

    df['BB_LOWER'] = (
        df['BB_MID'] -
        (df['BB_STD'] * 2)
    )

    # TRUE RANGE
    tr1 = df['High'] - df['Low']

    tr2 = abs(
        df['High'] -
        df['Close'].shift(1)
    )

    tr3 = abs(
        df['Low'] -
        df['Close'].shift(1)
    )

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    # ATR
    df['ATR'] = (
        tr.rolling(14)
        .mean()
    )

    # ADX
    plus_dm = (
        df['High']
        .diff()
        .clip(lower=0)
    )

    minus_dm = (
        df['Low']
        .diff()
        .clip(upper=0)
        .abs()
    )

    tr_smooth = (
        tr.rolling(14)
        .mean()
    )

    plus_di = (
        100 *
        (
            plus_dm
            .rolling(14)
            .mean()
            /
            (tr_smooth + 1e-9)
        )
    )

    minus_di = (
        100 *
        (
            minus_dm
            .rolling(14)
            .mean()
            /
            (tr_smooth + 1e-9)
        )
    )

    dx = (
        100 *
        (
            abs(plus_di - minus_di)
            /
            (plus_di + minus_di + 1e-9)
        )
    )

    df['ADX'] = (
        dx.rolling(14)
        .mean()
    )

    # RSI
    delta = df['Close'].diff()

    gain = (
        delta.where(delta > 0, 0)
        .rolling(14)
        .mean()
    )

    loss = (
        (-delta.where(delta < 0, 0))
        .rolling(14)
        .mean()
    )

    rs = gain / (loss + 1e-9)

    df['RSI'] = (
        100 -
        (100 / (1 + rs))
    )

    # RVOL
    df['RVOL'] = (
        df['Volume']
        /
        (
            df['Volume']
            .rolling(20)
            .mean()
            + 1e-9
        )
    )

    return df

# =========================================================
# SCORE ENGINE
# =========================================================
def calculate_score(row):

    score = 0

    if row['ADX'] > 22:
        score += 25

    if row['RVOL'] > 1.1:
        score += 25

    if 50 <= row['RSI'] <= 75:
        score += 25

    if abs(row['EMA9'] - row['EMA21']) > 0.2:
        score += 25

    return score

# =========================================================
# SCANNER ENGINE
# =========================================================
def scan(stock, mode="TODAY"):

    try:

        ticker = stock + ".NS"

        if ticker not in data_pool:
            return []

        raw = data_pool[ticker].dropna()

        if raw.empty:
            return []

        df = get_indicators(raw)

        if df.empty:
            return []

        # TIMEZONE FIX
        if df.index.tz is None:

            df.index = (
                df.index
                .tz_localize("UTC")
            )

        df.index = (
            df.index
            .tz_convert(IST)
        )

        # TODAY / BACKTEST
        if mode == "TODAY":

            scan_df = df[
                df.index.date == now.date()
            ]

        else:

            scan_df = df.copy()

        results = []

        for i in range(30, len(scan_df)-10):

            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]

            # =================================================
            # FULL MARKET SESSION
            # =================================================
            valid_time = (
                time(9, 15)
                <= row.name.time()
                <= time(15, 30)
            )

            # TREND
            strong_trend = (
                row['ADX'] > 22
            )

            # BB SAFETY
            bb_buy_safety = (
                row['Close']
                < row['BB_UPPER']
            )

            bb_sell_safety = (
                row['Close']
                > row['BB_LOWER']
            )

            # PULLBACK
            pb_buy = (
                prev['Low']
                <= prev['EMA21']
                and
                row['Close']
                > row['EMA21']
            )

            pb_sell = (
                prev['High']
                >= prev['EMA21']
                and
                row['Close']
                < row['EMA21']
            )

            # VOLUME
            vol_ok = (
                row['RVOL'] > 1.1
            )

            # =================================================
            # BUY SIGNAL
            # =================================================
            buy_sig = (

                row['EMA9']
                > row['EMA21']

                and

                row['Close']
                > row['VWAP']

                and

                (pb_buy or vol_ok)

                and

                50 < row['RSI'] < 75

                and

                strong_trend

                and

                valid_time

                and

                bb_buy_safety
            )

            # =================================================
            # SELL SIGNAL
            # =================================================
            sell_sig = (

                row['EMA9']
                < row['EMA21']

                and

                row['Close']
                < row['VWAP']

                and

                (pb_sell or vol_ok)

                and

                25 < row['RSI'] < 50

                and

                strong_trend

                and

                valid_time

                and

                bb_sell_safety
            )

            # =================================================
            # SIGNAL FOUND
            # =================================================
            if buy_sig or sell_sig:

                signal = (
                    "BUY"
                    if buy_sig
                    else "SELL"
                )

                entry = round(
                    row['Close'],
                    2
                )

                risk = (
                    row['ATR'] * 1.5
                )

                sl = (

                    round(
                        entry - risk,
                        2
                    )

                    if buy_sig

                    else

                    round(
                        entry + risk,
                        2
                    )
                )

                target = (

                    round(
                        entry + (risk * 2),
                        2
                    )

                    if buy_sig

                    else

                    round(
                        entry - (risk * 2),
                        2
                    )
                )

                # =================================================
                # REAL BACKTEST
                # =================================================
                future_df = (
                    scan_df.iloc[i+1:i+10]
                )

                status = "⏳ RUNNING"

                for _, frow in future_df.iterrows():

                    if buy_sig:

                        if frow['High'] >= target:

                            status = "✅ TGT HIT"
                            break

                        elif frow['Low'] <= sl:

                            status = "❌ SL HIT"
                            break

                    else:

                        if frow['Low'] <= target:

                            status = "✅ TGT HIT"
                            break

                        elif frow['High'] >= sl:

                            status = "❌ SL HIT"
                            break

                # LIVE PRICE
                ltp = round(
                    scan_df.iloc[-1]['Close'],
                    2
                )

                score = (
                    calculate_score(row)
                )

                results.append({

                    "DATE":
                    row.name.strftime("%Y-%m-%d"),

                    "TIME":
                    row.name.strftime("%H:%M"),

                    "STOCK":
                    stock,

                    "SIGNAL":
                    signal,

                    "ENTRY":
                    entry,

                    "LTP":
                    ltp,

                    "SL":
                    sl,

                    "TARGET":
                    target,

                    "STATUS":
                    status,

                    "ADX":
                    round(row['ADX'], 1),

                    "RSI":
                    round(row['RSI'], 1),

                    "RVOL":
                    round(row['RVOL'], 2),

                    "SCORE":
                    score
                })

        return results

    except Exception as e:

        print(f"{stock} ERROR : {e}")

        return []

# =========================================================
# EXCEL EXPORT
# =========================================================
def to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine='xlsxwriter'
    ) as writer:

        df.to_excel(
            writer,
            index=False
        )

    return output.getvalue()

# =========================================================
# STATUS STYLE
# =========================================================
def style_status(val):

    if "TGT" in str(val):

        return (
            'color:#22c55e;'
            'font-weight:bold'
        )

    if "SL" in str(val):

        return (
            'color:#ef4444;'
            'font-weight:bold'
        )

    return (
        'color:#facc15;'
        'font-weight:bold'
    )

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔍 LIVE SCANNER",
    "📊 BACKTEST REPORT"
])

# =========================================================
# LIVE SCANNER
# =========================================================
with tab1:

    st.subheader(
        "🚀 LIVE MARKET SCANNER"
    )

    if st.button(
        "🚀 RUN LIVE SCANNER"
    ):

        with st.spinner(
            "Scanning NSE Stocks..."
        ):

            with ThreadPoolExecutor(
                max_workers=10
            ) as executor:

                results = executor.map(
                    lambda s: scan(
                        s,
                        "TODAY"
                    ),
                    stocks
                )

            res = [

                item

                for sublist in results

                for item in sublist
            ]

        if len(res) > 0:

            df = pd.DataFrame(res)

            df = df.sort_values(
                ['SCORE', 'TIME'],
                ascending=[False, False]
            )

            st.success(
                f"{len(df)} Signals Found"
            )

            st.dataframe(
                df.style.map(
                    style_status,
                    subset=['STATUS']
                ),
                use_container_width=True
            )

            st.download_button(
                "📥 Download Scanner Excel",
                data=to_excel(df),
                file_name=f"Scanner_V22_{now.date()}.xlsx"
            )

        else:

            st.warning(
                "⚠️ No Signals Found"
            )

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    st.subheader(
        "📊 REAL BACKTEST REPORT"
    )

    if st.button(
        "📊 RUN BACKTEST"
    ):

        with st.spinner(
            "Running Backtest..."
        ):

            with ThreadPoolExecutor(
                max_workers=10
            ) as executor:

                results_bt = executor.map(
                    lambda s: scan(
                        s,
                        "BACKTEST"
                    ),
                    stocks
                )

            res_bt = [

                item

                for sublist in results_bt

                for item in sublist
            ]

        if len(res_bt) > 0:

            df_bt = pd.DataFrame(res_bt)

            df_bt = df_bt.sort_values(
                ['DATE', 'TIME'],
                ascending=False
            )

            wins = len(
                df_bt[
                    df_bt['STATUS']
                    .str.contains("TGT")
                ]
            )

            losses = len(
                df_bt[
                    df_bt['STATUS']
                    .str.contains("SL")
                ]
            )

            total = wins + losses

            accuracy = (

                round(
                    (wins / total) * 100,
                    2
                )

                if total > 0

                else 0
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "🎯 Accuracy",
                f"{accuracy}%"
            )

            c2.metric(
                "✅ Wins",
                wins
            )

            c3.metric(
                "❌ Losses",
                losses
            )

            st.dataframe(
                df_bt.style.map(
                    style_status,
                    subset=['STATUS']
                ),
                use_container_width=True
            )

            st.download_button(
                "📥 Download Backtest Excel",
                data=to_excel(df_bt),
                file_name="Backtest_V22.xlsx"
            )

        else:

            st.warning(
                "⚠️ No Backtest Signals Found"
            )
