import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Variety Motors Intraday Scanner", layout="wide")

# Sidebar
st.sidebar.title("📁 Intraday Sectors")
sector_choice = st.sidebar.selectbox(
    "Select Sector", 
    ["Nifty 50", "Banking", "Auto (Variety Motors)", "IT", "Pharma", "Finance"]
)

def run_intraday_scan(stock_list):
    results = []
    status = st.empty()
    status.info("Intraday scanning in progress (15m Intervals)...")
    
    try:
        # Fetching 15-minute interval data for intraday precision
        data = yf.download(stock_list, period="5d", interval="15m", group_by='ticker', threads=True, progress=False)
        
        for s in stock_list:
            df = data[s] if len(stock_list) > 1 else data
            if not df.empty and len(df) > 10:
                ltp = round(df['Close'].iloc[-1], 2)
                
                # --- Intraday Pivot Levels (Based on Previous Day) ---
                # We need daily data for pivots, so we fetch it separately for accuracy
                hist = yf.Ticker(s).history(period="2d")
                prev_high = hist['High'].iloc[0]
                prev_low = hist['Low'].iloc[0]
                prev_close = hist['Close'].iloc[0]
                
                pivot = (prev_high + prev_low + prev_close) / 3
                res1 = round((2 * pivot) - prev_low, 2)
                sup1 = round((2 * pivot) - prev_high, 2)
                
                # --- VWAP Calculation (Approx for Intraday) ---
                df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
                vwap = round((df['TP'] * df['Volume']).sum() / df['Volume'].sum(), 2)
                
                # --- Intraday Logic ---
                sig = "⏳ NEUTRAL"
                bg_color = "#ffffff"
                analysis = "Range Bound"

                # Condition: Price > R1 and Price > VWAP for Strong Buy
                if ltp > res1:
                    if ltp > vwap:
                        sig, bg_color, analysis = "🚀 STRONG BUY", "#d4edda", "✅ REAL BREAKOUT"
                    else:
                        sig, bg_color, analysis = "🚀 BUY", "#e1f5fe", "⚠️ WATCH VWAP"
                
                elif ltp < sup1:
                    if ltp < vwap:
                        sig, bg_color, analysis = "🔻 STRONG SELL", "#f8d7da", "✅ REAL BREAKDOWN"
                    else:
                        sig, bg_color, analysis = "🔻 SELL", "#fff3e0", "⚠️ WATCH VWAP"

                results.append({
                    "Stock": s.replace(".NS",""),
                    "LTP": f"{ltp:.2f}",
                    "VWAP": f"{vwap:.2f}",
                    "Buy Above (R1)": f"{res1:.2f}",
                    "Sell Below (S1)": f"{sup1:.2f}",
                    "Signal": sig,
                    "Analysis": analysis,
                    "Bg": bg_color
                })
    except Exception as e:
        st.error(f"Error: {e}")
        
    status.empty()
    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# Sector Lists
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Pharma": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

st.title(f"⚡ Intraday Scanner: {sector_choice}")
if st.button(f"Scan {sector_choice} (15m)"):
    run_intraday_scan(sector_data.get(sector_choice, []))

st.caption("Developed by Manohar | Variety Motors, Hyderabad | Powered by 15m VWAP Logic")
