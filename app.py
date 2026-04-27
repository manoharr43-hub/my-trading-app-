Import streamlit as st
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
st.set_page_config(page_title="🔥 NSE AI PRO V10.5 - INTRADAY SPECIAL", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V10.5 - ULTIMATE TRACKER")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")

# =============================
# STOCK LIST & SECTORS
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
# CORE FUNCTIONS
# =============================
def get_data(stock, period="2d", interval="15m"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        return df.dropna() if not df.empty else None
    except: return None

def add_indicators(df):
    df = df.copy()
    # EMA & RSI
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # Intraday VWAP (Daily Reset)
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
    if df is not None and len(df) > 15:
        df = add_indicators(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['Volume'].tail(20).mean()
        
        # Scoring Logic
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
        
        # SMART ALERTS (Updated to 3.5x and Power Reversal)
        alert = "Normal"
        if last['Volume'] > avg_vol * 3.5: 
            alert = "🐋 BIG FISH (3.5x)"
        elif prev['RSI'] < 30 and last['RSI'] > 30 and last['Close'] > last['VWAP']:
            alert = "🔄 POWER REVERSAL"
        elif prev['RSI'] > 70 and last['RSI'] < 70:
            alert = "🔄 BEARISH REV"
            
        curr_price = round(last['Close'], 2)
        sl = round(curr_price * 0.99, 2) if "BUY" in sig else round(curr_price * 1.01, 2) if "SELL" in sig else 0
        tgt = round(curr_price * 1.02, 2) if "BUY" in sig else round(curr_price * 0.98, 2) if "SELL" in sig else 0
        
        return {
            "STOCK": s, "TIME": df.index[-1].astimezone(IST).strftime('%H:%M'),
            "PRICE": curr_price, "SIGNAL": sig, "SMART ALERT": alert,
            "STOPLOSS": sl, "TARGET": tgt, "SCORE": score
        }
    return None

# =============================
# UI LAYOUT
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 LIVE SCANNER", "📊 30-DAY BACKTEST", "📈 CHART ANALYSIS"])

with tab1:
    col_s1, col_s2 = st.columns([1, 4])
    with col_s1:
        sel_sec = st.selectbox("Sector Filter", ["ALL"] + list(sector_map.keys()))
    
    if st.button("🚀 START AI SCAN"):
        targets = all_stocks if sel_sec == "ALL" else sector_map[sel_sec]
        with st.spinner(f"Scanning {len(targets)} stocks..."):
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(analyze_stock, targets))
            
            final_res = [r for r in results if r is not None]
            if final_res:
                res_df = pd.DataFrame(final_res)
                
                # Signal Styling Fix
                def color_signal(val):
                    if 'BUY' in str(val): return 'background-color: #004d00; color: white; font-weight: bold'
                    if 'SELL' in str(val): return 'background-color: #4d0000; color: white; font-weight: bold'
                    return ''

                st.dataframe(res_df.style.map(color_signal, subset=['SIGNAL']), use_container_width=True)
            else:
                st.warning("No data found.")

with tab2:
    st.info("గత 30 రోజుల్లో 3.5x వాల్యూమ్ మరియు పక్కా సిగ్నల్స్ వచ్చిన డేటా.")
    if st.button("📈 RUN BACKTEST"):
        bt_data = []
        with st.spinner("Analyzing historical data..."):
            for s in all_stocks[:12]:
                df_bt = get_data(s, period="1mo", interval="15m")
                if df_bt is not None:
                    df_bt = add_indicators(df_bt)
                    # Backtest for Strong Buy + Volume Spike
                    signals = df_bt[(df_bt['Close'] > df_bt['VWAP']) & (df_bt['RSI'] > 60) & (df_bt['Volume'] > df_bt['Volume'].rolling(20).mean() * 3.5)]
                    for idx, row in signals.tail(10).iterrows():
                        bt_data.append({
                            "DATE": idx.astimezone(IST).strftime('%Y-%m-%d %H:%M'),
                            "STOCK": s, "ENTRY": round(row['Close'], 2), "TYPE": "3.5x VOL BREAKOUT"
                        })
        if bt_data:
            st.table(pd.DataFrame(bt_data))

with tab3:
    selected = st.selectbox("Select stock to view Chart:", all_stocks)
    c_df = get_data(selected, period="5d", interval="15m")
    if c_df is not None:
        c_df = add_indicators(c_df)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=c_df.index, open=c_df['Open'], high=c_df['High'], low=c_df['Low'], close=c_df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['VWAP'], line=dict(color='orange', width=2), name="VWAP"))
        fig.add_trace(go.Scatter(x=c_df.index, y=c_df['EMA20'], line=dict(color='cyan', width=1), name="EMA20"))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{selected} Real-time Technicals")
        st.plotly_chart(fig, use_container_width=True)
