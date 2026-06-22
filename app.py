import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import requests
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

# ==========================================
# OPTIONAL XGBOOST
# ==========================================
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except:
    XGB_AVAILABLE = False

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="NSE AI PRO V11.11 Institutional Edition",
    page_icon="🚀",
    layout="wide"
)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
.main {
    background-color:#f7f9fc;
}
.stButton>button {
    width:100%;
    background:#0083ff;
    color:white;
    font-weight:bold;
}
.metric-card{
    background:white;
    padding:15px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.title("🚀 NSE AI PRO V11.11 Institutional Edition")

st.markdown("""
### Features

✅ AI Probability Engine

✅ Relative Strength Ranking

✅ BOS / CHOCH Detection

✅ CISD Early Entry

✅ VWAP Bounce Scanner

✅ RVOL Detection

✅ Supertrend

✅ ATR Target System

✅ News Momentum Scanner

✅ Streamlit Cloud Optimized
""")

# ==========================================
# SESSION STORAGE
# ==========================================
if "master_data" not in st.session_state:
    st.session_state.master_data = pd.DataFrame()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:

    st.header("⚙ Scanner Settings")

    interval = st.selectbox(
        "Interval",
        ["5m","15m","30m","1h","1d"],
        index=1
    )

    period = st.selectbox(
        "Period",
        ["5d","1mo","3mo","6mo","1y"],
        index=2
    )

    auto_refresh = st.checkbox(
        "Auto Refresh"
    )

    st.markdown("---")

    sector_dict = {

        "Banking":[
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "AXISBANK",
            "KOTAKBANK"
        ],

        "IT":[
            "TCS",
            "INFY",
            "WIPRO",
            "HCLTECH",
            "TECHM"
        ],

        "Auto":[
            "TATAMOTORS",
            "M&M",
            "MARUTI",
            "EICHERMOT",
            "HEROMOTOCO"
        ],

        "Energy":[
            "RELIANCE",
            "ONGC",
            "BPCL",
            "NTPC"
        ],

        "Pharma":[
            "SUNPHARMA",
            "CIPLA",
            "DIVISLAB",
            "DRREDDY"
        ]
    }

    sector = st.selectbox(
        "Select Sector",
        ["All NSE Stocks"] + list(sector_dict.keys())
    )

    run_scanner = st.button(
        "🚀 RUN SCANNER"
    )

# ==========================================
# NSE STOCK LIST
# ==========================================
@st.cache_data(ttl=86400)
def load_stock_list():

    try:

        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

        headers = {
            "User-Agent":"Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        df = pd.read_csv(
            io.StringIO(response.text)
        )

        return sorted(
            df["Symbol"]
            .dropna()
            .unique()
            .tolist()
        )

    except:

        return [

            "RELIANCE",
            "TCS",
            "INFY",
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "ITC",
            "LT",
            "AXISBANK",
            "TATAMOTORS",
            "BHARTIARTL",
            "MARUTI",
            "SUNPHARMA",
            "ULTRACEMCO",
            "HINDUNILVR"
        ]

stocks = load_stock_list()

# ==========================================
# MARKET DATA
# ==========================================
@st.cache_data(ttl=300)
def get_data(
    symbol,
    interval,
    period
):

    try:

        ticker = (
            symbol
            if "^" in symbol
            else f"{symbol}.NS"
        )

        df = yf.download(
            ticker,
            interval=interval,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):
            df.columns = (
                df.columns
                .get_level_values(0)
            )

        return df

    except:
        return pd.DataFrame()

# ==========================================
# NIFTY RETURN
# ==========================================
def get_nifty_return(
    interval,
    period
):

    try:

        nifty = get_data(
            "^NSEI",
            interval,
            period
        )

        if nifty.empty:
            return 0

        start = nifty["Close"].iloc[0]
        end = nifty["Close"].iloc[-1]

        return (
            (end - start)
            / start
        ) * 100

    except:
        return 0

# ==========================================
# AI TREND ENGINE
# ==========================================
def predict_trend_ai(close_series):

    if len(close_series) < 20:
        return "Neutral",0

    try:

        y = close_series.tail(20).values

        x = np.arange(
            len(y)
        )

        slope, intercept = np.polyfit(
            x,
            y,
            1
        )

        corr = np.corrcoef(
            x,
            y
        )[0,1]

        confidence = round(
            min(
                abs(corr)*100,
                99
            ),
            2
        )

        if slope > 0 and confidence > 50:
            return "UP 🚀",confidence

        elif slope < 0 and confidence > 50:
            return "DOWN 🔻",confidence

        else:
            return "SIDEWAYS",confidence

    except:

        return "Neutral",0

# ==========================================
# RELATIVE STRENGTH
# ==========================================
def calculate_relative_strength(
    df,
    nifty_return
):

    try:

        stock_return = (

            (
                df["Close"].iloc[-1]
                -
                df["Close"].iloc[0]
            )

            /

            df["Close"].iloc[0]

        ) * 100

        rs_score = round(
            stock_return# ==========================================
# EMA + RSI + MACD
# ==========================================
def add_indicators(df):

    if len(df) < 30:
        return df

    try:

        # EMA
        df["EMA20"] = df["Close"].ewm(
            span=20,
            adjust=False
        ).mean()

        df["EMA50"] = df["Close"].ewm(
            span=50,
            adjust=False
        ).mean()

        # RSI
        delta = df["Close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1/14,
            adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1/14,
            adjust=False
        ).mean()

        rs = avg_gain / avg_loss

        df["RSI"] = 100 - (
            100 / (1 + rs)
        )

        df["RSI"] = df["RSI"].fillna(50)

        # MACD
        ema12 = df["Close"].ewm(
            span=12,
            adjust=False
        ).mean()

        ema26 = df["Close"].ewm(
            span=26,
            adjust=False
        ).mean()

        df["MACD"] = ema12 - ema26

        df["MACD_SIGNAL"] = (
            df["MACD"]
            .ewm(
                span=9,
                adjust=False
            )
            .mean()
        )

        # Average Volume
        df["AVG_VOL"] = (
            df["Volume"]
            .rolling(20)
            .mean()
        )

        return df

    except:
        return df


# ==========================================
# VWAP
# ==========================================
def add_vwap(df):

    try:

        tp = (
            df["High"]
            +
            df["Low"]
            +
            df["Close"]
        ) / 3

        volume_sum = (
            df["Volume"]
            .rolling(20)
            .sum()
        )

        volume_sum = volume_sum.replace(
            0,
            np.nan
        )

        df["VWAP"] = (

            (tp * df["Volume"])
            .rolling(20)
            .sum()

            /

            volume_sum

        )

        return df

    except:
        return df


# ==========================================
# ATR
# ==========================================
def add_atr(df):

    try:

        hl = (
            df["High"]
            -
            df["Low"]
        )

        hc = abs(
            df["High"]
            -
            df["Close"].shift(1)
        )

        lc = abs(
            df["Low"]
            -
            df["Close"].shift(1)
        )

        tr = pd.concat(
            [hl, hc, lc],
            axis=1
        ).max(axis=1)

        df["ATR"] = (
            tr
            .rolling(14)
            .mean()
        )

        return df

    except:
        return df


# ==========================================
# SUPERTREND
# ==========================================
def add_supertrend(
    df,
    period=10,
    multiplier=3
):

    try:

        hl = (
            df["High"]
            +
            df["Low"]
        ) / 2

        tr = np.maximum(
            df["High"] - df["Low"],
            np.maximum(
                abs(
                    df["High"]
                    -
                    df["Close"].shift(1)
                ),
                abs(
                    df["Low"]
                    -
                    df["Close"].shift(1)
                )
            )
        )

        atr = (
            pd.Series(tr)
            .rolling(period)
            .mean()
        )

        upperband = (
            hl +
            multiplier * atr
        )

        lowerband = (
            hl -
            multiplier * atr
        )

        direction = np.zeros(len(df))

        for i in range(1, len(df)):

            if (
                df["Close"].iloc[i]
                >
                upperband.iloc[i-1]
            ):
                direction[i] = 1

            elif (
                df["Close"].iloc[i]
                <
                lowerband.iloc[i-1]
            ):
                direction[i] = -1

            else:
                direction[i] = direction[i-1]

        df["ST_DIRECTION"] = direction

        return df

    except:
        return df


# ==========================================
# BOS / CHOCH
# ==========================================
def detect_structure(df):

    try:

        df["SWING_HIGH"] = (
            df["High"]
            .rolling(10)
            .max()
            .shift(1)
        )

        df["SWING_LOW"] = (
            df["Low"]
            .rolling(10)
            .min()
            .shift(1)
        )

        last_close = (
            df["Close"]
            .iloc[-1]
        )

        last_high = (
            df["SWING_HIGH"]
            .iloc[-1]
        )

        last_low = (
            df["SWING_LOW"]
            .iloc[-1]
        )

        bullish_trend = (
            df["EMA20"].iloc[-1]
            >
            df["EMA50"].iloc[-1]
        )

        if last_close > last_high:

            if bullish_trend:
                return "BOS 📈"

            else:
                return "CHOCH 🐂"

        elif last_close < last_low:

            if bullish_trend:
                return "CHOCH 🐻"

            else:
                return "BOS 📉"

        return "RANGE"

    except:
        return "RANGE"


# ==========================================
# CISD DETECTION
# ==========================================
def detect_cisd(df):

    try:

        prev_high = (
            df["High"]
            .shift(1)
        )

        prev_low = (
            df["Low"]
            .shift(1)
        )

        bullish = (

            (df["Low"] < prev_low)

            &

            (df["Close"] > prev_high)

        )

        bearish = (

            (df["High"] > prev_high)

            &

            (df["Close"] < prev_low)

        )

        if bullish.iloc[-1]:
            return "Bullish CISD 🚀"

        if bearish.iloc[-1]:
            return "Bearish CISD 🔻"

        return "None"

    except:
        return "None"


# ==========================================
# CANDLESTICK PATTERN
# ==========================================
def get_pattern(df):

    try:

        if len(df) < 2:
            return "Normal"

        o1 = df["Open"].iloc[-2]
        c1 = df["Close"].iloc[-2]

        o2 = df["Open"].iloc[-1]
        c2 = df["Close"].iloc[-1]

        h2 = df["High"].iloc[-1]
        l2 = df["Low"].iloc[-1]

        body = abs(c2 - o2)

        rng = max(
            h2 - l2,
            0.01
        )

        if body <= rng * 0.1:
            return "Doji"

        if (
            c1 < o1
            and
            c2 > o2
            and
            o2 < c1
            and
            c2 > o1
        ):
            return "Bullish Engulfing"

        if (
            c1 > o1
            and
            c2 < o2
            and
            o2 > c1
            and
            c2 < o1
        ):
            return "Bearish Engulfing"

        return "Normal"

    except:
        return "Normal"


# ==========================================
# AI PROBABILITY ENGINE
# ==========================================
def calculate_ai_probability(
    df,
    rvol
):

    try:

        score = 0

        if (
            df["EMA20"].iloc[-1]
            >
            df["EMA50"].iloc[-1]
        ):
            score += 20

        if (
            df["RSI"].iloc[-1]
            >
            55
        ):
            score += 20

        if (
            df["MACD"].iloc[-1]
            >
            df["MACD_SIGNAL"].iloc[-1]
        ):
            score += 20

        if rvol > 1.5:
            score += 20

        if (
            df["Close"].iloc[-1]
            >
            df["VWAP"].iloc[-1]
        ):
            score += 20

        probability = min(
            score,
            100
        )

        return probability

    except:
        return 0
            -
            nifty_return,
            2
        )

        return rs_score

    except:
        return 0
# ==========================================
# STOCK PROCESSOR
# ==========================================
def process_stock(symbol, interval, period, nifty_return):

    try:

        df = get_data(
            symbol,
            interval,
            period
        )

        if df.empty or len(df) < 30:
            return None

        # Indicators
        df = add_indicators(df)
        df = add_vwap(df)
        df = add_atr(df)
        df = add_supertrend(df)

        close = float(
            df["Close"].iloc[-1]
        )

        # RVOL
        avg_vol = float(
            df["AVG_VOL"].iloc[-1]
        ) if pd.notna(
            df["AVG_VOL"].iloc[-1]
        ) else 0

        current_vol = float(
            df["Volume"].iloc[-1]
        )

        rvol = (
            current_vol / avg_vol
            if avg_vol > 0
            else 0
        )

        # Relative Strength
        rs_score = calculate_relative_strength(
            df,
            nifty_return
        )

        # Structure
        structure = detect_structure(df)

        # CISD
        cisd = detect_cisd(df)

        # Pattern
        pattern = get_pattern(df)

        # AI Trend
        ai_trend, ai_conf = predict_trend_ai(
            df["Close"]
        )

        # AI Probability
        probability = calculate_ai_probability(
            df,
            rvol
        )

        alerts = []

        # News Momentum
        try:

            prev_close = (
                df["Close"]
                .iloc[-2]
            )

            gap_pct = (
                (close - prev_close)
                /
                prev_close
            ) * 100

            if (
                abs(gap_pct) > 2
                and
                rvol > 3
            ):
                alerts.append(
                    "📰 NEWS MOMENTUM"
                )

                probability += 10

        except:
            gap_pct = 0

        # RVOL Alerts
        if rvol > 3:
            alerts.append(
                "🔥 Massive RVOL"
            )

        elif rvol > 2:
            alerts.append(
                "🔥 High RVOL"
            )

        # VWAP
        try:

            if (
                close >
                df["VWAP"].iloc[-1]
            ):
                alerts.append(
                    "💧 Above VWAP"
                )

        except:
            pass

        # Signal Logic
        if probability >= 80:
            signal = "STRONG BUY"

        elif probability >= 60:
            signal = "BUY"

        elif probability <= 20:
            signal = "STRONG SELL"

        elif probability <= 40:
            signal = "SELL"

        else:
            signal = "WAIT"

        # ATR Target
        atr = float(
            df["ATR"].iloc[-1]
        ) if pd.notna(
            df["ATR"].iloc[-1]
        ) else 0

        target = "-"
        stoploss = "-"

        if atr > 0:

            if signal in [
                "BUY",
                "STRONG BUY"
            ]:

                target = round(
                    close + (atr * 3),
                    2
                )

                stoploss = round(
                    close - (atr * 1.5),
                    2
                )

            elif signal in [
                "SELL",
                "STRONG SELL"
            ]:

                target = round(
                    close - (atr * 3),
                    2
                )

                stoploss = round(
                    close + (atr * 1.5),
                    2
                )

        return [

            symbol,

            round(close,2),

            round(probability,2),

            signal,

            round(rs_score,2),

            round(rvol,2),

            structure,

            cisd,

            pattern,

            ai_trend,

            round(ai_conf,2),

            round(gap_pct,2),

            target,

            stoploss,

            ", ".join(alerts)

        ]

    except:
        return None


# ==========================================
# MAIN SCANNER
# ==========================================
if run_scanner or auto_refresh:

    st.info(
        "⚡ Running Institutional Scanner..."
    )

    selected_stocks = (
        stocks
        if sector == "All NSE Stocks"
        else sector_dict[sector]
    )

    nifty_return = get_nifty_return(
        interval,
        period
    )

    progress = st.progress(0)

    results = []

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        futures = {

            executor.submit(
                process_stock,
                stock,
                interval,
                period,
                nifty_return
            ): stock

            for stock in selected_stocks

        }

        total = len(futures)

        for idx, future in enumerate(
            as_completed(futures)
        ):

            try:

                res = future.result()

                if res:
                    results.append(res)

            except:
                pass

            progress.progress(
                (idx + 1)
                /
                total
            )

    # Create DataFrame
    if results:

        columns = [

            "Stock",
            "LTP",
            "AI Probability",
            "Signal",
            "RS Score",
            "RVOL",
            "Structure",
            "CISD",
            "Pattern",
            "AI Trend",
            "AI Confidence",
            "Gap %",
            "Target",
            "Stoploss",
            "Alerts"

        ]

        df_res = pd.DataFrame(
            results,
            columns=columns
        )

        df_res = df_res.sort_values(
            by="AI Probability",
            ascending=False
        )

        st.session_state.master_data = df_res


# ==========================================
# DASHBOARD
# ==========================================
if not st.session_state.master_data.empty:

    df_final = (
        st.session_state.master_data
    )

    st.markdown(
        "## 🏆 Top Institutional Picks"
    )

    top_buy = df_final[
        df_final["Signal"]
        ==
        "STRONG BUY"
    ]

    if not top_buy.empty:

        cols = st.columns(4)

        for i, (_, row) in enumerate(
            top_buy.head(4).iterrows()
        ):

            with cols[i]:

                st.metric(
                    row["Stock"],
                    f"₹{row['LTP']}",
                    f"{row['AI Probability']}%"
                )

    # Statistics
    st.markdown(
        "### 📊 Scanner Summary"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "STRONG BUY",
        len(
            df_final[
                df_final["Signal"]
                ==
                "STRONG BUY"
            ]
        )
    )

    c2.metric(
        "BUY",
        len(
            df_final[
                df_final["Signal"]
                ==
                "BUY"
            ]
        )
    )

    c3.metric(
        "SELL",
        len(
            df_final[
                df_final["Signal"]
                ==
                "SELL"
            ]
        )
    )

    c4.metric(
        "STRONG SELL",
        len(
            df_final[
                df_final["Signal"]
                ==
                "STRONG SELL"
            ]
        )
    )

    # Download Excel
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        df_final.to_excel(
            writer,
            index=False,
            sheet_name="Scanner"
        )

    st.download_button(

        "📥 Download Excel",

        excel_buffer.getvalue(),

        "NSE_AI_PRO_V11_11.xlsx",

        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

    # Data Table
    st.markdown(
        "### 📋 Full Scanner Output"
    )

    st.dataframe(
        df_final,
        use_container_width=True,
        height=650
    )

    # Top Stock Chart
    st.markdown(
        "### 📈 Top Pick Chart"
    )

    try:

        top_symbol = (
            df_final
            .iloc[0]["Stock"]
        )

        chart_df = get_data(
            top_symbol,
            interval,
            period
        )

        if not chart_df.empty:

            st.line_chart(
                chart_df["Close"]
            )

    except:
        pass
