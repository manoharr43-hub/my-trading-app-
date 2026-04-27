import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V15 - BACKTEST FIXED", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V15 - ULTIMATE DASHBOARD")
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
# CORE FUNCTIONS
# =============================
def get_clean_data(stock, period="1y", interval="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty: return None
        df.index = df.index.tz_localize(None)
        return df.dropna()
    except: return None

def add_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    # ✅ RSI Fix (EMA method)
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ✅ VWAP Daily Reset
    df['CumVol'] = df['Volume'].groupby(df.index.date).cumsum()
    df['CumPV'] = (df['Close'] * df['Volume']).groupby(df.index.date).cumsum()
    df['VWAP'] = df['CumPV'] / df['CumVol']
    
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 2.5)
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    return df

# =============================
# UI - TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST REPORT", "📈 CHART ANALYSIS"])

with tab1:
    s_sec = st.selectbox("Select Sector", list(sector_map.keys()))
    if st.button(f"🚀 SCAN {s_sec}"):
        live_results = []
        with st.spinner("Analyzing Live Entry Points..."):
            for s in sector_map[s_sec]:
                df_l = yf.Ticker(s + ".NS").history(period="2d", interval="15m")
                if not df_l.empty:
                    df_l.index = df_l.index.tz_convert(IST)
                    df_l = add_indicators(df_l)
                    last = df_l.iloc[-1]
                    
                    price = round(last['Close'], 2)
                    sig = "WAIT"
                    sl, tgt = 0, 0
                    
                    if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']:
                        sig = "🚀 STRONG BUY"
                        sl = round(price * 0.99, 2)
                        tgt = round(price * 1.02, 2)
                    
                    live_results.append({
                        "STOCK": s, "TIME": df_l.index[-1].strftime('%H:%M'),
                        "ENTRY": price, "SIGNAL": sig, "STOPLOSS": sl, "TARGET": tgt,
                        "ALERT": "🐋 BIG FISH" if last['Big_Player'] else "Normal"
                    })
        if live_results:
            st.dataframe(pd.DataFrame(live_results), use_container_width=True)

with tab2:
    st.header("📊 Historical Backtest Report")
    st.info("గత 30 రోజుల్లో ఈ స్ట్రాటజీ ప్రకారం వచ్చిన పక్కా ఎంట్రీలు కింద టేబుల్‌లో చూడవచ్చు.")
    
    if st.button("📈 GENERATE BACKTEST REPORT"):
        back_logs = []
        with st.spinner("Fetching Historical Back Data..."):
            for s in all_stocks:
                df_b = get_clean_data(s, period="2mo", interval="1d")
                if df_b is not None:
                    df_b = add_indicators(df_b)
                    hits = df_b[(df_b['Big_Player']) | (df_b['Bull_Rev'])]
                    for idx, row in hits.iterrows():   # ✅ full logs
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
        else:
            st.warning("గత 30 రోజుల్లో సిగ్నల్స్ ఏవీ దొరకలేదు.")

with tab3:
    st.header("📈 Technical Chart Analysis")
    sel_stock = st.selectbox("Select Stock:", all_stocks)
    c_df = get_clean_data(sel_stock)
    if c_df is not None:
        c_df = add_indicators(c_df)
        last_val = round(c_df.iloc[-1]['Close'], 2)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=c_df.index, open=c_df['Open'], high=c_df['High'], low=c_df['Low'], close=c_df['Close'], name="Daily"))
        
        fig.add_hline(y=last_val * 1.02, line_dash="dash", line_color="green", annotation_text="Target (2%)")
        fig.add_hline(y=last_val * 0.99, line_dash="dash", line_color="red", annotation_text="SL (1%)")
        
        big_entry = c_df[c_df['Big_Player']]
        fig.add_trace(go.Scatter(x=big_entry.index, y=big_entry['Low']*0.98, mode='markers', marker=dict(symbol='diamond', size=10, color='yellow'), name="Big Player"))
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
