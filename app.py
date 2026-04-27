import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor

# =============================
# CONFIG & REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE AI PRO V10 - SUPERFAST", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V10 - ULTIMATE TRACKER")
st.write(f"🕒 **Last Sync (IST):** {current_time}")

# =============================
# SECTOR-WISE STOCK LIST
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "ENERGY/INFRA": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "LT", "ADANIPORTS"],
    "CONSUMER": ["ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND", "VBL", "ASIANPAINT"],
    "OTHERS": ["BAJFINANCE", "BAJAJFINSV", "TATASTEEL", "JSWSTEEL", "BHARTIARTL", "SUNPHARMA"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# CORE FUNCTIONS (OPTIMIZED)
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty: return None
        return df.dropna()
    except: return None

def add_indicators(df):
    # EMA & RSI
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # VWAP (Daily Reset - Logic Improved)
    df['Date'] = df.index.date
    df['VWAP'] = df.groupby('Date', group_keys=False).apply(
        lambda x: (x['Close'] * x['Volume']).cumsum() / x['Volume'].cumsum()
    )
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def analyze_stock(s):
    df = get_data(s)
    if df is not None and len(df) > 10:
        df = add_indicators(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['Volume'].tail(20).mean()
        
        # AI Scoring logic
        score = 0
        if last['EMA20'] > last['EMA50']: score += 20
        if 40 < last['RSI'] < 70: score += 20
        if last['Volume'] > avg_vol * 1.5: score += 20
        if last['Close'] > last['VWAP']: score += 20
        if last['MACD'] > last['Signal_Line']: score += 20
        
        # Signals
        sig = "WAIT"
        if score >= 80 and last['Close'] > last['VWAP']: sig = "🚀 STRONG BUY"
        elif score <= 30 and last['Close'] < last['VWAP']: sig = "💀 STRONG SELL"
        elif score >= 60: sig = "BUY"
        elif score <= 40: sig = "SELL"
        
        # Alerts
        alert = "Normal"
        if last['Volume'] > avg_vol * 2.5: alert = "🐋 BIG FISH"
        elif prev['RSI'] < 30 and last['RSI'] > 30: alert = "🔄 BULLISH REV"
        
        curr_price = round(last['Close'], 2)
        sl = round(curr_price * 0.99, 2) if "BUY" in sig else round(curr_price * 1.01, 2) if "SELL" in sig else 0
        tgt = round(curr_price * 1.02, 2) if "BUY" in sig else round(curr_price * 0.98, 2) if "SELL" in sig else 0
        
        return {
            "STOCK": s, "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
            "PRICE": curr_price, "SIGNAL": sig, "ALERT": alert,
            "STOPLOSS": sl, "TARGET": tgt, "SCORE": score
        }
    return None

# =============================
# UI - TABS
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST", "📈 CHART ANALYSIS"])

with tab1:
    col1, col2 = st.columns([1, 4])
    with col1:
        selected_sector = st.selectbox("Select Sector", ["ALL"] + list(sector_map.keys()))
    
    if st.button("🚀 START AI SCAN"):
        target_stocks = all_stocks if selected_sector == "ALL" else sector_map[selected_sector]
        
        with st.spinner(f"Scanning {len(target_stocks)} stocks with Multi-threading..."):
            # Multi-threading for speed
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(analyze_stock, target_stocks))
            
            data_results = [r for r in results if r is not None]
            if data_results:
                res_df = pd.DataFrame(data_results)
                # Highlighting signals
                def color_signal(val):
                    color = 'green' if 'BUY' in val else 'red' if 'SELL' in val else 'white'
                    return f'color: {color}; font-weight: bold'
                
                st.dataframe(res_df.style.applymap(color_signal, subset=['SIGNAL']), use_container_width=True)
            else:
                st.error("No data found.")

with tab2:
    st.info("గత 30 రోజుల్లో ఈ AI స్ట్రాటజీ ప్రకారం వచ్చిన పక్కా సిగ్నల్స్ రిపోర్ట్.")
    if st.button("📈 RUN BACKTEST (FAST)"):
        bt_logs = []
        with st.spinner("Processing historical data..."):
            for s in all_stocks[:15]: # Performance కోసం టాప్ 15 స్టాక్స్
                df_bt = get_data(s, period="1mo", interval="15m")
                if df_bt is not None:
                    df_bt = add_indicators(df_bt)
                    # Vectorized conditions for speed
                    strong_buy = (df_bt['EMA20'] > df_bt['EMA50']) & (df_bt['Close'] > df_bt['VWAP']) & (df_bt['RSI'] > 60)
                    hits = df_bt[strong_buy]
                    for idx, row in hits.tail(10).iterrows():
                        bt_logs.append({
                            "DATE": idx.astimezone(IST).strftime('%Y-%m-%d %H:%M'),
                            "STOCK": s, "ENTRY": round(row['Close'], 2), "SIGNAL": "🚀 STRONG BUY"
                        })
        if bt_logs:
            st.table(pd.DataFrame(bt_logs))

with tab3:
    selected = st.selectbox("Select stock:", all_stocks)
    chart_df = get_data(selected, period="5d", interval="15m")
    if chart_df is not None:
        chart_df = add_indicators(chart_df)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['VWAP'], line=dict(color='orange', width=2), name="VWAP"))
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA20'], line=dict(color='blue', width=1), name="EMA20"))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{selected} Real-time Technicals")
        st.plotly_chart(fig, use_container_width=True)
