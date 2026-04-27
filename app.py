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
st.set_page_config(page_title="🔥 NSE AI PRO V12 - ALL SECTORS", layout="wide")
st_autorefresh(interval=60000, key="refresh")

IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 NSE AI PRO V12 - ALL SECTOR TRACKER")
st.write(f"🕒 **Current Market Sync (IST):** {current_time}")

# =============================
# ALL SECTOR STOCK LIST (NSE)
# =============================
sector_map = {
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "AUBANK", "FEDERALBNK"],
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "COFORGE", "PERSISTENT"],
    "AUTO": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "ASHOKLEY"],
    "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "TORNTPHARM", "AUROPHARMA"],
    "FMCG": ["ITC", "HINDUNILVR", "BRITANNIA", "NESTLEIND", "VBL", "TATACONSUM", "GODREJCP", "DABUR"],
    "METAL": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL", "NMDC", "SAIL"],
    "ENERGY/INFRA": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "LT", "ADANIPORTS", "ADANIENT"],
    "REALTY/MEDIA": ["DLF", "LODHA", "OBEROIRLTY", "SUNTV", "ZEEL", "PVRINOX"]
}
all_stocks = [s for sub in sector_map.values() for s in sub]

# =============================
# CORE FUNCTIONS
# =============================
def get_data(stock, period="1y", interval="1d"):
    try:
        df = yf.Ticker(stock + ".NS").history(period=period, interval=interval)
        if df.empty: return None
        df.index = df.index.tz_localize(None) 
        return df.dropna()
    except: return None

def add_indicators(df):
    df = df.copy()
    # Indicators
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Big_Player'] = df['Volume'] > (df['Vol_Avg'] * 3.5)
    
    df['Bull_Rev'] = (df['RSI'].shift(1) < 30) & (df['RSI'] > 30)
    return df

# =============================
# UI LAYOUT
# =============================
tab1, tab2, tab3 = st.tabs(["🔍 SECTOR-WISE SCANNER", "📈 ONE-DAY ANALYSIS", "📊 ALL SECTOR STATUS"])

with tab1:
    selected_sector = st.selectbox("Select Sector to Scan:", list(sector_map.keys()))
    if st.button(f"Scan {selected_sector}"):
        results = []
        with st.spinner(f"Scanning {selected_sector} Sector..."):
            for s in sector_map[selected_sector]:
                df = yf.Ticker(s + ".NS").history(period="2d", interval="15m")
                if not df.empty:
                    df = add_indicators(df)
                    last = df.iloc[-1]
                    status = "WAIT"
                    if last['Close'] > last['VWAP'] and last['EMA20'] > last['EMA50']: status = "🚀 STRONG BUY"
                    
                    results.append({"STOCK": s, "PRICE": round(last['Close'], 2), "SIGNAL": status, "RSI": round(last['RSI'], 2)})
        st.table(pd.DataFrame(results))

with tab2:
    selected_stock = st.selectbox("Select Stock for Chart:", all_stocks)
    c_df = get_data(selected_stock)
    if c_df is not None:
        c_df = add_indicators(c_df)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=c_df.index, open=c_df['Open'], high=c_df['High'], low=c_df['Low'], close=c_df['Close'], name="Daily"))
        
        # Big Player Entry (🟡 Yellow Diamond)
        big_p = c_df[c_df['Big_Player']]
        fig.add_trace(go.Scatter(x=big_p.index, y=big_p['Low']*0.98, mode='markers', marker=dict(symbol='diamond', size=10, color='yellow'), name="Big Player"))
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, title=f"{selected_stock} Trend")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.info("ప్రస్తుతం మార్కెట్‌లో ఏ సెక్టార్ బలంగా ఉందో ఇక్కడ చూడవచ్చు.")
    if st.button("Check All Sectors"):
        sector_results = []
        for sec, stk_list in sector_map.items():
            # సెక్టార్‌లోని మొదటి స్టాక్‌ను బట్టి సెక్టార్ మూడ్‌ని అంచనా వేయడం
            test_df = get_data(stk_list[0], period="5d", interval="1d")
            if test_df is not None:
                test_df = add_indicators(test_df)
                last_val = test_df.iloc[-1]
                mood = "🟢 BULLISH" if last_val['Close'] > last_val['EMA20'] else "🔴 BEARISH"
                sector_results.append({"SECTOR": sec, "MOOD": mood, "TOP STOCK": stk_list[0]})
        st.table(pd.DataFrame(sector_results))
