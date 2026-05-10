import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================
# APP CONFIG
# =========================
st.set_page_config(
    page_title="🚀 NSE AI V60 INSTITUTIONAL",
    layout="wide"
)

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V60 INSTITUTIONAL")
st.markdown(
    f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}"
)

# =========================
# NSE STOCKS
# =========================
def get_stocks():

    return [

        "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
        "SBIN","AXISBANK","KOTAKBANK","LT","ITC",
        "BHARTIARTL","HCLTECH","WIPRO","TECHM",
        "SUNPHARMA","DRREDDY","CIPLA","TITAN",
        "MARUTI","TATAMOTORS","BAJFINANCE",
        "BAJAJFINSV","ADANIENT","ADANIPORTS",
        "NTPC","POWERGRID","ONGC","COALINDIA",
        "JSWSTEEL","TATASTEEL","HINDALCO",
        "GRASIM","ULTRACEMCO","INDUSINDBK",
        "M&M","DIVISLAB","APOLLOHOSP",
        "EICHERMOT","HEROMOTOCO","BRITANNIA",
        "NESTLEIND","DABUR","MARICO","COLPAL",
        "GODREJCP","TATACONSUM","SBILIFE",
        "HDFCLIFE","ICICIPRULI","LICI",
        "PNB","BANKBARODA","CANBK","FEDERALBNK",
        "IDFCFIRSTB","AUBANK","RBLBANK",
        "UNIONBANK","INDIANB","YESBANK",
        "ALKEM","BIOCON","LUPIN","AUROPHARMA",
        "GLENMARK","TORNTPHARM","ZYDUSLIFE",
        "LTIM","PERSISTENT","COFORGE",
        "KPITTECH","TATAELXSI","MPHASIS",
        "ASHOKLEY","TVSMOTOR","BALKRISIND",
        "MOTHERSON","EXIDEIND","MRF",
        "SAIL","NMDC","VEDL","JINDALSTEL",
        "IOC","BPCL","HINDPETRO","GAIL",
        "IGL","PETRONET","ACC","AMBUJACEM",
        "DALBHARAT","DLF","GODREJPROP",
        "OBEROIRLTY","HAL","BEL","BDL",
        "MAZDOCK","IRCTC","RVNL","IRFC",
        "RAILTEL","ABB","BHEL","HAVELLS",
        "POLYCAB","TRENT","DMART",
        "SUZLON","NHPC","SJVN","HFCL",
        "NBCC","IRB","IDEA","TATAPOWER",
        "ADANIGREEN","ADANIPOWER"

    ]

stocks = get_stocks()

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=300)
def load_data():

    tickers = [s + ".NS" for s in stocks]

    return yf.download(

        tickers=tickers,

        period="10d",

        interval="15m",

        group_by="ticker",

        auto_adjust=True,

        threads=True,

        progress=False
    )

data = load_data()

# =========================
# RSI
# =========================
def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    return 100 - (100 / (1 + rs))

# =========================
# VWAP
# =========================
def vwap(df):

    tp = (
        df["High"]
        + df["Low"]
        + df["Close"]
    ) / 3

    return (
        (tp * df["Volume"]).cumsum()
        /
        (df["Volume"].cumsum() + 1e-9)
    )

# =========================
# SUPERTREND
# =========================
def supertrend(df, period=10, multiplier=3):

    hl2 = (
        df["High"]
        + df["Low"]
    ) / 2

    tr1 = df["High"] - df["Low"]

    tr2 = abs(
        df["High"]
        - df["Close"].shift()
    )

    tr3 = abs(
        df["Low"]
        - df["Close"].shift()
    )

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    atr = tr.rolling(period).mean()

    upperband = hl2 + (multiplier * atr)

    lowerband = hl2 - (multiplier * atr)

    st_line = pd.Series(index=df.index, dtype="float64")

    direction = pd.Series(index=df.index, dtype="int")

    st_line.iloc[0] = upperband.iloc[0]

    direction.iloc[0] = 1

    for i in range(1, len(df)):

        if df["Close"].iloc[i] > st_line.iloc[i - 1]:

            st_line.iloc[i] = lowerband.iloc[i]

            direction.iloc[i] = 1

        else:

            st_line.iloc[i] = upperband.iloc[i]

            direction.iloc[i] = -1

    return st_line, direction

# =========================
# MARKET TREND
# =========================
@st.cache_data(ttl=300)
def market_trend():

    nifty = yf.download(

        "^NSEI",

        period="5d",

        interval="15m",

        progress=False
    )

    nifty["EMA50"] = (
        nifty["Close"]
        .ewm(span=50)
        .mean()
    )

    latest = nifty.iloc[-1]

    if latest["Close"] > latest["EMA50"]:

        return "BULLISH"

    return "BEARISH"

trend = market_trend()

# =========================
# BIG MOVE ENGINE
# =========================
def big_move_engine(row, prev_row):

    score = 0

    vol_ratio = (
        row["Volume"]
        /
        (row["VOL_AVG"] + 1e-9)
    )

    # VOLUME
    if vol_ratio > 3:
        score += 35

    elif vol_ratio > 2:
        score += 25

    elif vol_ratio > 1.5:
        score += 15

    # VWAP
    if row["Close"] > row["VWAP"]:
        score += 25
    else:
        score -= 25

    # EMA
    if row["Close"] > row["EMA21"]:
        score += 20
    else:
        score -= 20

    # RSI
    if row["RSI"] > 60:
        score += 15

    elif row["RSI"] < 40:
        score -= 15

    # ATR
    if row["ATR"] > prev_row["ATR"]:
        score += 10

    # BREAKOUT
    if row["Close"] > prev_row["High"]:
        score += 10

    if row["Close"] < prev_row["Low"]:
        score -= 10

    return score, round(vol_ratio, 2)

# =========================
# MAIN ENGINE
# =========================
def engine(stock, raw, date):

    key = stock + ".NS"

    if key not in raw.columns.get_level_values(0):

        return []

    df = raw[key].dropna().copy()

    if len(df) < 60:

        return []

    # =========================
    # INDICATORS
    # =========================
    df["EMA21"] = (
        df["Close"]
        .ewm(span=21)
        .mean()
    )

    df["VWAP"] = vwap(df)

    df["RSI"] = rsi(df["Close"])

    df["VOL_AVG"] = (
        df["Volume"]
        .rolling(20)
        .mean()
    )

    tr = pd.concat([

        df["High"] - df["Low"],

        abs(
            df["High"]
            - df["Close"].shift()
        ),

        abs(
            df["Low"]
            - df["Close"].shift()
        )

    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    # =========================
    # SUPERTREND
    # =========================
    df["SUPERTREND"], df["ST_DIR"] = supertrend(df)

    # =========================
    # TIMEZONE
    # =========================
    if df.index.tz is None:

        df.index = df.index.tz_localize("UTC")

    df.index = df.index.tz_convert(IST)

    # =========================
    # DATE FILTER
    # =========================
    df = df[
        df.index.date
        ==
        pd.to_datetime(date).date()
    ]

    results = []

    # =========================
    # LOOP
    # =========================
    for i in range(1, len(df)):

        row = df.iloc[i]

        prev_row = df.iloc[i - 1]

        t = row.name.time()

        if not (

            datetime.strptime(
                "09:30",
                "%H:%M"
            ).time()

            <= t <=

            datetime.strptime(
                "14:45",
                "%H:%M"
            ).time()
        ):

            continue

        # =========================
        # SCORE
        # =========================
        big_score, vol_ratio = big_move_engine(
            row,
            prev_row
        )

        # =========================
        # SUPER BUY
        # =========================
        buy = (

            row["Close"] > row["VWAP"]

            and

            row["Close"] > row["EMA21"]

            and

            row["RSI"] > 55

            and

            row["ST_DIR"] == 1

            and

            big_score >= 60

            and

            row["Close"] > row["Open"]

            and

            vol_ratio > 1.5

            and

            trend == "BULLISH"
        )

        # =========================
        # SUPER SELL
        # =========================
        sell = (

            row["Close"] < row["VWAP"]

            and

            row["Close"] < row["EMA21"]

            and

            row["RSI"] < 45

            and

            row["ST_DIR"] == -1

            and

            big_score <= -40

            and

            row["Close"] < row["Open"]

            and

            vol_ratio > 1.5

            and

            trend == "BEARISH"
        )

        if not (buy or sell):

            continue

        signal = (
            "BUY"
            if buy
            else "SELL"
        )

        entry = row["Close"]

        atr = row["ATR"]

        if pd.isna(atr):

            continue

        # =========================
        # TARGET / SL
        # =========================
        if buy:

            sl = entry - atr * 2.2

            tgt = entry + atr * 2.5

        else:

            sl = entry + atr * 2.2

            tgt = entry - atr * 2.5

        # =========================
        # RISK REWARD
        # =========================
        rr = (
            abs(tgt - entry)
            /
            (abs(entry - sl) + 1e-9)
        )

        # =========================
        # AI CONFIDENCE
        # =========================
        ai_confidence = 0

        if row["Close"] > row["VWAP"]:
            ai_confidence += 20

        if row["Close"] > row["EMA21"]:
            ai_confidence += 20

        if row["RSI"] > 55:
            ai_confidence += 15

        if vol_ratio > 2:
            ai_confidence += 20

        if row["ST_DIR"] == 1:
            ai_confidence += 25

        ai_confidence = min(ai_confidence, 100)

        # =========================
        # HIT PROBABILITY
        # =========================
        probability = (
            ai_confidence
            +
            (vol_ratio * 5)
            +
            (rr * 10)
        )

        probability = min(probability, 95)

        # =========================
        # BACKTEST
        # =========================
        future = df.iloc[i+1:i+20]

        status = "OPEN"

        for _, f in future.iterrows():

            if buy:

                if f["High"] >= tgt:

                    status = "TARGET"

                    break

                if f["Low"] <= sl:

                    status = "SL"

                    break

            else:

                if f["Low"] <= tgt:

                    status = "TARGET"

                    break

                if f["High"] >= sl:

                    status = "SL"

                    break

        # =========================
        # ACTION
        # =========================
        if big_score >= 90:

            action = "STRONG BUY"

        elif big_score <= -90:

            action = "STRONG SELL"

        elif buy:

            action = "BUY"

        else:

            action = "SELL"

        # =========================
        # RESULTS
        # =========================
        results.append({

            "TIME":
            row.name.strftime("%H:%M"),

            "STOCK":
            stock,

            "ACTION":
            action,

            "SIGNAL":
            signal,

            "ENTRY":
            round(entry, 2),

            "SL":
            round(sl, 2),

            "TARGET":
            round(tgt, 2),

            "R:R":
            round(rr, 2),

            "RSI":
            round(row["RSI"], 2),

            "BIG_MOVE_SCORE":
            round(big_score, 2),

            "AI_CONFIDENCE":
            round(ai_confidence, 2),

            "HIT_PROBABILITY":
            round(probability, 2),

            "VOLUME_RATIO":
            round(vol_ratio, 2),

            "SUPERTREND":
            "BUY"
            if row["ST_DIR"] == 1
            else "SELL",

            "CANDLE":
            "GREEN"
            if row["Close"] > row["Open"]
            else "RED",

            "STATUS":
            status
        })

    return results

# =========================
# EXCEL
# =========================
def to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(

        output,

        engine="xlsxwriter"

    ) as writer:

        df.to_excel(

            writer,

            index=False,

            sheet_name="RESULT"
        )

        workbook = writer.book

        worksheet = writer.sheets["RESULT"]

        header_format = workbook.add_format({

            "bold": True,

            "font_color": "white",

            "bg_color": "#0A4E8A",

            "border": 1
        })

        for col_num, value in enumerate(df.columns.values):

            worksheet.write(
                0,
                col_num,
                value,
                header_format
            )

        worksheet.set_column("A:Z", 18)

    return output.getvalue()

# =========================
# UI
# =========================
tab1, tab2 = st.tabs([

    "🔥 LIVE SCANNER",

    "📊 BACKTEST"
])

# =========================
# LIVE SCANNER
# =========================
with tab1:

    st.subheader("📈 MARKET TREND")

    if trend == "BULLISH":

        st.success(f"🚀 MARKET TREND: {trend}")

    else:

        st.error(f"🔻 MARKET TREND: {trend}")

    if st.button("RUN LIVE SCAN"):

        results = []

        with ThreadPoolExecutor(
            max_workers=10
        ) as ex:

            for r in ex.map(

                lambda s:
                engine(
                    s,
                    data,
                    now.date()
                ),

                stocks
            ):

                results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            # =========================
            # BUY
            # =========================
            buy_df = df[
                df["SIGNAL"] == "BUY"
            ].sort_values(

                "AI_CONFIDENCE",

                ascending=False
            )

            # =========================
            # SELL
            # =========================
            sell_df = df[
                df["SIGNAL"] == "SELL"
            ].sort_values(

                "BIG_MOVE_SCORE"
            )

            # =========================
            # DASHBOARD
            # =========================
            c1, c2, c3 = st.columns(3)

            c1.metric(
                "🚀 TOTAL BUY",
                len(buy_df)
            )

            c2.metric(
                "🔻 TOTAL SELL",
                len(sell_df)
            )

            c3.metric(
                "📈 TOTAL SIGNALS",
                len(df)
            )

            # =========================
            # TOP BUY
            # =========================
            st.subheader("🚀 TOP BUY")

            st.dataframe(
                buy_df.head(10)
            )

            # =========================
            # TOP SELL
            # =========================
            st.subheader("🔻 TOP SELL")

            st.dataframe(
                sell_df.head(10)
            )

            # =========================
            # ALL SIGNALS
            # =========================
            st.subheader("📊 ALL SIGNALS")

            st.dataframe(df)

            # =========================
            # EXCEL
            # =========================
            st.download_button(

                "⬇️ DOWNLOAD LIVE EXCEL",

                to_excel(df),

                "NSE_AI_V60_LIVE.xlsx",

                mime=(
                    "application/"
                    "vnd.openxmlformats-"
                    "officedocument."
                    "spreadsheetml.sheet"
                )
            )

        else:

            st.warning(
                "NO LIVE SIGNALS FOUND"
            )

# =========================
# BACKTEST
# =========================
with tab2:

    d = st.date_input(

        "SELECT DATE",

        now.date() - timedelta(days=1)
    )

    if st.button("RUN BACKTEST"):

        results = []

        with ThreadPoolExecutor(
            max_workers=10
        ) as ex:

            for r in ex.map(

                lambda s:
                engine(
                    s,
                    data,
                    d
                ),

                stocks
            ):

                results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            wins = len(
                df[
                    df["STATUS"]
                    == "TARGET"
                ]
            )

            losses = len(
                df[
                    df["STATUS"]
                    == "SL"
                ]
            )

            accuracy = round(

                (
                    wins
                    /
                    (wins + losses + 1e-9)
                ) * 100,

                2
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "🎯 WINS",
                wins
            )

            c2.metric(
                "❌ LOSSES",
                losses
            )

            c3.metric(
                "📈 ACCURACY %",
                f"{accuracy}%"
            )

            st.dataframe(df)

            st.download_button(

                "⬇️ DOWNLOAD BACKTEST EXCEL",

                to_excel(df),

                "NSE_AI_V60_BACKTEST.xlsx",

                mime=(
                    "application/"
                    "vnd.openxmlformats-"
                    "officedocument."
                    "spreadsheetml.sheet"
                )
            )

        else:

            st.warning(
                "NO BACKTEST SIGNALS FOUND"
            )
