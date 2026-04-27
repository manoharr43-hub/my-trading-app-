import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
from io import BytesIO

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V11", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V11 - INSTITUTIONAL SYSTEM")
st.write(f"🕒 IST Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# =============================
# NSE STOCK LIST (EXPANDED)
# =============================
@st.cache_data(ttl=3600)
def get_nse_stocks():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    return df['SYMBOL'].tolist()

stocks = get_nse_stocks()

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=300)
def get_data(symbol, interval="5m", period="5d"):
    try:
        df = yf.Ticker(symbol + ".NS").history(period=period, interval=interval)
        if df.empty:
            return None

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(IST)
        else:
            df.index = df.index.tz_convert(IST)

        return df.dropna()
    except:
        return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()

    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()

    return df

# =============================
# AI SCORE
# =============================
def ai_score(df):
    last = df.iloc[-1]
    score = 0

    if last['EMA20'] > last['EMA50']: score += 25
    if 50 < last['RSI'] < 70: score += 15
    if last['Close'] > last['VWAP']: score += 20
    if last['MACD'] > last['Signal']: score += 20
    if last['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]: score += 20

    return score

# =============================
# SMART MONEY
# =============================
def smart_money(df):
    last = df.iloc[-1]
    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]

    move = abs(last['Close'] - last['Open']) / last['Open'] * 100

    if last['Volume'] > avg_vol * 2 and move > 0.5:
        if last['Close'] > last['VWAP']:
            return "🔥 BIG BUYER"
        else:
            return "💀 BIG SELLER"
    return ""

# =============================
# SIGNAL
# =============================
def signal(score):
    if score >= 80: return "🚀 STRONG BUY"
    elif score >= 60: return "BUY"
    elif score <= 20: return "💀 STRONG SELL"
    elif score <= 40: return "SELL"
    else: return "WAIT"

# =============================
# EXCEL
# =============================
def convert_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================
# UI TABS
# =============================
tab1, tab2 = st.tabs(["🔍 LIVE SCANNER", "📊 BACKTEST"])

# =============================
# LIVE SCANNER
# =============================
with tab1:

    if st.button("🚀 RUN FULL SCAN"):

        results = []

        for s in stocks[:200]:  # limit for speed

            df5 = get_data(s, "5m")
            df15 = get_data(s, "15m")
            df1h = get_data(s, "1h")
            dfd = get_data(s, "1d", "3mo")

            if None in [df5, df15, df1h, dfd]:
                continue

            df5, df15, df1h, dfd = map(add_indicators, [df5, df15, df1h, dfd])

            score = (
                ai_score(df5) * 0.3 +
                ai_score(df15) * 0.3 +
                ai_score(df1h) * 0.2 +
                ai_score(dfd) * 0.2
            )

            sig = signal(score)

            if "STRONG" not in sig:
                continue

            price = df5['Close'].iloc[-1]
            atr = df5['ATR'].iloc[-1]

            entry = round(price,2)
            target = round(entry + atr * 1.5,2)
            sl = round(entry - atr,2)

            results.append({
                "STOCK": s,
                "PRICE": entry,
                "SIGNAL": sig,
                "SMART": smart_money(df5),
                "TARGET": target,
                "SL": sl,
                "SCORE": round(score,1)
            })

        if results:
            df = pd.DataFrame(results).sort_values("SCORE", ascending=False)
            st.dataframe(df, use_container_width=True)
            st.success(f"{len(df)} Strong Trades Found")

        else:
            st.warning("No signals")

# =============================
# BACKTEST
# =============================
with tab2:

    date = st.date_input("Select Date")

    if st.button("📈 RUN BACKTEST"):

        logs, wins, total = [], 0, 0

        for s in stocks[:100]:

            df = get_data(s, "5m", "7d")
            if df is None: continue

            df = add_indicators(df)
            df = df[df.index.date == date]

            for i in range(20, len(df)-1):

                sc = ai_score(df.iloc[:i+1])
                sig = signal(sc)

                entry = df.iloc[i]['Close']
                next_p = df.iloc[i+1]['Close']

                if "BUY" in sig:
                    res = "WIN" if next_p > entry else "LOSS"
                elif "SELL" in sig:
                    res = "WIN" if next_p < entry else "LOSS"
                else:
                    continue

                wins += (res == "WIN")
                total += 1

                logs.append([s, entry, next_p, res])

        if logs:
            df = pd.DataFrame(logs, columns=["Stock","Entry","Next","Result"])
            acc = (wins/total)*100

            st.dataframe(df)
            st.metric("Accuracy", f"{acc:.2f}%")

            st.download_button("Download Excel", convert_excel(df))
