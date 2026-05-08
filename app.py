import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="🚀 NSE AI V27 IMPROVED PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# NIFTY STATUS
# =========================================================
def get_nifty_summary():
    try:
        nifty = yf.Ticker("^NSEI").history(period="5d")

        last_close = nifty['Close'].iloc[-1]
        prev_close = nifty['Close'].iloc[-2]

        change = last_close - prev_close
        pct = (change / prev_close) * 100

        market_up = last_close > nifty['Close'].rolling(5).mean().iloc[-1]

        color = "#16a34a" if market_up else "#dc2626"
        status = "BULLISH" if market_up else "BEARISH"

        return f"""
        <div style='padding:15px;border-radius:10px;
        background:{color};color:white;text-align:center'>
        <h2>🚀 NIFTY MARKET TREND: {status} ({pct:.2f}%)</h2>
        </div>
        """, market_up

    except:
        return """
        <div style='padding:15px;border-radius:10px;
        background:#334155;color:white;text-align:center'>
        <h2>NIFTY DATA LOADING...</h2>
        </div>
        """, True

summary_html, market_up = get_nifty_summary()

st.markdown(summary_html, unsafe_allow_html=True)

# =========================================================
# NIFTY 200 STOCKS
# =========================================================
nifty_200 = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
    "SBIN","AXISBANK","ITC","LT","BHARTIARTL",
    "KOTAKBANK","ASIANPAINT","HINDUNILVR","BAJFINANCE",
    "MARUTI","TITAN","SUNPHARMA","ULTRACEMCO",
    "WIPRO","TECHM","POWERGRID","NTPC","ONGC",
    "COALINDIA","JSWSTEEL","TATASTEEL","HINDALCO",
    "ADANIENT","ADANIPORTS","BEL","BHEL","DLF",
    "BPCL","GAIL","M&M","BAJAJFINSV","INDUSINDBK",
    "EICHERMOT","GRASIM","HCLTECH","HEROMOTOCO",
    "NESTLEIND","SBILIFE","TATAMOTORS","UPL",
    "DRREDDY","CIPLA","DIVISLAB","BRITANNIA"
]

# =========================================================
# EXCEL DOWNLOAD
# =========================================================
def to_excel(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Scanner')

    return output.getvalue()

# =========================================================
# BULK DATA
# =========================================================
@st.cache_data(ttl=300)
def fetch_data():
    return yf.download(
        [s + ".NS" for s in nifty_200],
        period="1mo",
        interval="15m",
        group_by="ticker",
        auto_adjust=True,
        threads=True
    )

all_data = fetch_data()

# =========================================================
# RSI FUNCTION
# =========================================================
def calculate_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================================================
# CORE ENGINE
# =========================================================
def run_engine(stock, raw_data, target_date):

    try:

        ticker = stock + ".NS"

        df = raw_data[ticker].dropna().copy()

        if len(df) < 50:
            return []

        # =================================================
        # INDICATORS
        # =================================================
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

        df['PV'] = df['Close'] * df['Volume']

        df['VWAP'] = (
            df.groupby(df.index.date)['PV'].cumsum()
            /
            (df.groupby(df.index.date)['Volume'].cumsum() + 1e-9)
        )

        tr = pd.concat([
            df['High'] - df['Low'],
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        ], axis=1).max(axis=1)

        df['ATR'] = tr.rolling(14, min_periods=1).mean()

        df['VOL_AVG'] = df['Volume'].rolling(20).mean()

        df['RSI'] = calculate_rsi(df['Close'])

        # =================================================
        # TIMEZONE FIX
        # =================================================
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)

        # =================================================
        # DATE FILTER
        # =================================================
        analysis_df = df[
            df.index.date ==
            pd.to_datetime(target_date).date()
        ]

        results = []

        # =================================================
        # LOOP
        # =================================================
        for i in range(1, len(analysis_df)):

            row = analysis_df.iloc[i]
            prev = analysis_df.iloc[i - 1]

            current_time = row.name.time()

            valid_time = (
                current_time >= datetime.strptime("09:30", "%H:%M").time()
                and
                current_time <= datetime.strptime("14:45", "%H:%M").time()
            )

            if not valid_time:
                continue

            is_green = row['Close'] > row['Open']
            is_red = row['Close'] < row['Open']

            high_volume = row['Volume'] > row['VOL_AVG']

            # =============================================
            # IMPROVED SIGNALS
            # =============================================
            buy_sig = (
                (prev['Close'] <= prev['VWAP'])
                and
                (row['Close'] > row['VWAP'])
                and
                is_green
                and
                high_volume
                and
                row['RSI'] > 55
                and
                market_up
            )

            sell_sig = (
                (prev['Close'] >= prev['VWAP'])
                and
                (row['Close'] < row['VWAP'])
                and
                is_red
                and
                high_volume
                and
                row['RSI'] < 45
                and
                not market_up
            )

            if buy_sig or sell_sig:

                entry = round(float(row['Close']), 2)

                atr = float(row['ATR'])

                # =========================================
                # BETTER SL/TGT
                # =========================================
                if buy_sig:
                    sl = round(entry - atr, 2)
                    tgt = round(entry + (atr * 2), 2)
                else:
                    sl = round(entry + atr, 2)
                    tgt = round(entry - (atr * 2), 2)

                # =========================================
                # QUALITY SCORE
                # =========================================
                score = 0

                if high_volume:
                    score += 1

                if row['RSI'] > 60 or row['RSI'] < 40:
                    score += 1

                if abs(row['Close'] - row['VWAP']) > atr * 0.3:
                    score += 1

                quality = f"{score}/3"

                # =========================================
                # TARGET CHECK
                # =========================================
                status = "⏳ OPEN"

                future = analysis_df.iloc[i+1:i+15]

                for _, f in future.iterrows():

                    if buy_sig:

                        if f['High'] >= tgt:
                            status = "✅ TARGET HIT"
                            break

                        if f['Low'] <= sl:
                            status = "❌ SL HIT"
                            break

                    else:

                        if f['Low'] <= tgt:
                            status = "✅ TARGET HIT"
                            break

                        if f['High'] >= sl:
                            status = "❌ SL HIT"
                            break

                results.append({

                    "DATE": row.name.strftime("%Y-%m-%d"),

                    "TIME": row.name.strftime("%H:%M"),

                    "STOCK": stock,

                    "SIGNAL": "BUY" if buy_sig else "SELL",

                    "ENTRY": entry,

                    "SL": sl,

                    "TARGET": tgt,

                    "RSI": round(row['RSI'], 2),

                    "QUALITY": quality,

                    "STATUS": status
                })

        return results

    except:
        return []

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🔥 LIVE SCANNER",
    "📊 BACKTEST"
])

# =========================================================
# LIVE SCANNER
# =========================================================
with tab1:

    st.subheader("🚀 LIVE MARKET SCANNER")

    if st.button("RUN LIVE SCAN"):

        results = []

        progress = st.progress(0)

        with ThreadPoolExecutor(max_workers=10) as executor:

            futures = []

            for s in nifty_200:
                futures.append(
                    executor.submit(
                        run_engine,
                        s,
                        all_data,
                        now.date()
                    )
                )

            for idx, future in enumerate(futures):

                res = future.result()

                if res:
                    results.append(res[-1])

                progress.progress((idx + 1) / len(futures))

        if results:

            df_live = pd.DataFrame(results)

            st.dataframe(
                df_live.sort_values(
                    by="QUALITY",
                    ascending=False
                ),
                use_container_width=True
            )

            st.success(
                f"TOTAL SIGNALS FOUND: {len(df_live)}"
            )

            st.download_button(
                "📥 DOWNLOAD LIVE EXCEL",
                to_excel(df_live),
                file_name=f"LIVE_SCAN_{now.date()}.xlsx"
            )

        else:

            st.warning("NO LIVE SIGNALS FOUND")

# =========================================================
# BACKTEST
# =========================================================
with tab2:

    st.subheader("📊 DATE WISE BACKTEST")

    selected_date = st.date_input(
        "SELECT DATE",
        now.date() - timedelta(days=1)
    )

    if st.button("RUN BACKTEST"):

        bt_results = []

        progress = st.progress(0)

        with ThreadPoolExecutor(max_workers=10) as executor:

            futures = []

            for s in nifty_200:
                futures.append(
                    executor.submit(
                        run_engine,
                        s,
                        all_data,
                        selected_date
                    )
                )

            for idx, future in enumerate(futures):

                res = future.result()

                if res:
                    bt_results.extend(res)

                progress.progress((idx + 1) / len(futures))

        if bt_results:

            df_bt = pd.DataFrame(bt_results)

            st.dataframe(
                df_bt.sort_values(
                    by="QUALITY",
                    ascending=False
                ),
                use_container_width=True
            )

            wins = len(
                df_bt[df_bt['STATUS'] == "✅ TARGET HIT"]
            )

            losses = len(
                df_bt[df_bt['STATUS'] == "❌ SL HIT"]
            )

            open_trades = len(
                df_bt[df_bt['STATUS'] == "⏳ OPEN"]
            )

            accuracy = round(
                (wins / (wins + losses + 1e-9)) * 100,
                2
            )

            st.success(
                f"""
                ✅ WINS: {wins}
                | ❌ LOSSES: {losses}
                | ⏳ OPEN: {open_trades}
                | 🎯 ACCURACY: {accuracy}%
                """
            )

            st.download_button(
                "📥 DOWNLOAD BACKTEST EXCEL",
                to_excel(df_bt),
                file_name=f"BACKTEST_{selected_date}.xlsx"
            )

        else:

            st.warning("NO BACKTEST SIGNALS FOUND")
