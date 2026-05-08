import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
import io

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(page_title="🚀 NSE AI V31 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

# =========================================================
# LIVE CLOCK
# =========================================================
st.markdown(f"""
## 🕒 LIVE TIME (IST)
### {now.strftime("%Y-%m-%d %H:%M:%S")}
""")

# =========================================================
# NIFTY 50 DASHBOARD (POSITIVE / NEGATIVE)
# =========================================================
def nifty_dashboard():
    try:
        n = yf.Ticker("^NSEI").history(period="5d")

        last = n['Close'].iloc[-1]
        prev = n['Close'].iloc[-2]

        change = last - prev
        pct = (change / prev) * 100

        status = "🟢 POSITIVE" if change > 0 else "🔴 NEGATIVE"

        return f"""
        <div style="padding:15px;background:#0f172a;color:white;
        border-radius:10px;text-align:center">
        <h2>NIFTY 50 : {status}</h2>
        <h3>Change: {pct:.2f}%</h3>
        </div>
        """
    except:
        return "<h3>Loading NIFTY...</h3>"

st.markdown(nifty_dashboard(), unsafe_allow_html=True)

# =========================================================
# NSE 200 STOCKS (FULL EXPANDED)
# =========================================================
stocks = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "ITC","LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA",
    "JSWSTEEL","TATASTEEL","HINDALCO","BAJFINANCE","BAJAJFINSV",
    "ASIANPAINT","ULTRACEMCO","NESTLEIND","BRITANNIA","DRREDDY","CIPLA",
    "DIVISLAB","ADANIENT","ADANIPORTS","BEL","BHEL","DLF","GAIL",
    "IOC","BPCL","M&M","HEROMOTOCO","EICHERMOT","INDUSINDBK",
    "PNB","BANKBARODA","CANBK","SBILIFE","HDFCLIFE","TATAMOTORS",
    "TATAPOWER","GRASIM","UPL","PIDILITIND","DABUR","MARICO",
    "COLPAL","TRENT","PAGEIND","RECLTD","PFC","HAL","ABB","SIEMENS"
]

# =========================================================
# EXCEL FUNCTION
# =========================================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =========================================================
# DATA FETCH
# =========================================================
@st.cache_data(ttl=300)
def fetch_data():
    return yf.download(
        [s+".NS" for s in stocks],
        period="1mo",
        interval="15m",
        group_by="ticker",
        threads=True
    )

data = fetch_data()

# =========================================================
# RSI
# =========================================================
def rsi(x):
    d = x.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    rs = g.rolling(14).mean() / (l.rolling(14).mean()+1e-9)
    return 100 - (100/(1+rs))

# =========================================================
# ENGINE
# =========================================================
def engine(stock, raw, date):

    try:
        df = raw[stock+".NS"].dropna().copy()
        if len(df) < 50:
            return []

        df['EMA21'] = df['Close'].ewm(span=21).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()

        df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum()+1e-9)

        tr = pd.concat([
            df['High']-df['Low'],
            abs(df['High']-df['Close'].shift()),
            abs(df['Low']-df['Close'].shift())
        ], axis=1).max(axis=1)

        df['ATR'] = tr.rolling(14, min_periods=1).mean()

        df['RSI'] = rsi(df['Close'])

        df['VOL_AVG'] = df['Volume'].rolling(20).mean()

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        df.index = df.index.tz_convert(IST)

        df = df[df.index.date == pd.to_datetime(date).date()]

        results = []

        for i in range(1, len(df)):

            row = df.iloc[i]
            t = row.name.time()

            # TIME FILTER
            if not (datetime.strptime("09:30","%H:%M").time() <= t <= datetime.strptime("14:45","%H:%M").time()):
                continue

            vol_ok = row['Volume'] > row['VOL_AVG']

            # ================= BUY =================
            buy = (
                row['Close'] > row['VWAP'] and
                row['EMA21'] > row['EMA50'] and
                55 < row['RSI'] < 70 and
                vol_ok
            )

            # ================= SELL =================
            sell = (
                row['Close'] < row['VWAP'] and
                row['EMA21'] < row['EMA50'] and
                30 < row['RSI'] < 45 and
                vol_ok
            )

            if buy or sell:

                entry = row['Close']
                atr = row['ATR']

                sl = entry - atr*1.8 if buy else entry + atr*1.8
                tgt = entry + atr*1.6 if buy else entry - atr*1.6

                status = "OPEN"

                future = df.iloc[i+1:i+15]

                for _, f in future.iterrows():

                    if buy:
                        if f['High'] >= tgt:
                            status = "TARGET"
                            break
                        if f['Low'] <= sl:
                            status = "SL"
                            break
                    else:
                        if f['Low'] <= tgt:
                            status = "TARGET"
                            break
                        if f['High'] <= sl:
                            status = "SL"
                            break

                results.append({
                    "TIME": row.name.strftime("%H:%M"),
                    "STOCK": stock,
                    "SIGNAL": "BUY" if buy else "SELL",
                    "ENTRY": round(entry,2),
                    "SL": round(sl,2),
                    "TARGET": round(tgt,2),
                    "RSI": round(row['RSI'],2),
                    "STATUS": status
                })

        return results

    except:
        return []

# =========================================================
# UI
# =========================================================
tab1, tab2 = st.tabs(["🔥 LIVE SCANNER", "📊 BACKTEST"])

# ================= LIVE =================
with tab1:

    if st.button("RUN LIVE SCAN"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, now.date()) for s in stocks]

            for f in futures:
                r = f.result()
                if r:
                    results.append(r[-1])

        df = pd.DataFrame(results)

        if not df.empty:
            st.dataframe(df)

            st.download_button(
                "📥 LIVE EXCEL",
                to_excel(df),
                file_name=f"LIVE_{now.strftime('%Y%m%d_%H%M')}.xlsx"
            )
        else:
            st.warning("NO SIGNALS")

# ================= BACKTEST =================
with tab2:

    d = st.date_input("Select Date", now.date()-timedelta(days=1))

    if st.button("RUN BACKTEST"):

        results = []

        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(engine, s, data, d) for s in stocks]

            for f in futures:
                r = f.result()
                if r:
                    results.extend(r)

        df = pd.DataFrame(results)

        if not df.empty:

            st.dataframe(df)

            wins = len(df[df['STATUS']=="TARGET"])
            losses = len(df[df['STATUS']=="SL"])

            st.success(f"WINS: {wins} | LOSSES: {losses}")

            st.download_button(
                "📥 BACKTEST EXCEL",
                to_excel(df),
                file_name=f"BACKTEST_{d}.xlsx"
            )
        else:
            st.warning("NO DATA")
