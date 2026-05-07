import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io
import time

# =========================================================
# 🚀 NSE AI QUANT PRO V10.0 SUPREME ULTRA
# =========================================================

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V10.0 SUPREME ULTRA",
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

.main-title{
    text-align:center;
    font-size:44px;
    font-weight:bold;
    color:#22c55e;
}

.sub-title{
    text-align:center;
    font-size:18px;
    color:#cbd5e1;
    margin-bottom:25px;
}

.nifty-box{
    padding:20px;
    border-radius:14px;
    text-align:center;
    font-size:24px;
    font-weight:bold;
    margin-bottom:20px;
}

.pos-trend{
    background:#052e16;
    color:#22c55e;
    border:2px solid #22c55e;
}

.neg-trend{
    background:#450a0a;
    color:#f87171;
    border:2px solid #f87171;
}

.metric-card{
    background:#111827;
    padding:18px;
    border-radius:12px;
    text-align:center;
    border:1px solid #374151;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">🚀 NSE AI QUANT PRO V10.0 SUPREME ULTRA</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>',
    unsafe_allow_html=True
)

# =========================================================
# REFRESH BUTTON
# =========================================================
col_refresh1, col_refresh2 = st.columns([1, 5])

with col_refresh1:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","ADANIENT","ADANIPORTS","AXISBANK",
    "BAJFINANCE","BHARTIARTL","BPCL","CIPLA",
    "HDFCBANK","ICICIBANK","INFY","ITC","LT",
    "M&M","RELIANCE","SBIN","TCS","TATAMOTORS",
    "TITAN","WIPRO","ZOMATO","HCLTECH",
    "POWERGRID","SUNPHARMA","MARUTI",
    "TATASTEEL","ONGC","NTPC","JSWSTEEL",
    "KOTAKBANK","ULTRACEMCO","TECHM",
    "INDUSINDBK","HINDALCO","COALINDIA"
]

# =========================================================
# INDICATORS ENGINE
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty or len(df) < 30:
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
        (
            df.groupby('DATE_ONLY')['Volume'].cumsum()
            + 1e-9
        )
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
# FETCH DATA SAFE
# =========================================================
@st.cache_data(ttl=60)
def fetch_data_secure():

    try:

        tickers = [s + ".NS" for s in stocks]

        tickers.append("^NSEI")

        data_15m = yf.download(
            tickers=tickers,
            period="7d",
            interval="15m",
            auto_adjust=True,
            progress=False,
            threads=True,
            timeout=20,
            group_by="ticker"
        )

        time.sleep(2)

        data_1h = yf.download(
            tickers="^NSEI",
            period="7d",
            interval="1h",
            auto_adjust=True,
            progress=False,
            threads=True,
            timeout=20
        )

        return data_15m, data_1h

    except:

        return None, None

# =========================================================
# SCAN ENGINE
# =========================================================
def scan_stock(stock, data_15m, nifty_15m, market_trend):

    try:

        ticker = stock + ".NS"

        if ticker not in data_15m:
            return []

        raw = data_15m[ticker].dropna()

        df = add_indicators(raw)

        if df.empty:
            return []

        nifty_sync = nifty_15m.reindex(df.index).ffill()

        results = []

        today_date = now.date()

        scan_df = df[df.index.date == today_date]

        for i in range(1, len(scan_df)):

            idx = df.index.get_loc(scan_df.index[i])

            if idx < 20:
                continue

            row = df.iloc[idx]

            prev = df.iloc[idx - 1]

            n_row = nifty_sync.iloc[idx]

            # EMA9 VWAP CROSS
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

            # BUY SIGNAL
            buy_signal = (

                market_trend == "POSITIVE"

                and

                n_row['Close'] > n_row['EMA20']

                and

                cross_up

                and

                row['RSI'] > 55

                and

                row['RVOL'] > 1.3

                and

                row['MACD'] > row['MACD_SIGNAL']

                and

                row['Close'] > row['EMA20']
            )

            # SELL SIGNAL
            sell_signal = (

                market_trend == "NEGATIVE"

                and

                n_row['Close'] < n_row['EMA20']

                and

                cross_down

                and

                row['RSI'] < 45

                and

                row['RVOL'] > 1.3

                and

                row['MACD'] < row['MACD_SIGNAL']

                and

                row['Close'] < row['EMA20']
            )

            # AI SCORE
            ai_score = min(
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

            # BUY ENTRY
            if buy_signal:

                results.append({

                    "TIME": row.name.strftime('%H:%M'),

                    "STOCK": stock,

                    "SIGNAL": "BUY",

                    "PRICE": round(row['Close'], 2),

                    "RSI": round(row['RSI'], 2),

                    "RVOL": round(row['RVOL'], 2),

                    "AI_SCORE": ai_score
                })

            # SELL ENTRY
            if sell_signal:

                results.append({

                    "TIME": row.name.strftime('%H:%M'),

                    "STOCK": stock,

                    "SIGNAL": "SELL",

                    "PRICE": round(row['Close'], 2),

                    "RSI": round(row['RSI'], 2),

                    "RVOL": round(row['RVOL'], 2),

                    "AI_SCORE": ai_score
                })

        return results

    except:

        return []

# =========================================================
# LOAD DATA
# =========================================================
d15m, d1h = fetch_data_secure()

market_trend = "UNKNOWN"

nifty_15m = pd.DataFrame()

# =========================================================
# SAFE MARKET TREND
# =========================================================
if (
    d1h is not None
    and
    not d1h.empty
    and
    d15m is not None
):

    try:

        n_last_1h = d1h['Close'].iloc[-1]

        n_ema_1h = d1h['Close'].ewm(
            span=20,
            adjust=False
        ).mean().iloc[-1]

        market_trend = (
            "POSITIVE"
            if n_last_1h > n_ema_1h
            else "NEGATIVE"
        )

        if "^NSEI" in d15m:

            n_raw = d15m["^NSEI"].dropna()

        else:

            n_raw = pd.DataFrame()

        if not n_raw.empty:

            nifty_15m = add_indicators(n_raw)

            box_class = (
                "pos-trend"
                if market_trend == "POSITIVE"
                else "neg-trend"
            )

            st.markdown(
                f'''
                <div class="nifty-box {box_class}">
                📈 NIFTY 50 TREND : {market_trend}
                </div>
                ''',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "⚠️ NSEI Data Not Loaded"
            )

    except Exception as e:

        st.error(
            f"⚠️ Data Error : {e}"
        )

else:

    st.error(
        "⚠️ Yahoo Finance Connection Failed"
    )

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔍 LIVE TRACKER",
    "📊 REAL BACKTEST"
])

# =========================================================
# LIVE TRACKER
# =========================================================
with tab1:

    if st.button("🚀 START SCAN"):

        if market_trend == "UNKNOWN":

            st.error(
                "Cannot scan : Data not available"
            )

        else:

            with st.spinner("Scanning Stocks..."):

                with ThreadPoolExecutor(max_workers=20) as executor:

                    all_results = list(
                        executor.map(
                            lambda s: scan_stock(
                                s,
                                d15m,
                                nifty_15m,
                                market_trend
                            ),
                            stocks
                        )
                    )

                flat_results = [

                    item

                    for sublist in all_results

                    for item in sublist
                ]

                if len(flat_results) > 0:

                    df_live = pd.DataFrame(flat_results)

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
                        df_live[
                            df_live['SIGNAL'] == "BUY"
                        ]
                    )

                    sell_count = len(
                        df_live[
                            df_live['SIGNAL'] == "SELL"
                        ]
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

                    st.dataframe(
                        df_live,
                        use_container_width=True
                    )

                    # DOWNLOAD
                    excel_buffer = io.BytesIO()

                    with pd.ExcelWriter(
                        excel_buffer,
                        engine='xlsxwriter'
                    ) as writer:

                        df_live.to_excel(
                            writer,
                            index=False,
                            sheet_name='Signals'
                        )

                    st.download_button(
                        "📥 DOWNLOAD SIGNALS",
                        excel_buffer.getvalue(),
                        file_name="NSE_AI_SIGNALS.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                else:

                    st.warning(
                        "❌ No Strong Signals Found"
                    )

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    if st.button("📊 RUN BACKTEST"):

        if market_trend == "UNKNOWN":

            st.error(
                "Cannot run backtest : No data"
            )

        else:

            bt_results = []

            with st.spinner("Running Backtest..."):

                for stock in stocks:

                    try:

                        ticker = stock + ".NS"

                        if ticker not in d15m:
                            continue

                        raw = d15m[ticker].dropna()

                        df = add_indicators(raw)

                        if df.empty:
                            continue

                        nifty_sync = nifty_15m.reindex(df.index).ffill()

                        for i in range(25, len(df)-10):

                            row = df.iloc[i]

                            prev = df.iloc[i - 1]

                            n_row = nifty_sync.iloc[i]

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

                            buy_signal = (

                                market_trend == "POSITIVE"

                                and

                                n_row['Close'] > n_row['EMA20']

                                and

                                cross_up

                                and

                                row['RSI'] > 55

                                and

                                row['MACD'] > row['MACD_SIGNAL']
                            )

                            sell_signal = (

                                market_trend == "NEGATIVE"

                                and

                                n_row['Close'] < n_row['EMA20']

                                and

                                cross_down

                                and

                                row['RSI'] < 45

                                and

                                row['MACD'] < row['MACD_SIGNAL']
                            )

                            if buy_signal or sell_signal:

                                signal = (
                                    "BUY"
                                    if buy_signal
                                    else "SELL"
                                )

                                entry = row['Close']

                                atr = row['ATR']

                                if signal == "BUY":

                                    sl = entry - (atr * 1.5)

                                    target = entry + (atr * 2.5)

                                else:

                                    sl = entry + (atr * 1.5)

                                    target = entry - (atr * 2.5)

                                result = "OPEN"

                                for j in range(i+1, min(i+10, len(df))):

                                    nxt = df.iloc[j]

                                    if signal == "BUY":

                                        if nxt['Low'] <= sl:

                                            result = "LOSS"

                                            break

                                        if nxt['High'] >= target:

                                            result = "PROFIT"

                                            break

                                    else:

                                        if nxt['High'] >= sl:

                                            result = "LOSS"

                                            break

                                        if nxt['Low'] <= target:

                                            result = "PROFIT"

                                            break

                                bt_results.append({

                                    "STOCK": stock,

                                    "SIGNAL": signal,

                                    "ENTRY": round(entry, 2),

                                    "SL": round(sl, 2),

                                    "TARGET": round(target, 2),

                                    "RESULT": result
                                })

                    except:
                        continue

                if len(bt_results) > 0:

                    df_bt = pd.DataFrame(bt_results)

                    wins = len(
                        df_bt[
                            df_bt['RESULT'] == "PROFIT"
                        ]
                    )

                    losses = len(
                        df_bt[
                            df_bt['RESULT'] == "LOSS"
                        ]
                    )

                    total = wins + losses

                    accuracy = round(
                        (wins / total) * 100,
                        2
                    ) if total > 0 else 0

                    b1, b2, b3, b4 = st.columns(4)

                    b1.metric(
                        "TOTAL",
                        total
                    )

                    b2.metric(
                        "PROFIT",
                        wins
                    )

                    b3.metric(
                        "LOSS",
                        losses
                    )

                    b4.metric(
                        "WIN RATE",
                        f"{accuracy}%"
                    )

                    st.dataframe(
                        df_bt,
