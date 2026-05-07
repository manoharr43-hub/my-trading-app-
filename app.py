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
    page_title="🚀 NSE AI QUANT PRO V20.0",
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
🚀 NSE AI QUANT PRO V20.0
</h1>
""", unsafe_allow_html=True)

st.markdown(f"""
<h4 style='text-align:center;'>
🕒 IST TIME: {now.strftime("%Y-%m-%d %H:%M:%S")}
<br>
📊 EMA9 + EMA21 + VWAP + RSI + ATR + BACKTEST
</h4>
""", unsafe_allow_html=True)

# =========================================================
# 🚀 NSE 200 STOCKS
# =========================================================
stocks = [

    "ABB","ACC","AUBANK","AADHARHFC","AARTIIND",
    "ABBOTINDIA","ADANIENSOL","ADANIENT",
    "ADANIGREEN","ADANIPORTS","ADANIPOWER",
    "ATGL","ABCAPITAL","ABFRL","ALKEM",
    "AMBUJACEM","APOLLOHOSP","APOLLOTYRE",
    "ASHOKLEY","ASIANPAINT","ASTRAL",
    "AUROPHARMA","AXISBANK","BAJAJ-AUTO",
    "BAJFINANCE","BAJAJFINSV","BALKRISIND",
    "BALRAMCHIN","BANDHANBNK","BANKBARODA",
    "BATAINDIA","BEL","BERGEPAINT",
    "BHARATFORG","BHARTIARTL","BHEL",
    "BIOCON","BPCL","BRITANNIA","BSOFT",
    "CANBK","CDSL","CHAMBLFERT","CHOLAFIN",
    "CIPLA","COALINDIA","COFORGE","COLPAL",
    "CONCOR","COROMANDEL","CROMPTON",
    "CUMMINSIND","DABUR","DALBHARAT",
    "DEEPAKNTR","DELHIVERY","DIVISLAB",
    "DIXON","DLF","DRREDDY","EICHERMOT",
    "ESCORTS","EXIDEIND","FEDERALBNK",
    "GAIL","GLAND","GLENMARK","GMRINFRA",
    "GNFC","GODREJCP","GODREJPROP",
    "GRANULES","GRASIM","GUJGASLTD",
    "HAL","HAVELLS","HCLTECH","HDFCAMC",
    "HDFCBANK","HDFCLIFE","HEROMOTOCO",
    "HFCL","HINDALCO","HINDCOPPER",
    "HINDPETRO","HINDUNILVR","HUDCO",
    "ICICIBANK","ICICIGI","ICICIPRULI",
    "IDEA","IDFCFIRSTB","IEX","IGL",
    "INDHOTEL","INDIAMART","INDIGO",
    "INDUSINDBK","INDUSTOWER","INFY",
    "IOC","IPCALAB","IRB","IRCTC",
    "IREDA","IRFC","ITC","JINDALSTEL",
    "JKCEMENT","JSWENERGY","JSWSTEEL",
    "JUBLFOOD","KALYANKJIL","KEI",
    "KOTAKBANK","KPITTECH","LALPATHLAB",
    "LAURUSLABS","LICHSGFIN","LICI",
    "LODHA","LT","LTF","LTIM","LTTS",
    "LUPIN","M&M","MANKIND","MARICO",
    "MARUTI","MCX","MFSL","MGL",
    "MOTHERSON","MPHASIS","MRF",
    "MUTHOOTFIN","NATIONALUM","NAUKRI",
    "NBCC","NCC","NESTLEIND","NHPC",
    "NMDC","NTPC","OBEROIRLTY","OFSS",
    "OIL","ONGC","PAGEIND","PATANJALI",
    "PAYTM","PEL","PERSISTENT",
    "PETRONET","PFC","PIDILITIND",
    "PIIND","PNB","POLICYBZR",
    "POLYCAB","POWERGRID","PRESTIGE",
    "RECLTD","RELIANCE","SAIL",
    "SBICARD","SBILIFE","SBIN",
    "SHREECEM","SHRIRAMFIN","SIEMENS",
    "SJVN","SOLARINDS","SONACOMS",
    "SRF","SUNPHARMA","SUNTV",
    "SUPREMEIND","SYNGENE","TATACHEM",
    "TATACOMM","TATACONSUM",
    "TATAMOTORS","TATAPOWER",
    "TATASTEEL","TCS","TECHM",
    "TIINDIA","TITAN","TORNTPHARM",
    "TORNTPOWER","TRENT","TVSMOTOR",
    "UBL","ULTRACEMCO","UNIONBANK",
    "UPL","VEDL","VOLTAS","WIPRO",
    "YESBANK","ZEEL","ZOMATO",
    "ZYDUSLIFE"

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
    df['EMA9'] = df['Close'].ewm(
        span=9,
        adjust=False
    ).mean()

    df['EMA21'] = df['Close'].ewm(
        span=21,
        adjust=False
    ).mean()

    # VWAP
    df['PV'] = df['Close'] * df['Volume']

    df['VWAP'] = (
        df.groupby(df.index.date)['PV'].cumsum()
        /
        (
            df.groupby(df.index.date)['Volume'].cumsum()
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

    df['RSI'] = 100 - (
        100 / (1 + rs)
    )

    # ATR
    high_low = df['High'] - df['Low']

    high_cp = abs(
        df['High'] - df['Close'].shift()
    )

    low_cp = abs(
        df['Low'] - df['Close'].shift()
    )

    tr = pd.concat(
        [high_low, high_cp, low_cp],
        axis=1
    ).max(axis=1)

    df['ATR'] = tr.rolling(14).mean()

    # RVOL
    df['VOLAVG'] = df['Volume'].rolling(20).mean()

    df['RVOL'] = (
        df['Volume']
        /
        (df['VOLAVG'] + 1e-9)
    )

    # BODY
    df['BODY'] = abs(
        df['Close'] - df['Open']
    )

    df['BODY_AVG'] = (
        df['BODY'].rolling(10).mean()
    )

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

            df.index = (
                df.index
                .tz_localize("UTC")
                .tz_convert(IST)
            )

        else:

            df.index = (
                df.index
                .tz_convert(IST)
            )

        # =================================================
        # TODAY / BACKTEST
        # =================================================
        if mode == "TODAY":

            scan_df = df[
                df.index.date == now.date()
            ]

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

                row['BODY']
                >
                (1.1 * row['BODY_AVG'])

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

                row['EMA9']
                >
                row['EMA21']
                >
                row['VWAP']

            )

            strong_sell = (

                row['EMA9']
                <
                row['EMA21']
                <
                row['VWAP']

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

                signal = (
                    "BUY"
                    if buy_sig
                    else "SELL"
                )

                price = round(
                    row['Close'],
                    2
                )

                risk = row['ATR'] * 1.5

                # =========================================
                # SL / TARGET
                # =========================================
                if buy_sig:

                    sl = round(
                        price - risk,
                        2
                    )

                    tgt = round(
                        price + (risk * 2),
                        2
                    )

                else:

                    sl = round(
                        price + risk,
                        2
                    )

                    tgt = round(
                        price - (risk * 2),
                        2
                    )

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

                    future_data = scan_df.iloc[
                        i+1 : i+15
                    ]

                    for _, f_row in future_data.iterrows():

                        if buy_sig:

                            if f_row['High'] >= tgt:

                                status = "🎯 TARGET"

                                pnl = round(
                                    tgt - price,
                                    2
                                )

                                break

                            elif f_row['Low'] <= sl:

                                status = "🛑 STOPLOSS"

                                pnl = round(
                                    sl - price,
                                    2
                                )

                                break

                        else:

                            if f_row['Low'] <= tgt:

                                status = "🎯 TARGET"

                                pnl = round(
                                    price - tgt,
                                    2
                                )

                                break

                            elif f_row['High'] >= sl:

                                status = "🛑 STOPLOSS"

                                pnl = round(
                                    price - sl,
                                    2
                                )

                                break

                # =========================================
                # SAVE RESULT
                # =========================================
                results.append({

                    "DATE": row.name.strftime("%Y-%m-%d"),

                    "TIME": row.name.strftime("%H:%M"),

                    "STOCK": stock,

                    "SIGNAL": signal,

                    "TYPE": sig_type,

                    "PRICE": round(price, 2),

                    "SL": round(sl, 2),

                    "TARGET": round(tgt, 2),

                    "EMA21": round(
                        row['EMA21'],
                        2
                    ),

                    "VWAP": round(
                        row['VWAP'],
                        2
                    ),

                    "RSI": round(
                        row['RSI'],
                        2
                    ),

                    "RVOL": round(
                        row['RVOL'],
                        2
                    ),

                    "RESULT": status,

                    "P&L": round(
                        pnl,
                        2
                    )

                })

        return results

    except Exception as e:

        print(f"ERROR IN {stock}: {e}")

        return []

# =========================================================
# 🚀 EXCEL EXPORT
# =========================================================
def to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine='xlsxwriter'
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="NSE_AI_QUANT"
        )

    return output.getvalue()

# =========================================================
# 🚀 TABS
# =========================================================
tab1, tab2 = st.tabs([

    "🔍 LIVE SCANNER",

    "📊 BACKTEST"

])

# =========================================================
# 🚀 LIVE SCANNER
# =========================================================
with tab1:

    st.subheader("🔍 LIVE MARKET SCANNER")

    if st.button("🚀 RUN LIVE SCAN"):

        with st.spinner("Scanning NSE 200 Stocks..."):

            with ThreadPoolExecutor(
                max_workers=20
            ) as executor:

                result = list(

                    executor.map(
                        lambda s: scan(s, "TODAY"),
                        stocks
                    )

                )

            flat = [

                item

                for sublist in result

                for item in sublist

            ]

            if len(flat) > 0:

                df_today = pd.DataFrame(flat)

                df_today = df_today.sort_values(
                    "TIME",
                    ascending=False
                )

                # =====================================
                # METRICS
                # =====================================
                total_buy = len(
                    df_today[
                        df_today['SIGNAL'] == "BUY"
                    ]
                )

                total_sell = len(
                    df_today[
                        df_today['SIGNAL'] == "SELL"
                    ]
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "TOTAL SIGNALS",
                    len(df_today)
                )

                c2.metric(
                    "BUY SIGNALS",
                    total_buy
                )

                c3.metric(
                    "SELL SIGNALS",
                    total_sell
                )

                # =====================================
                # DATAFRAME
                # =====================================
                st.dataframe(
                    df_today,
                    use_container_width=True
                )

                # =====================================
                # EXCEL
                # =====================================
                excel_today = to_excel(df_today)

                st.download_button(

                    label="📥 DOWNLOAD LIVE EXCEL",

                    data=excel_today,

                    file_name=f"""
NSE_LIVE_SIGNALS_
{now.strftime('%Y%m%d_%H%M')}.xlsx
""",

                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                )

            else:

                st.warning(
                    "❌ NO LIVE SIGNALS FOUND"
                )

# =========================================================
# 🚀 BACKTEST
# =========================================================
with tab2:

    st.subheader("📊 5-DAY BACKTEST")

    if st.button("📊 RUN BACKTEST"):

        with st.spinner("Running Backtest..."):

            with ThreadPoolExecutor(
                max_workers=20
            ) as executor:

                result_bt = list(

                    executor.map(
                        lambda s: scan(s, "BACKTEST"),
                        stocks
                    )

                )

            flat_bt = [

                item

                for sublist in result_bt

                for item in sublist

            ]

            if len(flat_bt) > 0:

                df_bt = pd.DataFrame(flat_bt)

                df_bt = df_bt.sort_values(
                    ["DATE", "TIME"],
                    ascending=False
                )

                # =====================================
                # METRICS
                # =====================================
                wins = len(
                    df_bt[
                        df_bt['RESULT'] == "🎯 TARGET"
                    ]
                )

                losses = len(
                    df_bt[
                        df_bt['RESULT'] == "🛑 STOPLOSS"
                    ]
                )

                total_trades = wins + losses

                if total_trades > 0:

                    win_rate = round(
                        (wins / total_trades) * 100,
                        2
                    )

                else:

                    win_rate = 0

                total_pnl = round(
                    df_bt['P&L'].sum(),
                    2
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "TOTAL SIGNALS",
                    len(df_bt)
                )

                c2.metric(
                    "WINS / LOSSES",
                    f"{wins} / {losses}"
                )

                c3.metric(
                    "WIN RATE",
                    f"{win_rate}%"
                )

                c4.metric(
                    "TOTAL P&L",
                    f"{total_pnl} pts"
                )

                # =====================================
                # DATAFRAME
                # =====================================
                st.dataframe(
                    df_bt,
                    use_container_width=True
                )

                # =====================================
                # EXCEL
                # =====================================
                excel_bt = to_excel(df_bt)

                st.download_button(

                    label="📥 DOWNLOAD BACKTEST EXCEL",

                    data=excel_bt,

                    file_name="NSE_BACKTEST_REPORT.xlsx",

                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                )

            else:

                st.warning(
                    "❌ NO BACKTEST SIGNALS FOUND"
                )

# =========================================================
# 🚀 FOOTER
# =========================================================
st.markdown("---")

st.markdown("""
<center>
<h4 style='color:gray;'>

🚀 NSE AI QUANT PRO V20.0

<br>

EMA + VWAP + RSI + ATR + NSE200

</h4>
</center>
""", unsafe_allow_html=True)
