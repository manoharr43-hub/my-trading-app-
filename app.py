# ============================================
# 🚀 NSE AI V61 INSTITUTIONAL PRO MAX
# OLD CODE DISTURB KAKUNDA UPGRADED VERSION
# ============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="🚀 NSE AI V61 INSTITUTIONAL PRO MAX",
    layout="wide"
)

# ============================================
# TIME
# ============================================

IST = pytz.timezone("Asia/Kolkata")

now = datetime.now(IST)

# ============================================
# MARKET STATUS
# ============================================

market_open = (
    datetime.strptime("09:15", "%H:%M").time()
    <= now.time() <=
    datetime.strptime("15:30", "%H:%M").time()
)

# ============================================
# TITLE
# ============================================

st.title("🚀 NSE AI V61 INSTITUTIONAL PRO MAX")

st.markdown(
    f"### 🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}"
)

if market_open:
    st.success("🟢 MARKET LIVE")
else:
    st.error("🔴 MARKET CLOSED")

st.caption("🔄 Refresh page for latest scan")

# ============================================
# STOCK LIST
# ============================================

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

# ============================================
# LOAD DATA
# ============================================

@st.cache_data(ttl=300)

def load_data():

    tickers = [s + ".NS" for s in stocks]

    data = yf.download(

        tickers=tickers,

        period="20d",

        interval="15m",

        auto_adjust=True,

        group_by="ticker",

        threads=True,

        progress=False
    )

    return data

data = load_data()

# ============================================
# RSI
# ============================================

def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    return 100 - (100 / (1 + rs))

# ============================================
# VWAP
# ============================================

def vwap(df):

    tp = (
        df["High"] +
        df["Low"] +
        df["Close"]
    ) / 3

    return (
        (tp * df["Volume"]).cumsum()
        /
        (df["Volume"].cumsum() + 1e-9)
    )

# ============================================
# SUPERTREND
# ============================================

def supertrend(df, period=10, multiplier=3):

    hl2 = (df["High"] + df["Low"]) / 2

    tr1 = df["High"] - df["Low"]

    tr2 = abs(df["High"] - df["Close"].shift())

    tr3 = abs(df["Low"] - df["Close"].shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st_line = pd.Series(index=df.index, dtype='float64')
    trend = pd.Series(index=df.index, dtype='bool')

    for i in range(len(df)):

        if i == 0:

            st_line.iloc[i] = upperband.iloc[i]
            trend.iloc[i] = True

            continue

        if df["Close"].iloc[i] > st_line.iloc[i-1]:

            trend.iloc[i] = True
            st_line.iloc[i] = lowerband.iloc[i]

        else:

            trend.iloc[i] = False
            st_line.iloc[i] = upperband.iloc[i]

    return trend

# ============================================
# BIG MOVE ENGINE
# ============================================

def big_move_engine(row, prev_row):

    score = 0

    vol_ratio = (
        row["Volume"]
        /
        (row["VOL_AVG"] + 1e-9)
    )

    # ============================================
    # VOLUME
    # ============================================

    if vol_ratio > 3:

        score += 35

    elif vol_ratio > 2:

        score += 25

    elif vol_ratio > 1.5:

        score += 15

    # ============================================
    # VWAP DISTANCE
    # ============================================

    vwap_distance = (
        (
            row["Close"] - row["VWAP"]
        )
        /
        row["VWAP"]
    ) * 100

    if vwap_distance > 1:

        score += 30

    elif vwap_distance > 0.5:

        score += 20

    elif vwap_distance < -1:

        score -= 30

    elif vwap_distance < -0.5:

        score -= 20

    # ============================================
    # VWAP TREND
    # ============================================

    if row["VWAP"] > prev_row["VWAP"]:

        score += 10

    else:

        score -= 10

    # ============================================
    # EMA ALIGNMENT
    # ============================================

    if (
        row["EMA9"] >
        row["EMA21"] >
        row["EMA50"]
    ):

        score += 25

    elif (
        row["EMA9"] <
        row["EMA21"] <
        row["EMA50"]
    ):

        score -= 25

    # ============================================
    # RSI
    # ============================================

    if row["RSI"] > 70:

        score += 25

    elif row["RSI"] > 60:

        score += 15

    elif row["RSI"] < 30:

        score -= 25

    elif row["RSI"] < 40:

        score -= 15

    # ============================================
    # BREAKOUT
    # ============================================

    if row["Close"] > prev_row["High"]:

        score += 20

    if row["Close"] < prev_row["Low"]:

        score -= 20

    # ============================================
    # SUPERTREND
    # ============================================

    if row["SUPERTREND"]:

        score += 15

    else:

        score -= 15

    return score, round(vol_ratio, 2)

# ============================================
# ENGINE
# ============================================

def engine(stock, raw, date):

    key = stock + ".NS"

    try:

        if key not in raw.columns.get_level_values(0):

            return []

        df = raw[key].dropna().copy()

    except:

        return []

    if len(df) < 100:

        return []

    # ============================================
    # INDICATORS
    # ============================================

    df["EMA9"] = (
        df["Close"]
        .ewm(span=9)
        .mean()
    )

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
        .rolling(20, min_periods=1)
        .mean()
    )

    tr = pd.concat([

        df["High"] - df["Low"],

        abs(
            df["High"] -
            df["Close"].shift()
        ),

        abs(
            df["Low"] -
            df["Close"].shift()
        )

    ], axis=1).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    df["SUPERTREND"] = supertrend(df)

    # ============================================
    # TIMEZONE
    # ============================================

    if df.index.tz is None:

        df.index = df.index.tz_localize("UTC")

    df.index = df.index.tz_convert(IST)

    # ============================================
    # DATE FILTER
    # ============================================

    df = df[
        df.index.date
        ==
        pd.to_datetime(date).date()
    ]

    results = []

    # ============================================
    # LOOP
    # ============================================

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

        # ============================================
        # VWAP CROSS
        # ============================================

        vwap_cross_up = (

            prev_row["Close"] < prev_row["VWAP"]

            and

            row["Close"] > row["VWAP"]
        )

        vwap_cross_down = (

            prev_row["Close"] > prev_row["VWAP"]

            and

            row["Close"] < row["VWAP"]
        )

        # ============================================
        # SCORE
        # ============================================

        big_score, vol_ratio = big_move_engine(
            row,
            prev_row
        )

        # ============================================
        # BUY
        # ============================================

        buy = (

            row["Close"] > row["EMA9"]

            and

            row["EMA9"] > row["EMA21"]

            and

            row["EMA21"] > row["EMA50"]

            and

            row["Close"] > row["VWAP"]

            and

            row["RSI"] > 60

            and

            row["SUPERTREND"] == True

            and

            vol_ratio > 1.5

            and

            vwap_cross_up

            and

            big_score >= 55
        )

        # ============================================
        # SELL
        # ============================================

        sell = (

            row["Close"] < row["EMA9"]

            and

            row["EMA9"] < row["EMA21"]

            and

            row["EMA21"] < row["EMA50"]

            and

            row["Close"] < row["VWAP"]

            and

            row["RSI"] < 40

            and

            row["SUPERTREND"] == False

            and

            vol_ratio > 1.5

            and

            vwap_cross_down

            and

            big_score <= -55
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

        # ============================================
        # SL / TARGET
        # ============================================

        if buy:

            sl = entry - atr * 2

            tgt = entry + atr * 3

        else:

            sl = entry + atr * 2

            tgt = entry - atr * 3

        rr = (
            abs(tgt - entry)
            /
            (abs(entry - sl) + 1e-9)
        )

        # ============================================
        # BACKTEST
        # ============================================

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

        # ============================================
        # ACTION
        # ============================================

        if big_score >= 90:

            action = "STRONG BUY"

        elif big_score <= -90:

            action = "STRONG SELL"

        elif buy:

            action = "BUY"

        else:

            action = "SELL"

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

            "VOLUME_RATIO":
            round(vol_ratio, 2),

            "STATUS":
            status
        })

    return results
