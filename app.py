import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V120 ULTRA CLEAN", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V120 ULTRA CLEAN SYSTEM")
st.subheader(f"{now.strftime('%d-%b-%Y %H:%M:%S')} IST")

# =============================
# NSE 200 STOCKS
# =============================
stocks = [
"ABB","ACC","ADANIENSOL","ADANIENT","ADANIGREEN","ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL",
"ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY","ASIANPAINT","ASTRAL","AUROPHARMA","AUBANK","AVANTIFEED",
"AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALKRISIND","BANDHANBNK","BANKBARODA","BANKINDIA","BATAINDIA",
"BEL","BERGEPAINT","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON","BOSCHLTD","BRITANNIA","BSOFT",
"CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR","COROMANDEL","CROMPTON",
"CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB","DIXON","DLF","DRREDDY",
"EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK","GMRINFRA","GODREJCP","GODREJPROP",
"GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER",
"HINDPETRO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI","IDFCFIRSTB","IDFC","IEX","IGL","INDHOTEL",
"INDIACEM","INDIAMART","INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC","IRCTC","IRFC","ITC",
"JINDALSTEL","JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK","KPITTECH","L&TFH","LT","LTIM","LTTS",
"LICHSGFIN","LICI","LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO","MARUTI","MAHABANK","MAXHEALTH",
"METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NAVINFLUOR","NESTLEIND","NMDC",
"NTPC","OBEROIRLTY","ONGC","PAGEIND","PAYTM","PEL","PERSISTENT","PETRONET","PFC","PIDILITIND",
"PIIND","PNB","POLYCAB","POONAWALLA","POWERGRID","PRESTIGE","PVRINOX","RECLTD","RELIANCE","SAIL",
"SBICARD","SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA","SUNTV","SYNGENE",
"TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM","TITAN","TORNTPHARM",
"TRENT","TVSMOTOR","ULTRACEMCO","UBL","UPL","VBL","VEDL","VOLTAS","WIPRO","YESBANK","ZEEL","ZOMATO"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    if df.empty:
        return df

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Date'] = df.index.date
    df['PV'] = df['Close'] * df['Volume']
    df['VWAP'] = df.groupby('Date')['PV'].cumsum() / df.groupby('Date')['Volume'].cumsum()

    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    df['VolAvg'] = df['Volume'].rolling(20).mean()
    df['RVOL'] = df['Volume'] / (df['VolAvg'] + 1e-9)

    return df

# =============================
# DATA FETCH
# =============================
@st.cache_data(ttl=60)
def fetch(interval):
    tickers = [s + ".NS" for s in stocks]
    return yf.download(tickers, period="5d", interval=interval, group_by="ticker", progress=False)

data5 = fetch("5m")
data15 = fetch("15m")

# =============================
# SIGNAL ENGINE
# =============================
def scan(s):
    try:
        df5 = add_indicators(data5[s+".NS"].dropna())
        df15 = add_indicators(data15[s+".NS"].dropna())

        if len(df5) < 30:
            return None

        last = df5.iloc[-1]

        trend = "UP" if df15.iloc[-1]['Close'] > df15.iloc[-1]['EMA20'] else "DOWN"

        # Filters
        body = abs(last['Close'] - last['Open'])
        rng = last['High'] - last['Low']
        strong = body > (0.5 * rng)

        slope = df15['EMA20'].diff().iloc[-1]

        score = 0
        if last['Close'] > last['VWAP']: score += 1
        if last['RSI'] > 55: score += 1
        if last['RVOL'] > 1.5: score += 1
        if strong: score += 1
        if slope > 0: score += 1

        signal = None
        if score >= 3 and trend == "UP":
            signal = "BUY"
        elif score >= 3 and trend == "DOWN":
            signal = "SELL"

        if not signal:
            return None

        trade_type = "BREAKOUT" if last['Close'] > df5['High'].rolling(20).max().iloc[-2] else "PULLBACK"

        entry = round(last['Close'], 2)
        sl_pts = last['ATR'] * 1.5
        sl = round(entry - sl_pts if signal == "BUY" else entry + sl_pts, 2)
        tgt = round(entry + sl_pts * 2.5 if signal == "BUY" else entry - sl_pts * 2.5, 2)

        return {
            "STOCK": s,
            "SIGNAL": signal,
            "TYPE": trade_type,
            "PRICE": entry,
            "SL": sl,
            "TARGET": tgt,
            "SCORE": score
        }

    except:
        return None

# =============================
# BACKTEST
# =============================
def backtest(s):
    try:
        df = add_indicators(data5[s+".NS"].dropna())
        trades = []

        for i in range(30, len(df)-10):
            row = df.iloc[i]

            if row['Close'] > row['VWAP'] and row['RSI'] > 55:
                entry = row['Close']
                sl = entry - row['ATR'] * 1.5
                tgt = entry + row['ATR'] * 2.5

                future = df.iloc[i:i+10]

                for _, f in future.iterrows():
                    if f['Low'] <= sl:
                        trades.append("LOSS")
                        break
                    if f['High'] >= tgt:
                        trades.append("WIN")
                        break

        if not trades:
            return None

        winrate = round((trades.count("WIN") / len(trades)) * 100, 2)

        return {"STOCK": s, "TRADES": len(trades), "WINRATE": winrate}

    except:
        return None

# =============================
# UI
# =============================
tab1, tab2 = st.tabs(["🔴 LIVE SCANNER", "📊 BACKTEST"])

# LIVE
with tab1:
    if st.button("🚀 Scan Market"):
        with ThreadPoolExecutor(max_workers=20) as exe:
            results = [r for r in exe.map(scan, stocks) if r]

        if results:
            df = pd.DataFrame(results).sort_values(by="SCORE", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No signals")

# BACKTEST
with tab2:
    if st.button("📊 Run Backtest"):
        with ThreadPoolExecutor(max_workers=20) as exe:
            results = [r for r in exe.map(backtest, stocks) if r]

        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)
            st.metric("Average Winrate", f"{df['WINRATE'].mean():.2f}%")
        else:
            st.warning("No backtest data")
