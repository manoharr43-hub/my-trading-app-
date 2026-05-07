# =========================================================
# 🚀 NSE AI QUANT PRO V13.0 ULTRA FINAL
# NSE 200 STOCKS
# EMA9 + VWAP + RSI + RVOL
# TODAY SCANNER + 5 DAY BACKTEST
# EXCEL DOWNLOAD + IST TIME FIX
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
    page_title="🚀 NSE AI QUANT PRO V13.0",
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
    '<div class="main-title">🚀 NSE AI QUANT PRO V13.0 ULTRA</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">🕒 LIVE TIME : {now.strftime("%H:%M:%S")} IST</div>',
    unsafe_allow_html=True
)

# =========================================================
# REFRESH BUTTON
# =========================================================
if st.button("🔄 REFRESH DATA"):
    st.cache_data.clear()
    st.rerun()

# =========================================================
# NSE 200 STOCKS
# =========================================================
stocks = [

"ABB","ACC","AUBANK","ADANIENSOL","ADANIENT",
"ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
"ABCAPITAL","ABFRL","ALKEM","AMBUJACEM",
"APOLLOHOSP","APOLLOTYRE","ASHOKLEY",
"ASIANPAINT","ASTRAL","AUROPHARMA","AXISBANK",
"BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV",
"BAJAJHLDNG","BALKRISIND","BANDHANBNK",
"BANKBARODA","BANKINDIA","BATAINDIA","BEL",
"BERGEPAINT","BHARATFORG","BHEL","BPCL",
"BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA",
"CANBK","CGPOWER","CHOLAFIN","CIPLA",
"COALINDIA","COFORGE","COLPAL","CONCOR",
"COROMANDEL","CROMPTON","CUMMINSIND",
"CYIENT","DABUR","DALBHARAT","DEEPAKNTR",
"DELHIVERY","DIVISLAB","DIXON","DLF",
"DRREDDY","EICHERMOT","ESCORTS","EXIDEIND",
"FEDERALBNK","FORTIS","GAIL","GLENMARK",
"GMRINFRA","GODREJCP","GODREJPROP","GRASIM",
"GUJGASLTD","HAL","HAVELLS","HCLTECH",
"HDFCBANK","HDFCLIFE","HEROMOTOCO",
"HINDALCO","HINDCOPPER","HINDPETRO",
"HINDUNILVR","ICICIBANK","IDFCFIRSTB",
"IEX","IGL","INDHOTEL","INDIGO",
"INDUSINDBK","INDUSTOWER","INFY","IOC",
"IRCTC","IRFC","ITC","JINDALSTEL",
"JSWENERGY","JSWSTEEL","JUBLFOOD",
"KOTAKBANK","KPITTECH","LT","LTIM",
"LTTS","LICI","LUPIN","M&M",
"M&MFIN","MARICO","MARUTI","MAXHEALTH",
"METROPOLIS","MFSL","MGL","MPHASIS",
"MRF","MUTHOOTFIN","NATIONALUM",
"NESTLEIND","NMDC","NTPC","OBEROIRLTY",
"ONGC","PAYTM","PERSISTENT","PETRONET",
"PFC","PIDILITIND","PIIND","PNB",
"POLYCAB","POONAWALLA","POWERGRID",
"PRESTIGE","PVRINOX","RECLTD","RELIANCE",
"SAIL","SBICARD","SBILIFE","SBIN",
"SIEMENS","SRF","SUNPHARMA","SUNTV",
"SYNGENE","TATACOMM","TATACONSUM",
"TATAELXSI","TATAMOTORS","TATAPOWER",
"TATASTEEL","TCS","TECHM","TITAN",
"TORNTPHARM","TRENT","TVSMOTOR",
"ULTRACEMCO","UPL","VBL","VEDL",
"VOLTAS","WIPRO","YESBANK","ZEEL",
"ZOMATO"

]

# =========================================================
# INDICATORS
# =========================================================
def add_indicators(df):

    df = df.copy()

    if df.empty or len(df) < 30:
        return pd.DataFrame()

    df.index = pd.to_datetime(
        df.index,
        utc=True
    ).tz_convert("Asia/Kolkata")

    df['DATE_ONLY'] = df.index.date

    # EMA9
    df['EMA9'] = df['Close'].ewm(
        span=9,
        adjust=False
    ).mean()

    # EMA20
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

    return df

# =========================================================
# FETCH DATA
# =========================================================
@st.cache_data(ttl=60)
def fetch_data():

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

# =========================================================
# LOAD DATA
# =========================================================
d15m, d1h = fetch_data()

# =========================================================
# MARKET TREND
# =========================================================
market_trend = "UNKNOWN"

try:

    close_series = d1h['Close']

    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]

    last_close = float(close_series.iloc[-1])

    ema20 = float(
        close_series.ewm(
            span=20,
            adjust=False
        ).mean().iloc[-1]
    )

    market_trend = (
        "POSITIVE"
        if last_close > ema20
        else "NEGATIVE"
    )

    box_class = (
        "bull"
        if market_trend == "POSITIVE"
        else "bear"
    )

    st.markdown(
        f"""
        <div class="market-box {box_class}">
        📈 MARKET TREND : {market_trend}
        </div>
        """,
        unsafe_allow_html=True
    )

except Exception as e:

    st.error(f"Market Trend Error : {e}")

# =========================================================
# SCAN ENGINE
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

        for i in range(1, len(scan_df)):

            idx = df.index.get_loc(scan_df.index[i])

            row = df.iloc[idx]
            prev = df.iloc[idx - 1]

            # BUY
            buy_signal = (

                row['EMA9'] > row['VWAP']

                and

                prev['EMA9'] <= prev['VWAP']

                and

                row['RSI'] > 50

                and

                row['RVOL'] > 0.8
            )

            # SELL
            sell_signal = (

                row['EMA9'] < row['VWAP']

                and

                prev['EMA9'] >= prev['VWAP']

                and

                row['RSI'] < 50

                and

                row['RVOL'] > 0.8
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

        with st.spinner("Scanning NSE 200 Stocks..."):

            with ThreadPoolExecutor(max_workers=25) as executor:

                all_results = list(
                    executor.map(
                        scan_stock,
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

                df_live = df_live.drop_duplicates(
                    subset=["STOCK"],
                    keep="last"
                )

                df_live = df_live.sort_values(
                    by="TIME",
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

                # EXCEL
                output = io.BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine='xlsxwriter'
                ) as writer:

                    df_live.to_excel(
                        writer,
                        index=False,
                        sheet_name='Today Scanner'
                    )

                st.download_button(
                    "📥 DOWNLOAD TODAY EXCEL",
                    output.getvalue(),
                    file_name="TODAY_SCANNER.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:

                st.warning(
                    "❌ No Signals Found"
                )

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    if st.button("📊 RUN BACKTEST"):

        with st.spinner("Running 5 Day Backtest..."):

            with ThreadPoolExecutor(max_workers=25) as executor:

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
                    f"✅ TOTAL BACKTEST SIGNALS : {len(df_bt)}"
                )

                st.dataframe(
                    df_bt,
                    use_container_width=True
                )

                # BACKTEST EXCEL
                bt_output = io.BytesIO()

                with pd.ExcelWriter(
                    bt_output,
                    engine='xlsxwriter'
                ) as writer:

                    df_bt.to_excel(
                        writer,
                        index=False,
                        sheet_name='Backtest'
                    )

                st.download_button(
                    "📥 DOWNLOAD BACKTEST EXCEL",
                    bt_output.getvalue(),
                    file_name="BACKTEST_REPORT.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:

                st.warning(
                    "❌ No Backtest Signals Found"
                )
