import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ==========================================
# 🚀 NSE AI V60 INSTITUTIONAL LEVEL SCANNER
# ==========================================

st.set_page_config(
    page_title="🚀 NSE AI V60 INSTITUTIONAL",
    layout="wide"
)

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V60 INSTITUTIONAL LEVEL")
st.markdown(
    f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}"
)

# ==========================================
# STOCK LIST
# ==========================================
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

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data(ttl=300)
def load_data():

    tickers = [s + ".NS" for s in stocks]

    data = yf.download(

        tickers=tickers,

        period="10d",

        interval="15m",

        group_by="ticker",

        auto_adjust=True,

        threads=True
    )

    return data

data = load_data()

# ==========================================
# MARKET TREND FILTER
# ==========================================
@st.cache_data(ttl=300)
def market_trend():

    nifty = yf.download(

        "^NSEI",

        period="5d",

        interval="15m",

        auto_adjust=True
    )

    nifty["EMA50"] = (
        nifty["Close"]
        .ewm(span=50)
        .mean()
    )

    bullish = (

        nifty["Close"].iloc[-1]

        >

        nifty["EMA50"].iloc[-1]
    )

    return bullish

market_bullish = market_trend()

# ==========================================
# RSI
# ==========================================
def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    return 100 - (100 / (1 + rs))

# ==========================================
# VWAP
# ==========================================
def vwap(df):

    tp = (
        df["High"]
        +
        df["Low"]
        +
        df["Close"]
    ) / 3

    return (

        (tp * df["Volume"]).cumsum()

        /

        (df["Volume"].cumsum() + 1e-9)
    )

# ==========================================
# BIG MOVE ENGINE
# ==========================================
def big_move_engine(row, prev_row):

    score = 0

    vol_ratio = (

        row["Volume"]

        /

        (row["VOL_AVG"] + 1e-9)
    )

    # =====================
    # VOLUME
    # =====================
    if vol_ratio > 4:
        score += 40

    elif vol_ratio > 3:
        score += 30

    elif vol_ratio > 2:
        score += 20

    # =====================
    # VWAP
    # =====================
    if row["Close"] > row["VWAP"]:
        score += 25
    else:
        score -= 25

    # =====================
    # EMA
    # =====================
    if row["Close"] > row["EMA21"]:
        score += 20
    else:
        score -= 20

    # =====================
    # RSI
    # =====================
    if row["RSI"] > 65:
        score += 20

    elif row["RSI"] < 40:
        score -= 20

    # =====================
    # ATR EXPANSION
    # =====================
    if row["ATR"] > prev_row["ATR"]:
        score += 10

    # =====================
    # BREAKOUT
    # =====================
    if row["Close"] > prev_row["High"]:
        score += 15

    if row["Close"] < prev_row["Low"]:
        score -= 15

    return score, round(vol_ratio, 2)

# ==========================================
# MAIN ENGINE
# ==========================================
def engine(stock, raw, date):

    key = stock + ".NS"

    if key not in raw.columns.get_level_values(0):
        return []

    df = raw[key].dropna().copy()

    if len(df) < 60:
        return []

    # ======================================
    # INDICATORS
    # ======================================
    df["EMA21"] = (
        df["Close"]
        .ewm(span=21)
        .mean()
    )

    df["EMA50"] = (
        df["Close"]
        .ewm(span=50)
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
            -
            df["Close"].shift()
        ),

        abs(
            df["Low"]
            -
            df["Close"].shift()
        )

    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    # ======================================
    # TIMEZONE
    # ======================================
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")

    df.index = df.index.tz_convert(IST)

    # ======================================
    # DATE FILTER
    # ======================================
    df = df[
        df.index.date
        ==
        pd.to_datetime(date).date()
    ]

    results = []

    last_signal_time = None

    # ======================================
    # LOOP
    # ======================================
    for i in range(20, len(df)):

        row = df.iloc[i]

        prev_row = df.iloc[i - 1]

        t = row.name.time()

        # ==================================
        # MARKET TIME
        # ==================================
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

        # ==================================
        # LUNCH NO TRADE
        # ==================================
        if 12 <= t.hour <= 13:
            continue

        # ==================================
        # DUPLICATE FILTER
        # ==================================
        if last_signal_time:

            diff = (
                row.name
                -
                last_signal_time
            ).seconds / 60

            if diff < 60:
                continue

        # ==================================
        # BIG MOVE
        # ==================================
        big_score, vol_ratio = (
            big_move_engine(
                row,
                prev_row
            )
        )

        # ==================================
        # BREAKOUT
        # ==================================
        breakout = (

            row["Close"]

            >

            df["High"]
            .rolling(20)
            .max()
            .iloc[i - 1]
        )

        breakdown = (

            row["Close"]

            <

            df["Low"]
            .rolling(20)
            .min()
            .iloc[i - 1]
        )

        # ==================================
        # CANDLE STRENGTH
        # ==================================
        body = abs(
            row["Close"]
            -
            row["Open"]
        )

        candle_range = (
            row["High"]
            -
            row["Low"]
        )

        body_ratio = (
            body
            /
            (candle_range + 1e-9)
        )

        # ==================================
        # BUY
        # ==================================
        buy = (

            market_bullish

            and

            row["Close"] > row["VWAP"]

            and

            row["Close"] > row["EMA21"]

            and

            row["EMA21"] > row["EMA50"]

            and

            row["RSI"] > 58

            and

            breakout

            and

            body_ratio > 0.6

            and

            big_score >= 70
        )

        # ==================================
        # SELL
        # ==================================
        sell = (

            not market_bullish

            and

            row["Close"] < row["VWAP"]

            and

            row["Close"] < row["EMA21"]

            and

            row["EMA21"] < row["EMA50"]

            and

            row["RSI"] < 42

            and

            breakdown

            and

            body_ratio > 0.6

            and

            big_score <= -50
        )

        if not (buy or sell):
            continue

        signal = (
            "BUY"
            if buy
            else
            "SELL"
        )

        entry = row["Close"]

        atr = row["ATR"]

        if pd.isna(atr):
            continue

        # ==================================
        # TARGET / SL
        # ==================================
        if buy:

            sl = entry - atr * 2.2

            tgt = entry + atr * 2.8

        else:

            sl = entry + atr * 2.2

            tgt = entry - atr * 2.8

        # ==================================
        # RISK REWARD
        # ==================================
        rr = (

            abs(tgt - entry)

            /

            (abs(entry - sl) + 1e-9)
        )

        # ==================================
        # CAPITAL MANAGEMENT
        # ==================================
        risk_per_trade = 1000

        qty = int(

            risk_per_trade

            /

            (abs(entry - sl) + 1e-9)
        )

        # ==================================
        # AI TREND SCORE
        # ==================================
        trend_score = 0

        if row["Close"] > row["EMA21"]:
            trend_score += 25

        if row["Close"] > row["VWAP"]:
            trend_score += 25

        if row["RSI"] > 60:
            trend_score += 25

        if vol_ratio > 2:
            trend_score += 25

        if trend_score >= 90:
            ai_signal = "MEGA BULLISH"

        elif trend_score >= 70:
            ai_signal = "BULLISH"

        elif trend_score <= 30:
            ai_signal = "BEARISH"

        else:
            ai_signal = "SIDEWAYS"

        # ==================================
        # MONEY FLOW
        # ==================================
        money_flow = (
            row["Close"]
            *
            row["Volume"]
        )

        # ==================================
        # PRICE MOVE %
        # ==================================
        move_pct = (

            (
                row["Close"]
                -
                prev_row["Close"]
            )

            /

            prev_row["Close"]
        ) * 100

        # ==================================
        # BACKTEST
        # ==================================
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

        # ==================================
        # ACTION
        # ==================================
        if big_score >= 95:
            action = "🔥 MEGA BUY"

        elif big_score >= 80:
            action = "🚀 STRONG BUY"

        elif big_score <= -80:
            action = "🔻 STRONG SELL"

        else:
            action = signal

        results.append({

            "TIME":
            row.name.strftime("%H:%M"),

            "STOCK":
            stock,

            "ACTION":
            action,

            "AI_SIGNAL":
            ai_signal,

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

            "QTY":
            qty,

            "RSI":
            round(row["RSI"], 2),

            "BIG_MOVE_SCORE":
            round(big_score, 2),

            "TREND_SCORE":
            trend_score,

            "VOLUME_RATIO":
            round(vol_ratio, 2),

            "BODY_RATIO":
            round(body_ratio, 2),

            "MOVE_%":
            round(move_pct, 2),

            "MONEY_FLOW":
            round(money_flow / 10000000, 2),

            "STATUS":
            status
        })

        last_signal_time = row.name

    return results

# ==========================================
# EXCEL
# ==========================================
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

        worksheet.set_column("A:Z", 20)

    return output.getvalue()

# ==========================================
# TABS
# ==========================================
tab1, tab2 = st.tabs([

    "🔥 LIVE SCANNER",

    "📊 BACKTEST"
])

# ==========================================
# LIVE SCAN
# ==========================================
with tab1:

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

            buy_df = df[
                df["SIGNAL"] == "BUY"
            ].sort_values(
                "BIG_MOVE_SCORE",
                ascending=False
            )

            sell_df = df[
                df["SIGNAL"] == "SELL"
            ].sort_values(
                "BIG_MOVE_SCORE"
            )

            # ======================
            # METRICS
            # ======================
            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "🚀 BUY SIGNALS",
                len(buy_df)
            )

            c2.metric(
                "🔻 SELL SIGNALS",
                len(sell_df)
            )

            c3.metric(
                "📈 MARKET",
                (
                    "BULLISH"
                    if market_bullish
                    else
                    "BEARISH"
                )
            )

            c4.metric(
                "🔥 TOTAL SIGNALS",
                len(df)
            )

            # ======================
            # TOP PANELS
            # ======================
            col1, col2 = st.columns(2)

            with col1:

                st.subheader("🚀 TOP BUY")

                st.dataframe(
                    buy_df.head(10),
                    use_container_width=True
                )

            with col2:

                st.subheader("🔻 TOP SELL")

                st.dataframe(
                    sell_df.head(10),
                    use_container_width=True
                )

            # ======================
            # ALL SIGNALS
            # ======================
            st.subheader("📊 ALL SIGNALS")

            st.dataframe(
                df,
                use_container_width=True
            )

            # ======================
            # DOWNLOAD
            # ======================
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

# ==========================================
# BACKTEST
# ==========================================
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

            open_trades = len(
                df[
                    df["STATUS"]
                    == "OPEN"
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

            # ======================
            # METRICS
            # ======================
            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "🎯 WINS",
                wins
            )

            c2.metric(
                "❌ LOSSES",
                losses
            )

            c3.metric(
                "📈 ACCURACY",
                f"{accuracy}%"
            )

            c4.metric(
                "🟡 OPEN",
                open_trades
            )

            st.dataframe(
                df,
                use_container_width=True
            )

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
