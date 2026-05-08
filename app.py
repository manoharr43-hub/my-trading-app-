import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import io

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="🚀 NSE AI V60 PRO", layout="wide")

IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("🚀 NSE AI V60 PRO - FULL MARKET CONTROL PANEL")

st.markdown(f"🕒 LIVE TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# NIFTY 50 STOCKS
# =========================
nifty50 = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","AXISBANK",
    "ITC","LT","BHARTIARTL","KOTAKBANK","HCLTECH","WIPRO","TECHM",
    "SUNPHARMA","TITAN","MARUTI","ONGC","NTPC","POWERGRID","COALINDIA",
    "BAJFINANCE","BAJAJFINSV","ASIANPAINT","NESTLEIND","BRITANNIA",
    "ULTRACEMCO","TATAMOTORS","M&M","HINDUNILVR","JSWSTEEL"
]

# =========================
# DATA FUNCTION
# =========================
def get_stock_data(symbol):
    try:
        df = yf.download(symbol+".NS", period="2d", interval="15m")
        if len(df) < 2:
            return None

        last = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]

        change = last - prev
        pct = (change / prev) * 100

        return {
            "STOCK": symbol,
            "PRICE": round(last,2),
            "CHANGE": round(change,2),
            "PERCENT": round(pct,2),
            "TREND": "POSITIVE" if change > 0 else "NEGATIVE"
        }

    except:
        return None

# =========================
# MARKET SCANNER
# =========================
def scan_market():

    results = []

    for s in nifty50:
        data = get_stock_data(s)
        if data:
            results.append(data)

    return pd.DataFrame(results)

# =========================
# SCENARIO ENGINE
# =========================
def market_scenario(df):

    avg = df["PERCENT"].mean()

    if avg > 0:
        return "🟢 BULLISH MARKET - BUY SIDE ACTIVE"
    else:
        return "🔴 BEARISH MARKET - SELL SIDE ACTIVE"

# =========================
# TOP PICKS
# =========================
def top_picks(df):

    pos = df[df["TREND"]=="POSITIVE"].sort_values("PERCENT", ascending=False).head(5)
    neg = df[df["TREND"]=="NEGATIVE"].sort_values("PERCENT").head(5)

    return pos, neg

# =========================
# EXCEL EXPORT
# =========================
def to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="NIFTY_REPORT")

    return output.getvalue()

# =========================
# UI
# =========================
tab1, tab2 = st.tabs(["📊 NIFTY MARKET VIEW", "📈 FULL REPORT"])

# =========================
# TAB 1 - MARKET VIEW
# =========================
with tab1:

    if st.button("RUN MARKET SCAN"):

        df = scan_market()

        if not df.empty:

            st.subheader("📊 MARKET SCENARIO")
            st.info(market_scenario(df))

            pos, neg = top_picks(df)

            st.subheader("🟢 TOP POSITIVE STOCKS")
            st.dataframe(pos)

            st.subheader("🔴 TOP NEGATIVE STOCKS")
            st.dataframe(neg)

        else:
            st.warning("NO DATA FOUND")

# =========================
# TAB 2 - FULL REPORT + EXCEL
# =========================
with tab2:

    if st.button("GENERATE FULL REPORT"):

        df = scan_market()

        if not df.empty:

            st.subheader("📊 COMPLETE NIFTY REPORT")
            st.dataframe(df)

            st.download_button(
                "📥 DOWNLOAD EXCEL REPORT",
                to_excel(df),
                file_name="NSE_MARKET_REPORT.xlsx"
            )

        else:
            st.warning("NO DATA FOUND")
