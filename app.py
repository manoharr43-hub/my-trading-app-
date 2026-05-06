# ==========================================
# 🚀 NSE AI PRO V120 ULTRA - FULL SYSTEM
# (OLD CODE TOUCH చేయాల్సిన అవసరం లేదు)
# ==========================================

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
st.set_page_config(page_title="🚀 NSE AI PRO V120 ULTRA", layout="wide")

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

st.title("🚀 NSE AI PRO V120 ULTRA SYSTEM")
st.caption(now_ist().strftime("%d-%b-%Y %H:%M:%S IST"))

# =============================
# NSE 200 LIST
# =============================
stocks = [
"ABB","ACC","AIAENG","APLAPOLLO","AUBANK","AARTIIND","ABBOTINDIA","ADANIENSOL","ADANIENT","ADANIGREEN",
"ADANIPORTS","ADANIPOWER","ATGL","ABCAPITAL","ABFRL","ALKEM","AMBUJACEM","APOLLOHOSP","APOLLOTYRE","ASHOKLEY",
"ASIANPAINT","ASTRAL","AUROPHARMA","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BAJAJHLDNG","BALKRISIND","BANDHANBNK",
"BANKBARODA","BANKINDIA","BATAINDIA","BEL","BERGEPAINT","BHARATFORG","BHEL","BPCL","BHARTIARTL","BIOCON",
"BOSCHLTD","BRITANNIA","BSOFT","CANBK","CGPOWER","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL",
"CONCOR","COROMANDEL","CROMPTON","CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB",
"DIXON","DLF","DRREDDY","EICHERMOT","ESCORTS","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK",
"GMRINFRA","GODREJCP","GODREJPROP","GRASIM","GUJGASLTD","HAL","HAVELLS","HCLTECH","HDFCBANK","HDFCLIFE",
"HEROMOTOCO","HINDALCO","HINDCOPPER","HINDPETRO","HINDUNILVR","ICICIBANK","ICICIGI","ICICIPRULI","IDFCFIRSTB","IDFC",
"IEX","IGL","INDHOTEL","INDIACEM","INDIAMART","INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC",
"IRCTC","IRFC","ITC","JINDALSTEL","JSWENERGY","JSWSTEEL","JUBLFOOD","KOTAKBANK","KPITTECH","LTFH",
"LT","LTIM","LTTS","LICHSGFIN","LICI","LUPIN","M&M","M&MFIN","MANAPPURAM","MARICO",
"MARUTI","MAXHEALTH","METROPOLIS","MFSL","MGL","MPHASIS","MRF","MUTHOOTFIN","NATIONALUM","NAVINFLUOR",
"NESTLEIND","NMDC","NTPC","OBEROIRLTY","ONGC","PAGEIND","PAYTM","PEL","PERSISTENT","PETRONET",
"PFC","PIDILITIND","PIIND","PNB","POLYCAB","POONAWALLA","POWERGRID","PRESTIGE","PVRINOX","RECLTD",
"RELIANCE","SAIL","SBICARD","SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SRF","SUNPHARMA",
"SUNTV","SYNGENE","TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TCS","TECHM",
"TITAN","TORNTPHARM","TRENT","TVSMOTOR","ULTRACEMCO","UBL","UPL","VBL","VEDL","VOLTAS",
"WIPRO","YESBANK","ZEEL","ZOMATO"
]

# =============================
# INDICATORS
# =============================
def add_indicators(df):
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

    df['RSI'] = 100 - (100 / (1 + gain/(loss+1e-9)))
    df['VolAvg'] = df['Volume'].rolling(20).mean()

    return df

# =============================
# DATA LOAD
# =============================
@st.cache_data(ttl=120)
def load_data():
    tickers = [s+".NS" for s in stocks]
    d5 = yf.download(tickers, period="30d", interval="5m", group_by="ticker", progress=False)
    d15 = yf.download(tickers, period="30d", interval="15m", group_by="ticker", progress=False)
    return d5, d15

data_5m, data_15m = load_data()

# =============================
# SCANNER
# =============================
def scan_stock(s):
    try:
        df5 = add_indicators(data_5m[s+".NS"].dropna())
        df15 = add_indicators(data_15m[s+".NS"].dropna())

        if len(df5) < 50:
            return None

        row = df5.iloc[-1]

        trend15 = "UP" if df15.iloc[-1]['Close'] > df15.iloc[-1]['EMA20'] else "DOWN"

        vol_bo = row['Volume'] > row['VolAvg'] * 1.5
        candle = abs(row['Close'] - row['Open']) > row['ATR'] * 0.5

        prev_high = df5['High'].rolling(20).max().iloc[-2]
        prev_low = df5['Low'].rolling(20).min().iloc[-2]

        breakout_buy = row['Close'] > prev_high
        breakout_sell = row['Close'] < prev_low

        score = 0
        if row['Close'] > row['VWAP']: score+=1
        if row['RSI'] > 55: score+=1
        if trend15=="UP": score+=1
        if vol_bo: score+=1
        if candle: score+=1

        signal=None

        if score>=4 and breakout_buy and trend15=="UP":
            signal="BUY"
        elif score>=4 and breakout_sell and trend15=="DOWN":
            signal="SELL"

        if not signal:
            return None

        return {
            "Stock": s,
            "Signal": signal,
            "Price": round(row['Close'],2),
            "Score": score
        }

    except:
        return None

# =============================
# BACKTEST
# =============================
def run_backtest():
    trades=[]

    for s in stocks:
        try:
            df = add_indicators(data_5m[s+".NS"].dropna())

            for i in range(30,len(df)-1):
                row=df.iloc[i]
                nxt=df.iloc[i+1]

                if row['RSI']>55:
                    entry=row['Close']
                    if nxt['High']>entry*1.01:
                        trades.append(1)
                    else:
                        trades.append(-1)
        except:
            continue

    return trades

# =============================
# UI
# =============================
tab1,tab2=st.tabs(["LIVE SCANNER","BACKTEST"])

with tab1:
    if st.button("🚀 SCAN NSE 200"):
        with ThreadPoolExecutor(max_workers=25) as ex:
            res=[r for r in ex.map(scan_stock,stocks) if r]

        if res:
            st.dataframe(pd.DataFrame(res))
        else:
            st.warning("No signals")

with tab2:
    if st.button("📊 RUN BACKTEST"):
        trades=run_backtest()

        if trades:
            winrate=round((trades.count(1)/len(trades))*100,2)
            st.metric("WinRate",f"{winrate}%")
        else:
            st.warning("No trades")
