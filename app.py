import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V23.7 HQ", layout="wide")
st.title("🚀 NSE AI PRO V23.7 - HQ Stable System")

# =============================
# BACKTEST FOLDER CONFIG
# =============================
BACKTEST_DIR = "backtests"
os.makedirs(BACKTEST_DIR, exist_ok=True)

# =============================
# STOCK LIST
# =============================
stocks = ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK",
          "INFY","TCS","HCLTECH","WIPRO","TECHM",
          "MARUTI","M&M","TATAMOTORS","HEROMOTOCO",
          "RELIANCE","ONGC","TATASTEEL","HINDALCO"]

timeframe = st.sidebar.selectbox("Interval", ["5m","15m","30m","1h"])
sl_pct = st.sidebar.slider("Stop Loss %",0.5,5.0,1.0)/100
tgt_pct = st.sidebar.slider("Target %",1.0,10.0,2.0)/100

# =============================
# SAFE DATA LOADER
# =============================
@st.cache_data(ttl=60)
def load_data(stock, interval, period="5d"):
    try:
        df = yf.Ticker(stock+".NS").history(period=period, interval=interval)
        return df
    except Exception:
        return pd.DataFrame()

# =============================
# INDICATORS
# =============================
def add_indicators(df):
    if df.empty: return df
    df = df.copy()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    return df

# =============================
# SIGNAL ENGINE
# =============================
def get_signals(df, stock):
    df = add_indicators(df)
    signals=[]
    if len(df)<30: return signals
    for i in range(30,len(df)):
        row=df.iloc[i]; prev=df.iloc[i-1]
        price=float(row["Close"]); sig=None
        if row["Volume"]>row["Volume"].rolling(20).mean().iloc[i]*2.5:
            sig="🔥 BIG BUY" if row["Close"]>row["Open"] else "💀 BIG SELL"
        elif prev["Close"]<row["EMA20"] and row["Close"]>row["EMA20"]:
            if row["EMA20"]>row["EMA50"]: sig="🟢 BULLISH"
        elif prev["Close"]>row["EMA20"] and row["Close"]<row["EMA20"]:
            if row["EMA20"]<row["EMA50"]: sig="🔴 BEARISH"
        if sig:
            is_buy="BUY" in sig or "BULLISH" in sig
            sl=price*(1-sl_pct) if is_buy else price*(1+sl_pct)
            tgt=price*(1+tgt_pct) if is_buy else price*(1-tgt_pct)
            signals.append({
                "Stock":stock,"Type":sig,"Entry":round(price,2),
                "SL":round(sl,2),"Target":round(tgt,2),
                "Time":df.index[i].strftime("%Y-%m-%d %H:%M")
            })
    return signals

# =============================
# LIVE SCAN SECTION
# =============================
if st.button("🚀 SCAN MARKET"):
    all_data=[]
    with st.spinner("Scanning Stocks..."):
        for s in stocks:
            df=load_data(s,timeframe)
            if not df.empty: all_data.extend(get_signals(df,s))
    st.session_state.results=all_data

if "results" in st.session_state:
    res_df=pd.DataFrame(st.session_state.results)
    if not res_df.empty:
        st.subheader("📊 LIVE SIGNALS")
        st.dataframe(res_df,use_container_width=True)

        # ✅ Chart below signals
        for stock in res_df["Stock"].unique():
            df_live=load_data(stock,timeframe)
            if not df_live.empty:
                fig=go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df_live.index,open=df_live['Open'],high=df_live['High'],
                    low=df_live['Low'],close=df_live['Close'],name="Price"
                ))
                df_ind=add_indicators(df_live)
                if "EMA20" in df_ind.columns:
                    fig.add_trace(go.Scatter(x=df_ind.index,y=df_ind['EMA20'],name="EMA20",line=dict(color='orange')))
                    fig.add_trace(go.Scatter(x=df_ind.index,y=df_ind['EMA50'],name="EMA50",line=dict(color='blue')))
                sigs=res_df[res_df["Stock"]==stock]
                for _,r in sigs.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[r["Time"]],y=[r["Entry"]],text=r["Type"],
                        mode="markers+text",textposition="top center",
                        marker=dict(color="green" if "BUY" in r["Type"] or "BULLISH" in r["Type"] else "red",size=12)
                    ))
                fig.update_layout(height=450,xaxis_rangeslider_visible=False,template="plotly_dark")
                st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No signals found at this moment.")

# =============================
# BACKTEST ENGINE BUTTON
# =============================
if st.button("📂 RUN BACKTEST"):
    bt_stock = st.selectbox("Stock", stocks, key="bt_stock")
    bt_date = st.date_input("Analysis Date", datetime.now()-timedelta(days=1))
    bt_df = load_data(bt_stock,timeframe,period="5d")
    if not bt_df.empty:
        bt_df = bt_df[bt_df.index.date == bt_date]
        bt_signals = get_signals(bt_df, bt_stock)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=bt_df.index,open=bt_df['Open'],high=bt_df['High'],
            low=bt_df['Low'],close=bt_df['Close'],name="Price"
        ))
        bt_df_ind = add_indicators(bt_df)
        if "EMA20" in bt_df_ind.columns:
            fig.add_trace(go.Scatter(x=bt_df_ind.index,y=bt_df_ind['EMA20'],name="EMA20",line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=bt_df_ind.index,y=bt_df_ind['EMA50'],name="EMA50",line=dict(color='blue')))
        for sig in bt_signals:
            fig.add_trace(go.Scatter(
                x=[sig["Time"]],y=[sig["Entry"]],text=sig["Type"],
                mode="markers+text",textposition="top center",
                marker=dict(color="green" if "BUY" in sig["Type"] or "BULLISH" in sig["Type"] else "red",size=12)
            ))
        fig.update_layout(height=450,xaxis_rangeslider_visible=False,template="plotly_dark")
        st.plotly_chart(fig,use_container_width=True)

        if bt_signals:
            st.write(f"### 📂 Backtest Results for {bt_stock} ({bt_date})")
            bt_results_df = pd.DataFrame(bt_signals)
            st.dataframe(bt_results_df,use_container_width=True)
        else:
            st.warning("No signals recorded for this date.")
            bt_results_df = pd.DataFrame(columns=["Stock","Type","Entry","SL","Target","Time"])

        # ✅ Always Save CSV
        file_path = f"{BACKTEST_DIR}/{bt_stock}_{bt_date}.csv"
        bt_results_df.to_csv(file_path,index=False)

        # Download button
        csv_data = bt_results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_data,
            file_name=f"{bt_stock}_{bt_date}.csv",
            mime="text/csv"
        )

    st.sidebar.subheader("📂 Backtest Folder Contents")
    files = os.listdir(BACKTEST_DIR)
    if files:
        for f in files:
            st.sidebar.write(f)
    else:
        st.sidebar.write("No backtest files yet")
