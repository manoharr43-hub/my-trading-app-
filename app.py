import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz, io
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚀 NSE AI PRO V45", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI PRO V45 - LIVE + BACKTEST + BIG MOVE")
st.write(f"🕒 Market Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================
# STOCK LIST
# =============================
stocks = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK","LT","ITC","HINDUNILVR",
          "BAJFINANCE","TITAN","MARUTI","TATAMOTORS","ADANIENT","ADANIPORTS","WIPRO","HCLTECH","LTIM",
          "BEL","DLF","INDUSINDBK","PNB","BANKBARODA","CANBK","YESBANK","ZOMATO"]

# =============================
# INDICATORS
# =============================
def indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    
    df['ATR'] = tr.rolling(14).mean()
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

# =============================
# FETCH
# =============================
@st.cache_data(ttl=60)
def get_data():
    return yf.download([s+".NS" for s in stocks], period="5d", interval="5m", group_by="ticker")

data = get_data()

# =============================
# EXCEL EXPORT
# =============================
def excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔴 LIVE", "📊 PULLBACK BACKTEST", "🔥 BIG MOVE BACKTEST"])

# =============================
# LIVE SCAN
# =============================
with tab1:
    if st.button("RUN LIVE"):
        res = []

        for s in stocks:
            try:
                df = data[s+".NS"].dropna()
                df = indicators(df)

                last = df.iloc[-1]
                dist = abs(last['Close'] - last['EMA20']) / last['EMA20']

                if dist < 0.004:
                    signal = None

                    if last['Close'] > last['VWAP']:
                        signal = "BUY"
                    elif last['Close'] < last['VWAP']:
                        signal = "SELL"

                    if signal:
                        entry = round(last['Close'],2)

                        res.append({
                            "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                            "STOCK": s,
                            "SIGNAL": signal,
                            "ENTRY": entry,
                            "SL": round(entry - last['ATR']*1.5 if signal=="BUY" else entry + last['ATR']*1.5,2),
                            "TGT": round(entry + last['ATR']*3 if signal=="BUY" else entry - last['ATR']*3,2),
                            "BIG": "🔥" if last['Volume'] > last['VolAvg']*2 else "-"
                        })
            except:
                continue

        if res:
            df = pd.DataFrame(res)
            st.dataframe(df, use_container_width=True)
            st.download_button("Download", excel(df), "live.xlsx")
        else:
            st.warning("No signals")

# =============================
# PULLBACK BACKTEST
# =============================
with tab2:
    date = st.date_input("Select Date", now.date()-timedelta(days=1))

    if st.button("RUN PULLBACK BT"):
        logs = []

        for s in stocks:
            try:
                df = data[s+".NS"].dropna()
                df.index = df.index.tz_convert(IST)

                df = df[df.index.date == date]
                df = indicators(df)

                for i in range(20, len(df)):
                    row = df.iloc[i]
                    dist = abs(row['Close'] - row['EMA20']) / row['EMA20']

                    if dist < 0.004:
                        sig = None
                        if row['Close'] > row['VWAP']:
                            sig = "BUY"
                        elif row['Close'] < row['VWAP']:
                            sig = "SELL"

                        if sig:
                            entry = row['Close']

                            logs.append({
                                "TIME": df.index[i].strftime('%H:%M'),
                                "STOCK": s,
                                "TYPE": sig,
                                "PRICE": entry
                            })
            except:
                continue

        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df)
            st.download_button("Download", excel(df), "pullback.xlsx")

# =============================
# BIG MOVE BACKTEST
# =============================
with tab3:
    date2 = st.date_input("Big Move Date", now.date()-timedelta(days=1))

    if st.button("RUN BIG MOVE"):
        logs = []

        for s in stocks:
            try:
                df = data[s+".NS"].dropna()
                df.index = df.index.tz_convert(IST)

                df = df[df.index.date == date2]
                df = indicators(df)

                for i in range(30, len(df)):
                    row = df.iloc[i]

                    body = abs(row['Close'] - row['Open'])
                    rng = row['High'] - row['Low']

                    breakout_up = row['Close'] > df['High'].iloc[i-10:i].max()
                    breakout_dn = row['Close'] < df['Low'].iloc[i-10:i].min()

                    vol = row['Volume'] > row['VolAvg']*2

                    if body > rng*0.6 and vol:
                        if breakout_up:
                            logs.append({"TIME":df.index[i].strftime('%H:%M'),"STOCK":s,"TYPE":"BUY 🚀"})
                        elif breakout_dn:
                            logs.append({"TIME":df.index[i].strftime('%H:%M'),"STOCK":s,"TYPE":"SELL 🔻"})

            except:
                continue

        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df)
            st.download_button("Download", excel(df), "bigmove.xlsx")
