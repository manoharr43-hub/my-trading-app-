import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import os
import time

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V19 - BACKTEST FOLDER", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V19 - ULTIMATE DASHBOARD")
st.write(f"🕒 **System Sync (IST):** {current_time}")

# =============================
# STOCK SECTORS
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT"],
    "ENERGY": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL"],
    "OTHERS": ["ITC", "LT", "BAJFINANCE", "TATASTEEL", "BHARTIARTL"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# SAFE HISTORY LOADER
# =============================
def safe_history(ticker, period="2d", interval="15m", retries=3, delay=2):
    for i in range(retries):
        try:
            df = yf.Ticker(ticker + ".NS").history(period=period, interval=interval)
            if not df.empty:
                return df
        except Exception:
            time.sleep(delay)
    return None

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['CumVol'] = df['Volume'].groupby(df.index.date).cumsum()
    df['CumPV'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum()
    df['VWAP'] = df['CumPV'] / df['CumVol']
    
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 2.5)
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    return df

# =============================
# BACKTEST SAVE + SIDEBAR LIST
# =============================
def save_backtest_report(report_df, folder="backtests"):
    os.makedirs(folder, exist_ok=True)
    file_name = f"{folder}/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    report_df.to_csv(file_name, index=False)
    return file_name

def show_backtest_folder(folder="backtests"):
    st.sidebar.header("📂 Backtest Folder")
    if os.path.exists(folder):
        files = os.listdir(folder)
        if files:
            for f in files:
                st.sidebar.write(f"📄 {f}")
        else:
            st.sidebar.warning("No backtest files yet.")
    else:
        st.sidebar.warning("Backtest folder not created.")

# =============================
# UI - BACKTEST TAB
# =============================
if st.button("📈 GENERATE BACKTEST REPORT"):
    back_logs = []
    with st.spinner("Fetching Historical Back Data..."):
        for s in all_stocks:
            df_b = safe_history(s, period="2mo", interval="1d")
            if df_b is not None:
                df_b = add_indicators(df_b)
                hits = df_b[(df_b['Big_Player']) | (df_b['Bull_Rev'])]
                for idx, row in hits.iterrows():
                    back_logs.append({
                        "DATE": idx.strftime('%Y-%m-%d'),
                        "STOCK": s,
                        "ENTRY PRICE": round(row['Close'], 2),
                        "STOPLOSS": round(row['Close'] * 0.99, 2),
                        "TARGET": round(row['Close'] * 1.02, 2),
                        "SIGNAL TYPE": "🐋 BIG PLAYER" if row['Big_Player'] else "🔄 REVERSAL"
                    })
    
    if back_logs:
        report_df = pd.DataFrame(back_logs)
        st.success(f"మొత్తం {len(report_df)} ఎంట్రీలు దొరికాయి.")
        st.dataframe(report_df, use_container_width=True)
        
        # ✅ Save CSV + Show Folder
        save_backtest_report(report_df)
        show_backtest_folder()
    else:
        st.warning("గత 30 రోజుల్లో సిగ్నల్స్ ఏవీ దొరకలేదు.")
