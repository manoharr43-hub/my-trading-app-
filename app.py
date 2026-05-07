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
st.set_page_config(page_title="🚀 NSE AI QUANT PRO V20", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.markdown(
    '<h1 style="text-align:center; color:#22c55e;">🚀 NSE AI QUANT PRO V20</h1>',
    unsafe_allow_html=True
)

st.markdown(
    f'<h4 style="text-align:center;">🕒 IST: {now.strftime("%Y-%m-%d %H:%M:%S")} | REAL BACKTEST + SCORE ENGINE</h4>',
    unsafe_allow_html=True
)

# =========================================================
# NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS",
    "ADANIPOWER","ATGL","ABCAPITAL","ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP",
    "APOLLOTYRE","ASHOKLEY","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE",
    "BAJAJFINSV","BEL","BHEL","BPCL","BHARTIARTL","CANBK","CIPLA","COALINDIA",
    "DLF","DRREDDY","GAIL","HDFCBANK","HCLTECH","HINDALCO","ICICIBANK",
    "INFY","ITC","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NTPC","ONGC",
    "RELIANCE","SBIN","SUNPHARMA","TATASTEEL","TCS","TECHM","TITAN","WIPRO",
    "ZOMATO"
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
        group_by='ticker',
        progress=False,
        threads=True
    )

    return data

data_pool = fetch_data()

# =========================================================
# NIFTY MARKET FILTER
# =========================================================
@st.cache_data(ttl=300)
def get_market_trend():

    nifty = yf.download(
        "^NSEI",
        period="2d",
        interval="15m",
        progress=False
    )

    nifty['EMA20'] = nifty['Close'].ewm(span=20).mean()

    bullish = nifty['Close'].iloc[-1] > nifty['EMA20'].iloc[-1]

    return bullish

market_bullish = get_market_trend()

# =========================================================
# INDICATORS
# =========================================================
def get_indicators(df):

    df = df.copy()

    if len(df) < 50:
        return pd.DataFrame()

    # EMA
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby(df.index.date)['PV'].cumsum() /
        (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)
    )

    # Bollinger Bands
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std()

    df['BB_UPPER'] = df['BB_MID'] + (df['BB_STD'] * 2)
    df['BB_LOWER'] = df['BB_MID'] - (df['BB_STD'] * 2)

    # True Range
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift(1))
    tr3 = abs(df['Low'] - df['Close'].shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR
    df['ATR'] = tr.rolling(14).mean()

    # ADX
    plus_dm = df['High'].diff().clip(lower=0)
    minus_dm = df['Low'].diff().clip(upper=0).abs()

    tr_smooth = tr.rolling(14).mean()

    plus_di = 100 * (
        plus_dm.rolling(14).mean() /
        (tr_smooth + 1e-9)
    )

    minus_di = 100 * (
        minus_dm.rolling(14).mean() /
        (tr_smooth + 1e-9)
    )

    dx = 100 * (
        abs(plus_di - minus_di) /
        (plus_di + minus_di + 1e-9)
    )

    df['ADX'] = dx.rolling(14).mean()

    # RSI
    delta = df['Close'].diff()

    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # RVOL
    df['RVOL'] = (
        df['Volume'] /
        (df['Volume'].rolling(20).mean() + 1e-9)
    )

    return df

# =========================================================
# SCORE ENGINE
# =========================================================
def calculate_score(row):

    score = 0

    if row['ADX'] > 35:
        score += 25

    if row['RVOL'] > 2:
        score += 25

    if 58 <= row['RSI'] <= 65:
        score += 25

    if abs(row['EMA9'] - row['EMA21']) > 1:
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

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)

        if mode == "TODAY":
            scan_df = df[df.index.date == now.date()]
        else:
            scan_df = df.copy()

        results = []

        for i in range(30, len(scan_df)-10):

            row = scan_df.iloc[i]
            prev = scan_df.iloc[i-1]

            valid_time = (
                time(9, 45) <= row.name.time() <= time(14, 45)
            )

            strong_trend = row['ADX'] > 30

            bb_buy_safety = row['Close'] < row['BB_UPPER']
            bb_sell_safety = row['Close'] > row['BB_LOWER']

            pb_buy = (
                prev['Low'] <= prev['EMA21'] and
                row['Close'] > row['EMA21']
            )

            pb_sell = (
                prev['High'] >= prev['EMA21'] and
                row['Close'] < row['EMA21']
            )

            vol_ok = row['RVOL'] > 1.5

            trend_filter = (
                abs(row['EMA9'] - row['EMA21']) > 0.3
            )

            candle_strength = (
                abs(row['Close'] - row['Open']) >
                (row['ATR'] * 0.3)
            )

            buy_sig = (
                row['EMA9'] > row['EMA21'] and
                row['Close'] > row['VWAP'] and
                (pb_buy or vol_ok) and
                55 < row['RSI'] < 68 and
                strong_trend and
                valid_time and
                bb_buy_safety and
                trend_filter and
                candle_strength and
                market_bullish
            )

            sell_sig = (
                row['EMA9'] < row['EMA21'] and
                row['Close'] < row['VWAP'] and
                (pb_sell or vol_ok) and
                32 < row['RSI'] < 45 and
                strong_trend and
                valid_time and
                bb_sell_safety and
                trend_filter and
                candle_strength and
                not market_bullish
            )

            if buy_sig or sell_sig:

                signal = "BUY" if buy_sig else "SELL"

                entry = round(row['Close'], 2)

                risk = row['ATR'] * 1.5

                sl = (
                    round(entry - risk, 2)
                    if buy_sig else
                    round(entry + risk, 2)
                )

                tgt = (
                    round(entry + (risk * 2), 2)
                    if buy_sig else
                    round(entry - (risk * 2), 2)
                )

                # REAL BACKTEST
                future_df = scan_df.iloc[i+1:i+10]

                status = "⏳ RUNNING"

                for _, frow in future_df.iterrows():

                    if buy_sig:

                        if frow['High'] >= tgt:
                            status = "✅ TGT HIT"
                            break

                        elif frow['Low'] <= sl:
                            status = "❌ SL HIT"
                            break

                    else:

                        if frow['Low'] <= tgt:
                            status = "✅ TGT HIT"
                            break

                        elif frow['High'] >= sl:
                            status = "❌ SL HIT"
                            break

                score = calculate_score(row)

                results.append({
                    "DATE": row.name.strftime("%Y-%m-%d"),
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": signal,
                    "ENTRY": entry,
                    "SL": sl,
                    "TARGET": tgt,
                    "STATUS": status,
                    "ADX": round(row['ADX'], 1),
                    "RSI": round(row['RSI'], 1),
                    "RVOL": round(row['RVOL'], 2),
                    "SCORE": score
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

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    return output.getvalue()

# =========================================================
# STATUS STYLE
# =========================================================
def style_status(val):

    if "TGT" in str(val):
        return 'color: #22c55e; font-weight: bold'

    if "SL" in str(val):
        return 'color: #ef4444; font-weight: bold'

    return 'color: #facc15; font-weight: bold'

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

    st.subheader("🚀 LIVE MARKET SCANNER")

    if st.button("🚀 RUN LIVE SCANNER"):

        with st.spinner("Scanning NSE Stocks..."):

            with ThreadPoolExecutor(max_workers=10) as executor:

                results = executor.map(
                    lambda s: scan(s, "TODAY"),
                    stocks
                )

            res = [
                item
                for sublist in results
                for item in sublist
            ]

        if res:

            df = pd.DataFrame(res)

            df = df.sort_values(
                ['SCORE', 'TIME'],
                ascending=[False, False]
            )

            st.success(f"{len(df)} Signals Found")

            st.dataframe(
                df.style.map(
                    style_status,
                    subset=['STATUS']
                ),
                use_container_width=True
            )

            st.download_button(
                "📥 Download Scanner Excel",
                to_excel(df),
                file_name=f"Scanner_V20_{now.date()}.xlsx"
            )

        else:
            st.warning("No Strong Signals Found")

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    st.subheader("📊 REAL BACKTEST ENGINE")

    if st.button("📊 RUN BACKTEST"):

        with st.spinner("Running Backtest..."):

            with ThreadPoolExecutor(max_workers=10) as executor:

                results_bt = executor.map(
                    lambda s: scan(s, "BACKTEST"),
                    stocks
                )

            res_bt = [
                item
                for sublist in results_bt
                for item in sublist
            ]

        if res_bt:

            df_bt = pd.DataFrame(res_bt)

            df_bt = df_bt.sort_values(
                ['DATE', 'TIME'],
                ascending=False
            )

            wins = len(
                df_bt[df_bt['STATUS'].str.contains("TGT")]
            )

            loss = len(
                df_bt[df_bt['STATUS'].str.contains("SL")]
            )

            total = wins + loss

            accuracy = (
                round((wins / total) * 100, 2)
                if total > 0 else 0
            )

            c1, c2, c3 = st.columns(3)

            c1.metric("🎯 Accuracy", f"{accuracy}%")
            c2.metric("✅ Wins", wins)
            c3.metric("❌ Loss", loss)

            st.dataframe(
                df_bt.style.map(
                    style_status,
                    subset=['STATUS']
                ),
                use_container_width=True
            )

            st.download_button(
                "📥 Download Backtest Excel",
                to_excel(df_bt),
                file_name="Backtest_V20.xlsx"
            )

        else:
            st.warning("No Backtest Signals Found")
