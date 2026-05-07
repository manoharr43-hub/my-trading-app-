# =========================================================
# 🚀 NSE AI QUANT PRO V12.0 ULTRA FINAL
# TODAY SCANNER + 5 DAY BACKTEST + EXCEL DOWNLOAD
# =========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V12.0",
    layout="wide"
)

# =========================================================
# TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# UI STYLE
# =========================================================
st.markdown("""
<style>

.main-title{
    text-align:center;
    font-size:42px;
    font-weight:bold;
    color:#22c55e;
}

.sub-title{
    text-align:center;
    font-size:18px;
    color:#cbd5e1;
    margin-bottom:20px;
}

.market-box{
    padding:20px;
    border-radius:12px;
    text-align:center;
    font-size:24px;
    font-weight:bold;
    margin-bottom:20px;
}

.bull{
    background:#052e16;
    color:#22c55e;
    border:2px solid #22c55e;
}

.bear{
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
    '<div class="main-title">🚀 NSE AI QUANT PRO V12.0 ULTRA</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>',
    unsafe_allow_html=True
)

# =========================================================
# REFRESH
# =========================================================
if st.button("🔄 REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

# =========================================================
# STOCK LIST
# =========================================================
stocks = [
    "ABB","ACC","ADANIENT","ADANIPORTS",
    "AXISBANK","BAJFINANCE","BHARTIARTL",
    "BPCL","CIPLA","HDFCBANK","ICICIBANK",
    "INFY","ITC","LT","M&M","RELIANCE",
    "SBIN","TCS","TATAMOTORS","TITAN",
    "WIPRO","ZOMATO","HCLTECH",
    "POWERGRID","SUNPHARMA","MARUTI",
    "TATASTEEL","ONGC","NTPC",
    "JSWSTEEL","KOTAKBANK","TECHM"
]

# =========================================================
# INDICATORS
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty or len(df) < 30:
        return pd.DataFrame()

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

    # ATR
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    return df

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=60)
def fetch_data():

    try:

        tickers = [s + ".NS" for s in stocks]
        tickers.append("^NSEI")

        data_15m = yf.download(
            tickers=tickers,
            period="7d",
            interval="15m",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True
        )

        data_1h = yf.download(
            "^NSEI",
            period="7d",
            interval="1h",
            auto_adjust=True,
            progress=False
        )

        return data_15m, data_1h

    except:
        return None, None

# =========================================================
# LOAD DATA
# =========================================================
d15m, d1h = fetch_data()

market_trend = "UNKNOWN"

nifty_15m = pd.DataFrame()

# =========================================================
# MARKET TREND
# =========================================================
if d1h is not None and not d1h.empty:

    try:

        close_series = d1h['Close']

        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]

        n_last = float(close_series.iloc[-1])

        n_ema = float(
            close_series.ewm(
                span=20,
                adjust=False
            ).mean().iloc[-1]
        )

        market_trend = (
            "POSITIVE"
            if n_last > n_ema
            else "NEGATIVE"
        )

        nifty_raw = d15m["^NSEI"].dropna()

        nifty_15m = add_indicators(nifty_raw)

        box_class = (
            "bull"
            if market_trend == "POSITIVE"
            else "bear"
        )

        st.markdown(
            f'''
            <div class="market-box {box_class}">
            📈 MARKET TREND : {market_trend}
            </div>
            ''',
            unsafe_allow_html=True
        )

    except Exception as e:

        st.error(f"Trend Error : {e}")

# =========================================================
# SIGNAL ENGINE
# =========================================================
def scan_stock(stock, is_backtest=False):

    try:

        ticker = stock + ".NS"

        if ticker not in d15m:
            return []

        raw = d15m[ticker].dropna()

        df = add_indicators(raw)

        if df.empty:
            return []

        nifty_sync = nifty_15m.reindex(df.index).ffill()

        results = []

        # TODAY FILTER
        if is_backtest:

            scan_df = df.copy()

        else:

            scan_df = df[
                (
                    df.index.time >= pd.to_datetime("09:15").time()
                )
                &
                (
                    df.index.time <= pd.to_datetime("15:30").time()
                )
            ]

            scan_df = scan_df[
                scan_df.index.date == now.date()
            ]

        for i in range(20, len(scan_df)):

            idx = df.index.get_loc(scan_df.index[i])

            row = df.iloc[idx]
            prev = df.iloc[idx - 1]

            n_row = nifty_sync.iloc[idx]

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

                and

                row['RVOL'] > 1.2
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

                and

                row['RVOL'] > 1.2
            )

            if buy_signal or sell_signal:

                signal = (
                    "BUY"
                    if buy_signal
                    else "SELL"
                )

                results.append({

                    "DATE": row.name.strftime("%d-%b"),

                    "TIME": row.name.strftime("%H:%M"),

                    "STOCK": stock,

                    "SIGNAL": signal,

                    "PRICE": round(row['Close'], 2),

                    "RSI": round(row['RSI'], 2),

                    "RVOL": round(row['RVOL'], 2)
                })

        return results

    except:
        return []

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔍 TODAY SCANNER",
    "📊 5 DAY BACKTEST"
])

# =========================================================
# TODAY SCANNER
# =========================================================
with tab1:

    if st.button("🚀 RUN TODAY SCANNER"):

        with st.spinner("Scanning Today Signals..."):

            with ThreadPoolExecutor(max_workers=20) as executor:

                all_results = list(
                    executor.map(
                        scan_stock,
                        stocks
                    )
                )

            flat = [
                item
                for sublist in all_results
                for item in sublist
            ]

            if len(flat) > 0:

                df_live = pd.DataFrame(flat)

                df_live = df_live.sort_values(
                    by="TIME",
                    ascending=False
                )

                st.success(
                    f"TOTAL SIGNALS : {len(df_live)}"
                )

                st.dataframe(
                    df_live,
                    use_container_width=True
                )

                # EXCEL
                excel_buffer = io.BytesIO()

                with pd.ExcelWriter(
                    excel_buffer,
                    engine='xlsxwriter'
                ) as writer:

                    df_live.to_excel(
                        writer,
                        index=False,
                        sheet_name='Today Signals'
                    )

                st.download_button(
                    "📥 DOWNLOAD TODAY EXCEL",
                    excel_buffer.getvalue(),
                    file_name="TODAY_SIGNALS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:

                st.warning("No Signals Found")

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    if st.button("📊 RUN 5 DAY BACKTEST"):

        with st.spinner("Running Backtest..."):

            with ThreadPoolExecutor(max_workers=20) as executor:

                all_bt = list(
                    executor.map(
                        lambda s: scan_stock(
                            s,
                            True
                        ),
                        stocks
                    )
                )

            flat_bt = [
                item
                for sublist in all_bt
                for item in sublist
            ]

            if len(flat_bt) > 0:

                df_bt = pd.DataFrame(flat_bt)

                st.success(
                    f"TOTAL BACKTEST SIGNALS : {len(df_bt)}"
                )

                st.dataframe(
                    df_bt,
                    use_container_width=True
                )

                # BACKTEST EXCEL
                bt_buffer = io.BytesIO()

                with pd.ExcelWriter(
                    bt_buffer,
                    engine='xlsxwriter'
                ) as writer:

                    df_bt.to_excel(
                        writer,
                        index=False,
                        sheet_name='Backtest'
                    )

                st.download_button(
                    "📥 DOWNLOAD BACKTEST EXCEL",
                    bt_buffer.getvalue(),
                    file_name="BACKTEST_REPORT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:

                st.warning("No Backtest Signals Found")
