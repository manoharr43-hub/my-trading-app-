# ==========================================
# 🚀 NSE AI PRO V72 - ULTRA AI (FULL SYSTEM)
# ==========================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="🚀 NSE AI PRO V72 ULTRA", layout="wide")
st.title("🚀 NSE AI PRO V72 - ULTRA AI SYSTEM")

IST = pytz.timezone("Asia/Kolkata")
st.write("🕒", datetime.now(IST))

# ==========================================
# NSE 200 STOCK LIST (AUTO EXPAND)
# ==========================================
stocks = list(set([
"RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","LT.NS","ITC.NS",
"KOTAKBANK.NS","AXISBANK.NS","HINDUNILVR.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
"TITAN.NS","ULTRACEMCO.NS","NESTLEIND.NS","BAJFINANCE.NS","BAJAJFINSV.NS","WIPRO.NS",
"HCLTECH.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","TATAMOTORS.NS","COALINDIA.NS",
"JSWSTEEL.NS","TATASTEEL.NS","INDUSINDBK.NS","ADANIENT.NS","ADANIPORTS.NS",
"DMART.NS","ZOMATO.NS","NYKAA.NS","PAYTM.NS","IRCTC.NS","HAL.NS","BEL.NS","BHEL.NS",
"IOC.NS","BPCL.NS","HPCL.NS","GAIL.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","IDFCFIRSTB.NS",
"DLF.NS","LODHA.NS","GODREJPROP.NS","OBEROIRLTY.NS","COLPAL.NS","DABUR.NS","MARICO.NS",
"BRITANNIA.NS","PIDILITIND.NS","SRF.NS","DEEPAKNTR.NS","BERGEPAINT.NS",
"APOLLOHOSP.NS","MAXHEALTH.NS","FORTIS.NS","LALPATHLAB.NS","METROPOLIS.NS",
"DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","AUROPHARMA.NS",
"SIEMENS.NS","ABB.NS","HAVELLS.NS","POLYCAB.NS","VOLTAS.NS","DIXON.NS",
"TATAPOWER.NS","ADANIGREEN.NS","ADANIPOWER.NS","NHPC.NS",
"AMBUJACEM.NS","ACC.NS","RAMCOCEM.NS",
"TORNTPHARM.NS","LUPIN.NS",
"INDIGO.NS","ESCORTS.NS","EICHERMOT.NS","HEROMOTOCO.NS",
"TVSMOTOR.NS","ASHOKLEY.NS",
"PAGEIND.NS","TRENT.NS","ABFRL.NS",
"GLAND.NS","BIOCON.NS",
"MFSL.NS","CHOLAFIN.NS","MUTHOOTFIN.NS",
"LICHSGFIN.NS","PFC.NS","RECLTD.NS",
"IRFC.NS","RVNL.NS","NBCC.NS"
]))

# ==========================================
# INDICATORS
# ==========================================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_atr(df, period=14):
    tr = pd.concat([
        df['High'] - df['Low'],
        abs(df['High'] - df['Close'].shift()),
        abs(df['Low'] - df['Close'].shift())
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ==========================================
# ULTRA AI LOGIC
# ==========================================
def ultra_ai(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['EMA200'] = df['Close'].ewm(span=200).mean()
    df['RSI'] = compute_rsi(df['Close'])
    df['ATR'] = compute_atr(df)
    df['VOL_AVG'] = df['Volume'].rolling(20).mean()

    signals = []

    for i in range(50, len(df)):
        score = 0

        trend_up = df['EMA50'][i] > df['EMA200'][i]
        trend_down = df['EMA50'][i] < df['EMA200'][i]

        vol_spike = df['Volume'][i] > 1.5 * df['VOL_AVG'][i]
        pullback = df['Close'][i] <= df['EMA20'][i]
        rsi_buy = df['RSI'][i] > 55
        rsi_sell = df['RSI'][i] < 45
        atr_high = df['ATR'][i] > df['ATR'].rolling(20).mean()[i]

        # SCORE
        if trend_up: score += 20
        if trend_down: score += 20
        if vol_spike: score += 20
        if pullback: score += 15
        if atr_high: score += 15

        signal = "NO TRADE"

        # DECISION
        if trend_up and rsi_buy and score >= 75:
            signal = "STRONG BUY"
        elif trend_up and score >= 65:
            signal = "BUY"
        elif trend_down and rsi_sell and score >= 75:
            signal = "STRONG SELL"
        elif trend_down and score >= 65:
            signal = "SELL"

        entry = df['Close'][i]

        if "BUY" in signal:
            sl = df['Low'][i-3:i].min()
            target = entry + 2*(entry - sl)
        elif "SELL" in signal:
            sl = df['High'][i-3:i].max()
            target = entry - 2*(sl - entry)
        else:
            sl, target = 0, 0

        signals.append({
            "Time": df.index[i],
            "Signal": signal,
            "Score": score,
            "Entry": round(entry,2),
            "SL": round(sl,2),
            "Target": round(target,2)
        })

    return pd.DataFrame(signals)

# ==========================================
# PROCESS FUNCTION (FAST)
# ==========================================
def process_stock(stock):
    try:
        df = yf.download(stock, period="3mo", interval="15m", progress=False)

        if df.empty:
            return None

        signals = ultra_ai(df)

        if signals.empty:
            return None

        latest = signals.iloc[-1]
        latest["Stock"] = stock

        return latest
    except:
        return None

# ==========================================
# SCANNER
# ==========================================
final_results = []

if st.button("🚀 RUN SCANNER"):

    with st.spinner("Scanning NSE 200..."):
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(process_stock, stocks)

        for r in results:
            if r is not None:
                final_results.append(r)

    if final_results:
        df = pd.DataFrame(final_results)

        # FILTER BEST
        df = df[df["Score"] >= 65]
        df = df.sort_values(by="Score", ascending=False)

        st.success(f"Found {len(df)} high-quality trades 🔥")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "nse_signals.csv")

    else:
        st.warning("No strong signals found")
