import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# 🚀 PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="🚀 NSE AI QUANT PRO V16.0",
    layout="wide"
)

# =========================================================
# 🚀 TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# 🚀 HEADER
# =========================================================
st.markdown("""
<h1 style='text-align:center; color:#22c55e;'>
🚀 NSE AI QUANT PRO V16.0
</h1>
""", unsafe_allow_html=True)

st.markdown(f"""
<h4 style='text-align:center;'>
🕒 IST TIME: {now.strftime("%Y-%m-%d %H:%M:%S")}
<br>
📊 Strategy: EMA9 + EMA21 + VWAP CROSS + RSI + ATR
</h4>
""", unsafe_allow_html=True)

# =========================================================
# 🚀 NSE STOCKS
# =========================================================
stocks = [
    "ABB","ACC","AUBANK","ADANIENSOL","ADANIENT",
    "ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL",
    "ABCAPITAL","ABFRL","ALKEM","AMBUJACEM",
    "APOLLOHOSP","APOLLOTYRE","ASHOKLEY",
    "ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BEL","BHEL",
    "BPCL","BHARTIARTL","CANBK","CIPLA",
    "COALINDIA","DLF","DRREDDY","GAIL",
    "HDFCBANK","HCLTECH","HINDALCO",
    "ICICIBANK","INFY","ITC","JSWSTEEL",
    "KOTAKBANK","LT","M&M","MARUTI",
    "NTPC","ONGC","RELIANCE","SBIN",
    "SUNPHARMA","TATASTEEL","TCS",
    "TECHM","TITAN","WIPRO","ZOMATO"
]

# =========================================================
# 🚀 FETCH DATA
# =========================================================
@st.cache_data(ttl=120)
def fetch_data():

    tickers = [s + ".NS" for s in stocks]

    data = yf.download(
        tickers=tickers,
        period="7d",
        interval="15m",
        auto_adjust=True,
        group_by='ticker',
        progress=False,
        threads=True
    )

    return data

data_pool = fetch_data()

# =========================================================
# 🚀 INDICATORS
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
        df.groupby(df.index.date)['PV'].cumsum()
        /
        (
            df.groupby(df.index.date)['Volume'].cumsum() + 1e-9
        )
    )

    # RSI
    delta = df['Close'].diff()

    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / (loss + 1e-9)

    df['RSI'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df['High'] - df['Low']
    high_cp = abs(df['High'] - df['Close'].shift())
    low_cp = abs(df['Low'] - df['Close'].shift())

    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    # Volume
    df['VOLAVG'] = df['Volume'].rolling(20).mean()

    df['RVOL'] = (
        df['Volume']
        /
        (df['VOLAVG'] + 1e-9)
    )

    # Candle Body
    df['BODY'] = abs(df['Close'] - df['Open'])

    df['BODY_AVG'] = df['BODY'].rolling(10).mean()

    return df

# =========================================================
# 🚀 SCANNER ENGINE
# =========================================================
def scan(stock, mode="TODAY"):

    try:

        ticker = stock + ".NS"

        raw_df = data_pool[ticker].dropna()

        df = get_indicators(raw_df)

        if df.empty:
            return []

        # =================================================
        # TIMEZONE FIX
        # =================================================
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(IST)
        else:
            df.index = df.index.tz_convert(IST)

        # =================================================
        # TODAY / BACKTEST
        # =================================================
        if mode == "TODAY":
            scan_df = df[df.index.date == now.date()]
        else:
            scan_df = df.tail(500)

        results = []

        # =================================================
        # LOOP
        # =================================================
        for i in range(2, len(scan_df)):

            row = scan_df.iloc[i]
            prev = scan_df.iloc[i - 1]

            # =============================================
            # BIG PLAYER
            # =============================================
            big_player = (
                row['RVOL'] > 1.3
                and
                row['BODY'] > (1.1 * row['BODY_AVG'])
            )

            # =============================================
            # PULLBACK
            # =============================================
            pb_buy = (
                prev['Low'] > prev['EMA21']
                and
                row['Low'] <= row['EMA21']
                and
                row['Close'] > row['EMA21']
            )

            pb_sell = (
                prev['High'] < prev['EMA21']
                and
                row['High'] >= row['EMA21']
                and
                row['Close'] < row['EMA21']
            )

            # =============================================
            # VWAP CROSS
            # =============================================
            vwap_bull_cross = (
                prev['EMA21'] < prev['VWAP']
                and
                row['EMA21'] > row['VWAP']
            )

            vwap_bear_cross = (
                prev['EMA21'] > prev['VWAP']
                and
                row['EMA21'] < row['VWAP']
            )

            # =============================================
            # STRONG TREND
            # =============================================
            strong_buy = (
                row['EMA9'] > row['EMA21'] > row['VWAP']
            )

            strong_sell = (
                row['EMA9'] < row['EMA21'] < row['VWAP']
            )

            # =============================================
            # BUY SIGNAL
            # =============================================
            buy_sig = (
                strong_buy
                and
                row['Close'] > row['VWAP']
                and
                row['RSI'] > 50
                and
                (
                    big_player
                    or
                    pb_buy
                    or
                    vwap_bull_cross
                )
            )

            # =============================================
            # SELL SIGNAL
            # =============================================
            sell_sig = (
                strong_sell
                and
                row['Close'] < row['VWAP']
                and
                row['RSI'] < 50
                and
                (
                    big_player
                    or
                    pb_sell
                    or
                    vwap_bear_cross
                )
            )

            # =============================================
            # FINAL SIGNAL
            # =============================================
            if buy_sig or sell_sig:

                signal = "BUY" if buy_sig else "SELL"

                price = round(row['Close'], 2)

                risk = row['ATR'] * 1.5

                if buy_sig:

                    sl = round(price - risk, 2)

                    tgt = round(price + (risk * 2), 2)

                else:

                    sl = round(price + risk, 2)

                    tgt = round(price - (risk * 2), 2)

                # =========================================
                # SIGNAL TYPE
                # =========================================
                if vwap_bull_cross:
                    sig_type = "🔥 VWAP BULL"

                elif vwap_bear_cross:
                    sig_type = "🔻 VWAP BEAR"

                elif big_player:
                    sig_type = "🚀 BIG PLAYER"

                elif pb_buy or pb_sell:
                    sig_type = "🔄 PULLBACK"

                else:
                    sig_type = "📈 TREND"

                # =========================================
                # BACKTEST
                # =========================================
                status = "OPEN"

                pnl = 0.0

                if mode == "BACKTEST":

                    future_data = scan_df.iloc[i+1:i+15]

                    for _, f_row in future_data.iterrows():

                        if buy_sig:

                            if f_row['High'] >= tgt:

                                status = "🎯 TARGET"

                                pnl = round(tgt - price, 2)

                                break

                            elif f_row['Low'] <= sl:

                                status = "🛑 STOPLOSS"

                                pnl = round(sl - price, 2)

                                break

                        else:

                            if f_row['Low'] <= tgt:

                                status = "🎯 TARGET"

                                pnl = round(price - tgt, 2)

                                break

                            elif f_row['High'] >= sl:

                                status = "🛑 STOPLOSS"

                                pnl = round(price - sl, 2)

                                break

                # =========================================
                # STORE RESULT
                # =========================================
                results.append({

                    "DATE": row.name.strftime("%Y-%m-%d"),

                    "TIME": row.name.strftime("%H:%M"),

                    "STOCK": stock,

                    "SIGNAL": signal,

                    "TYPE": sig_type,
