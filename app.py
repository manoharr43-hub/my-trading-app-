import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh # కొత్తగా యాడ్ చేశాం

st.set_page_config(page_title="Variety Motors Live Scanner", layout="wide")

# --- 5 సెకన్లకు ఒకసారి ఆటోమేటిక్ గా రిఫ్రెష్ అవుతుంది ---
count = st_autorefresh(interval=5000, limit=None, key="fizzbuzzcounter")

# Sidebar
st.sidebar.title("📁 Live Sectors")
sector_choice = st.sidebar.selectbox(
    "Select Sector", 
    ["Nifty 50", "Banking", "Auto (Variety Motors)", "IT", "Pharma", "Finance"]
)

def run_live_scan(stock_list):
    results = []
    # ఆటో రిఫ్రెష్ అవుతున్నప్పుడు పదే పదే మెసేజ్ రాకుండా జాగ్రత్త పడదాం
    try:
        # Download data for all stocks in bulk
        data = yf.download(stock_list, period="2d", interval="1m", group_by='ticker', threads=True, progress=False)
        
        for s in stock_list:
            df = data[s] if len(stock_list) > 1 else data
            if not df.empty and len(df) > 2:
                ltp = round(df['Close'].iloc[-1], 2)
                prev_close = df['Close'].iloc[-2]
                pct_change = round(((ltp - prev_close) / prev_close) * 100, 2)
                
                # Pivot Levels for Intraday
                high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
                pivot = (high + low + close) / 3
                res1 = round((2 * pivot) - low, 2)
                sup1 = round((2 * pivot) - high, 2)
                
                # Signal Logic
                sig, color, analysis = "⏳ NEUTRAL", "#ffffff", "Range"
                if ltp > res1:
                    sig, color, analysis = "🚀 BUY", "#d4edda", "✅ BREAKOUT"
                elif ltp < sup1:
                    sig, color, analysis = "🔻 SELL", "#f8d7da", "✅ BREAKDOWN"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Change": f"{pct_change}%",
                    "Buy Above": f"{res1:.2f}",
                    "Sell Below": f"{sup1:.2f}",
                    "Signal": sig,
                    "Status": analysis,
                    "Bg": color
                })
    except: pass
    
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# Sector Lists
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

st.title(f"⚡ Live Market Scanner: {sector_choice}")
st.write(f"🔄 Last Updated: {pd.Timestamp.now().strftime('%H:%M:%S')} (Refreshing every 5s)")

run_live_scan(sector_data.get(sector_choice, []))

st.caption("Developed by Manohar | Variety Motors, Hyderabad | Real-time Auto-Refresh Enabled")
