import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# 🚀 NSE AI QUANT PRO V8.0 ULTIMATE
# EMA9 VWAP CROSS + MACD + RSI + RVOL + REAL BACKTEST
# =========================================================

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V8.0 ULTIMATE",
    layout="wide"
)

# =========================================================
# TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>

.main-title {
    text-align:center;
    font-size:40px;
    font-weight:bold;
    color:#22c55e;
    margin-bottom:10px;
}

.sub-title {
    text-align:center;
    font-size:18px;
    color:#cbd5e1;
    margin-bottom:30px;
}

.trend-box {
    padding:20px;
    border-radius:12px;
    text-align:center;
    font-size:28px;
    font-weight:bold;
    margin-bottom:20px;
}

.bull {
    background:#052e16;
    color:#22c55e;
    border:2px solid #22c55e;
}

.bear {
    background:#450a0a;
    color:#f87171;
    border:2px solid #f87171;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">🚀 NSE AI QUANT PRO V8.0 ULTIMATE</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>',
    unsafe_allow_html=True
)

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENT","ADANIPORTS",
    "APOLLOHOSP","ASHOKLEY","ASIANPAINT","AXISBANK",
    "BAJFINANCE","BAJAJFINSV","BANKBARODA","BEL",
    "BHARTIARTL","BHEL","BPCL","CANBK","CIPLA",
    "COALINDIA","DIXON","DLF","DRREDDY","EICHERMOT",
    "FEDERALBNK","GAIL","GRASIM","HAL","HAVELLS",
    "HCLTECH","HDFCBANK","HDFCLIFE","HINDALCO",
    "ICICIBANK","IDFCFIRSTB","INDUSINDBK","INFY",
    "IOC","IRCTC","ITC","JINDALSTEL","JSWSTEEL",
    "KOTAKBANK","LT","LTIM","M&M","MARUTI",
    "NTPC","ONGC","PFC","PNB","POWERGRID",
    "RECLTD","RELIANCE","SBIN","SUNPHARMA",
    "TATAMOTORS","TATASTEEL","TCS","TECHM",
    "TITAN","ULTRACEMCO","WIPRO","YESBANK",
    "ZOMATO"
]

# =========================================================
# INDICATORS
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty or len(df) < 50:
        return pd.DataFrame()

    # DATE
    df['DATE_ONLY'] = df.index.date

    # EMA
    df['EMA9'] = df['Close'].ewm(
        span=9,
        adjust=False
    ).mean()

    df['EMA20'] = df['Close'].ewm(
        span=20,
        adjust=False
    ).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby('DATE_ONLY')['PV'].cumsum()
        /
        df.groupby('DATE_ONLY')['Volume'].cumsum()
    )

    # RSI
    delta = df['Close'].diff()

    gain = (
        delta.where(delta > 0, 0)
    ).rolling(14).mean()

    loss = (
        -delta.where(delta < 0, 0)
    ).rolling(14).mean()

    rs = gain / (loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()

    df['RVOL'] = (
        df['Volume']
        /
        (df['VOLAVG'] + 1e-9)
    )

    # ATR
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    # MACD
    ema12 = df['Close'].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = df['Close'].ewm(
        span=26,
        adjust=False
    ).mean()

    df['MACD'] = ema12 - ema26

    df['MACD_SIGNAL'] = df['MACD'].ewm(
        span=9,
        adjust=False
    ).mean()

    return df

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=60)
def fetch_data():

    tickers = [s + ".NS" for s in stocks]

    tickers.append("^NSEI")

    d15 = yf.download(
        tickers,
        period="10d",
        interval="15m",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="ticker"
    )

    d1h = yf.download(
        "^NSEI",
        period="10d",
        interval="1h",
        auto_adjust=True,
        progress=False
    )

    return d15, d1h

# =========================================================
# SIGNAL ENGINE
# =========================================================
def scan_stock(stock, d15, nifty_15m, nifty_trend, backtest=False):

    try:

        ticker = stock + ".NS"

        if ticker not in d15:
            return []

        raw = d15[ticker].dropna()

        df = add_indicators(raw)

        if df.empty:
            return []

        nifty_sync = nifty_15m.reindex(df.index).ffill()

        results = []

        # =================================================
        # ONLY LATEST DAY
        # =================================================
        today = now.date()

        if backtest:
            scan_df = df
        else:
            scan_df = df[df.index.date == today]

        # =================================================
        # LOOP
        # =================================================
        for idx in range(1, len(scan_df)):

            row_index = df.index.get_loc(scan_df.index[idx])

            if row_index < 30:
                continue

            row = df.iloc[row_index]
            prev = df.iloc[row_index - 1]

            n_row = nifty_sync.iloc[row_index]

            # =============================================
            # EMA9 VWAP CROSS
            # =============================================
            cross_up = (
                prev['EMA9'] < prev['VWAP']
                and
                row['EMA9'] > row['VWAP']
            )

            cross_down = (
                prev['EMA9'] > prev['VWAP']
                and
                row['EMA9'] < row['VWAP']
            )

            # =============================================
            # MACD
            # =============================================
            macd_bullish = (
                row['MACD'] > row['MACD_SIGNAL']
            )

            macd_bearish = (
                row['MACD'] < row['MACD_SIGNAL']
            )

            # =============================================
            # AI SCORE
            # =============================================
            score = min(
                round(
                    (
                        row['RSI']
                        +
                        (row['RVOL'] * 20)
                    ) / 2,
                    2
                ),
                100
            )

            # =============================================
            # BUY
            # =============================================
            buy_signal = (

                nifty_trend == "BULLISH"

                and

                n_row['Close'] > n_row['EMA20']

                and

                cross_up

                and

                row['RSI'] > 55

                and

                row['RVOL'] > 1.5

                and

                row['Close'] > row['EMA20']

                and

                macd_bullish
            )

            # =============================================
            # SELL
            # =============================================
            sell_signal = (

                nifty_trend == "BEARISH"

                and

                n_row['Close'] < n_row['EMA20']

                and

                cross_down

                and

                row['RSI'] < 45

                and

                row['RVOL'] > 1.5

                and

                row['Close'] < row['EMA20']

                and

                macd_bearish
            )

            # =============================================
            # SIGNAL RETURN
            # =============================================
            if buy_signal:

                results.append({

                    "DATE": row.name.strftime('%d-%b'),

                    "TIME": row.name.strftime('%H:%M'),

                    "STOCK": stock,

                    "SIGNAL": "BUY",

                    "PRICE": round(row['Close'], 2),

                    "RSI": round(row['RSI'], 2),

                    "RVOL": round(row['RVOL'], 2),

                    "AI_SCORE": score,

                    "ATR": round(row['ATR'], 2)
                })

            if sell_signal:

                results.append({

                    "DATE": row.name.strftime('%d-%b'),

                    "TIME": row.name.strftime('%H:%M'),

                    "STOCK": stock,

                    "SIGNAL": "SELL",

                    "PRICE": round(row['Close'], 2),

                    "RSI": round(row['RSI'], 2),

                    "RVOL": round(row['RVOL'], 2),

                    "AI_SCORE": score,

                    "ATR": round(row['ATR'], 2)
                })

        return results

    except:
        return []

# =========================================================
# LOAD DATA
# =========================================================
d15, d1h = fetch_data()

# =========================================================
# NIFTY DATA
# =========================================================
nifty_15m = add_indicators(
    d15["^NSEI"].dropna()
)

nifty_1h_ema = d1h['Close'].ewm(
    span=20,
    adjust=False
).mean()

# =========================================================
# MARKET TREND
# =========================================================
if d1h['Close'].iloc[-1] > nifty_1h_ema.iloc[-1]:

    nifty_trend = "BULLISH"

    st.markdown(
        '<div class="trend-box bull">📈 NIFTY 1H TREND : BULLISH</div>',
        unsafe_allow_html=True
    )

else:

    nifty_trend = "BEARISH"

    st.markdown(
        '<div class="trend-box bear">📉 NIFTY 1H TREND : BEARISH</div>',
        unsafe_allow_html=True
    )

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔍 LIVE SCANNER",
    "📊 ADVANCED BACKTEST"
])

# =========================================================
# LIVE SCANNER
# =========================================================
with tab1:

    if st.button("🚀 START LIVE SCAN"):

        with st.spinner("Scanning NSE Stocks..."):

            with ThreadPoolExecutor(
                max_workers=30
            ) as executor:

                output = list(
                    executor.map(
                        lambda s: scan_stock(
                            s,
                            d15,
                            nifty_15m,
                            nifty_trend
                        ),
                        stocks
                    )
                )

            flat = [
                item
                for sublist in output
                for item in sublist
            ]

            if len(flat) > 0:

                df_live = pd.DataFrame(flat)

                # REMOVE DUPLICATES
                df_live = df_live.drop_duplicates(
                    subset=["STOCK", "SIGNAL"],
                    keep="last"
                )

                # SORT
                df_live = df_live.sort_values(
                    by="AI_SCORE",
                    ascending=False
                )

                # METRICS
                buy_count = len(
                    df_live[df_live['SIGNAL'] == "BUY"]
                )

                sell_count = len(
                    df_live[df_live['SIGNAL'] == "SELL"]
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "TOTAL SIGNALS",
                    len(df_live)
                )

                c2.metric(
                    "BUY SIGNALS",
                    buy_count
                )

                c3.metric(
                    "SELL SIGNALS",
                    sell_count
                )

                # TABLE
                st.dataframe(
                    df_live.drop(columns=['DATE']),
                    use_container_width=True
                )

                # EXCEL
                excel_out = io.BytesIO()

                with pd.ExcelWriter(
                    excel_out,
                    engine='xlsxwriter'
                ) as writer:

                    df_live.to_excel(
                        writer,
                        index=False,
                        sheet_name='Signals'
                    )

                st.download_button(
                    "📥 DOWNLOAD SIGNALS",
                    excel_out.getvalue(),
                    file_name="NSE_AI_SIGNALS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:

                st.warning(
                    "❌ No Strong Signals Found"
                )

# =========================================================
# ADVANCED BACKTEST
# =========================================================
with tab2:

    if st.button("📊 RUN ADVANCED BACKTEST"):

        with st.spinner("Running Backtest..."):

            with ThreadPoolExecutor(
                max_workers=30
            ) as executor:

                bt_output = list(
                    executor.map(
                        lambda s: scan_stock(
                            s,
                            d15,
                            nifty_15m,
                            nifty_trend,
                            backtest=True
                        ),
                        stocks
                    )
                )

            flat_bt = [
                item
                for sublist in bt_output
                for item in sublist
            ]

            if len(flat_bt) > 0:

                df_bt = pd.DataFrame(flat_bt)

                backtest_results = []

                # =============================================
                # REAL BACKTEST
                # =============================================
                for _, row in df_bt.iterrows():

                    signal = row['SIGNAL']

                    entry = row['PRICE']

                    atr = row['ATR']

                    if signal == "BUY":

                        sl = entry - (atr * 1.5)
                        target = entry + (atr * 2.5)

                    else:

                        sl = entry + (atr * 1.5)
                        target = entry - (atr * 2.5)

                    rr = round(
                        abs(target - entry)
                        /
                        abs(entry
