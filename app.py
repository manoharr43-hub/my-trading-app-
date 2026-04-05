import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. పేజీ సెటప్
st.set_page_config(page_title="Variety Motors Live Scanner", layout="wide")

# 2. ఆటో రిఫ్రెష్ (10 సెకన్లకు ఒకసారి - లోడింగ్ స్పీడ్ పెరుగుతుంది)
st_autorefresh(interval=10000, limit=None, key="fizzbuzzcounter")

# 3. సెక్టార్ డేటా
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

# 4. వేగంగా డేటా తెచ్చే ఫంక్షన్ (Caching)
@st.cache_data(ttl=10)
def get_live_data(stock_list):
    try:
        # threads=True వాడటం వల్ల స్పీడ్ పెరుగుతుంది
        data = yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        return data
    except:
        return None

# 5. మెయిన్ స్కానర్ ఫంక్షన్
def run_live_scan(stock_list):
    results = []
    data = get_live_data(stock_list)
    
    if data is None or data.empty:
        st.warning("డేటా లోడ్ అవుతోంది... దయచేసి 10 సెకన్లు ఆగండి.")
        return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if not df.empty and len(df) > 10:
                ltp = round(df['Close'].iloc[-1], 2)
                
                # Support & Resistance (Pivot Levels)
                high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)
                sup1 = round((2 * pivot) - high, 2)
                
                # Operator Entry (Volume Check)
                curr_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].rolling(window=15).mean().iloc[-1]
                is_operator = "⚠️ BIG FISH" if curr_vol > (avg_vol * 2.2) else "Normal"
                
                # Signal Logic
                sig = "⏳ NEUTRAL"
                color = "#ffffff"
                if ltp > res1:
                    sig = "🚀 BUY"
                    color = "#d4edda"
                elif ltp < sup1:
                    sig = "🔻 SELL"
                    color = "#f8d7da"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": ltp,
                    "Support": sup1,
                    "Resistance": res1,
                    "Operator": is_operator,
                    "Signal": sig,
                    "Bg": color
                })
        except: continue
    
    if results:
        df_final = pd.DataFrame(results)
        # టేబుల్ ప్రదర్శన
        st.table(df_final.drop(columns=['Bg']).style.apply(
            lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"] * len(x), axis=1)
        )

# 6. UI ఇంటర్‌ఫేస్
st.sidebar.title("📁 Live Sectors")
sector_choice = st.sidebar.selectbox("Select Sector", list(sector_data.keys()))

st.title(f"⚡ Live Market Scanner: {sector_choice}")
st.write(f"🔄 Last Updated: {pd.Timestamp.now().strftime('%H:%M:%S')}")

# రన్ చేయడం
run_live_scan(sector_data[sector_choice])

st.caption("Developed by Manohar | Variety Motors, Hyderabad | Faster Load Enabled")
