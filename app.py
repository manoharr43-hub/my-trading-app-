import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timedelta

# Page Config
st.set_page_config(page_title="NSE AI PRO V69 - ELITE", layout="wide")

# --- HEADER ---
st.title("🚀 NSE AI PRO V69 - ELITE PRO")
st.subheader("Live Scanner & Backtesting Dashboard")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Configuration")
tickers_input = st.sidebar.text_area("Enter Stock Symbols (NSE)", "LICHSGFIN.NS, TATACHEM.NS, BIOCON.NS, SAIL.NS")
tickers = [t.strip() for t in tickers_input.split(",")]

period = st.sidebar.selectbox("Backtest Period", ["1mo", "3mo", "6mo", "1y"])
interval = st.sidebar.selectbox("Interval", ["15m", "30m", "1h", "1d"])

# --- FUNCTIONS ---
def get_data(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval)
        if df.empty: return None
        # Technical Indicators
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        return df
    except:
        return None

def run_backtest(df):
    # Strategy: Buy when EMA 9 crosses above EMA 21
    df['Signal'] = 0
    df.loc[df['EMA_9'] > df['EMA_21'], 'Signal'] = 1
    df['Position'] = df['Signal'].diff()
    
    trades = []
    buy_price = 0
    
    for i in range(len(df)):
        if df['Position'].iloc[i] == 1: # Buy
            buy_price = df['Close'].iloc[i]
        elif df['Position'].iloc[i] == -1 and buy_price != 0: # Sell
            sell_price = df['Close'].iloc[i]
            profit = sell_price - buy_price
            trades.append(profit)
            buy_price = 0
            
    total_trades = len(trades)
    win_trades = len([p for p in trades if p > 0])
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(trades)
    
    return total_trades, win_rate, total_pnl

# --- MAIN TABBS ---
tab1, tab2 = st.tabs(["🔍 Live Scanner", "📊 Backtest Report"])

with tab1:
    if st.button("RUN LIVE SCAN"):
        results = []
        for stock in tickers:
            df = get_data(stock, "5d", interval)
            if df is not None:
                last_row = df.iloc[-1]
                signal = "BUY" if last_row['EMA_9'] > last_row['EMA_21'] else "WAIT"
                results.append({
                    "STOCK": stock.replace(".NS", ""),
                    "TIME": datetime.now().strftime("%H:%M"),
                    "SIGNAL": signal,
                    "ENTRY": round(last_row['Close'], 2),
                    "SL": round(last_row['EMA_21'], 2),
                    "RSI": round(last_row['RSI'], 2)
                })
        
        st.table(pd.DataFrame(results))

with tab2:
    st.write("### Strategy Performance (Last 30 Days)")
    bt_results = []
    for stock in tickers:
        df = get_data(stock, period, interval)
        if df is not None:
            trades, win_rate, pnl = run_backtest(df)
            bt_results.append({
                "Stock": stock.replace(".NS", ""),
                "Total Trades": trades,
                "Win Rate %": f"{win_rate:.2f}%",
                "Total PnL": round(pnl, 2)
            })
    
    st.dataframe(pd.DataFrame(bt_results), use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.caption("Developed by Manohar | Variety Motors Tech")
