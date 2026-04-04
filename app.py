import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Pro Sector Scanner", layout="wide")

# --- ఎడమ వైపు సెక్టార్ ఫోల్డర్స్ (Sidebar) ---
st.sidebar.title("📁 Sector Folders")
sector_choice = st.sidebar.selectbox(
    "Select Sector to Scan", 
    [
        "Market Overview",
        "Nifty 50 (Top Stocks)",
        "Banking (Nifty Bank)", 
        "Auto (Variety Motors Special)", 
        "IT (Software)", 
        "Pharma (Healthcare)",
        "Metal (Steel/Iron)",
        "Finance (Fin Nifty)"
    ]
)

# --- స్టాక్ అనాలిసిస్ ఫంక్షన్ ---
def run_sector_scan(stock_list):
    results = []
    status = st.empty()
    for s in stock_list:
        status.info(f"Analyzing {s}...")
        try:
            ticker = yf.Ticker(s)
            df = ticker.history(period="20d", interval="1d")
            if not df.empty and len(df) > 1:
                ltp = round(df['Close'].iloc[-1], 2)
                prev_close = df['Close'].iloc[-2]
                pct_change = round(((ltp - prev_close) / prev_close) * 100, 2)
                
                # Pivot Levels
                high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
                pivot = (high + low + close) / 3
                buy_above = round((2 * pivot) - low, 2)
                sell_below = round((2 * pivot) - high, 2)
                
                # Logic
                if ltp > buy_above:
                    sig, color = "🚀 BUY", "#d4edda"
                elif ltp < sell_below:
                    sig, color = "🔻 SELL", "#f8d7da"
                else:
                    sig, color = "⏳ NEUTRAL", "#ffffff"
                
                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "Change %": f"{pct_change}%",
                    "Buy Above": f"{buy_above:.2f}",
                    "Sell Below": f"{sell_below:.2f}",
                    "Signal": sig,
                    "Bg": color
                })
        except: continue
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# --- సెక్టార్ వైజ్ డేటా ---
sector_data = {
    "Nifty 50 (Top Stocks)": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS"],
    "Banking (Nifty Bank)": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS", "FEDERALBNK.NS", "AUBANK.NS"],
    "Auto (Variety Motors Special)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "TVSMOTOR.NS", "MARUTI.NS"],
    "IT (Software)": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "COFORGE.NS"],
    "Pharma (Healthcare)": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "TORNTPHARM.NS"],
    "Metal (Steel/Iron)": ["TATASTEEL.NS", "JINDALSTEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS"],
    "Finance (Fin Nifty)": ["BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS"]
}

# --- మెయిన్ డిస్‌ప్లే ---
if sector_choice == "Market Overview":
    st.title("🌍 Market Heatmap & Overview")
    st.write("ఎడమ వైపు ఉన్న ఫోల్డర్స్ నుండి ఏదైనా సెక్టార్‌ని సెలెక్ట్ చేసుకోండి.")
    st.info("ఈరోజు ఏ సెక్టార్ బలంగా ఉందో చూసి, అందులోని 'BUY' స్టాక్స్‌ని పట్టుకోండి!")

else:
    st.title(f"🔍 Scanning {sector_choice}")
    if st.button(f"Scan {sector_choice} Now"):
        stocks = sector_data.get(sector_choice, [])
        run_sector_scan(stocks)

st.divider()
st.caption("Developed by Manohar | Variety Motors, Hyderabad | All the best for your Trades!")
