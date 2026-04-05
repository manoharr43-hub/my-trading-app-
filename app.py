import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Variety Motors Pro Scanner", layout="wide")
st_autorefresh(interval=10000, limit=None, key="fizzbuzzcounter")

# --- Sector Data ---
sector_data = {
    "Nifty 50": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TCS.NS", "INFY.NS", "SBIN.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "PNB.NS"],
    "Auto (Variety Motors)": ["HEROMOTOCO.NS", "TATAMOTORS.NS", "M&M.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "RECLTD.NS", "PFC.NS"]
}

@st.cache_data(ttl=10)
def get_live_data(stock_list):
    try:
        data = yf.download(stock_list, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        return data
    except: return None

# --- 1. సెక్టార్ స్ట్రెంత్ (Top/Low Strong) ---
st.subheader("📊 Today's Sector Heatmap (High & Low Strong)")
perf_data = []
for sector, stocks in sector_data.items():
    s_data = yf.download(stocks, period="1d", interval="15m", progress=False)['Close']
    if not s_data.empty:
        change = ((s_data.iloc[-1] - s_data.iloc[0]) / s_data.iloc[0]).mean() * 100
        perf_data.append({"Sector": sector, "Change %": round(change, 2)})

perf_df = pd.DataFrame(perf_data).sort_values(by="Change %", ascending=False)
cols = st.columns(len(perf_df))
for i, row in enumerate(perf_df.itertuples()):
    color = "normal" if abs(row._2) < 0.5 else ("inverse" if row._2 > 0 else "off")
    cols[i].metric(row.Sector, f"{row._2}%", delta_color=color)

def run_live_scan(stock_list):
    results = []
    data = get_live_data(stock_list)
    if data is None or data.empty: return

    for s in stock_list:
        try:
            df = data[s] if len(stock_list) > 1 else data
            if len(df) < 10: continue
            
            ltp = round(df['Close'].iloc[-1], 2)
            open_p = df['Open'].iloc[0]
            change_p = round(((ltp - open_p) / open_p) * 100, 2)
            
            # Support & Resistance
            high, low, close = df['High'].iloc[-2], df['Low'].iloc[-2], df['Close'].iloc[-2]
            pivot = (high + low + close) / 3
            res = round((2 * pivot) - low, 2)
            sup = round((2 * pivot) - high, 2)

            # --- 2. OI Increase & Operator Logic (LH/RH Side) ---
            curr_vol = df['Volume'].iloc[-1]
            avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
            vol_spike = curr_vol > (avg_vol * 2.0)
            
            oi_status = "Normal"
            op_entry = "Retail"
            bg_color = "#ffffff"

            # ప్రైస్ పెరుగుతూ వాల్యూమ్ పెరిగితే Call Side OI Incr
            if vol_spike and ltp > df['Close'].iloc[-2]:
                oi_status = "🟢 Call OI Incr"
                op_entry = "⚠️ BIG FISH BUY"
                bg_color = "#d4edda"
            # ప్రైస్ తగ్గుతూ వాల్యూమ్ పెరిగితే Put Side OI Incr
            elif vol_spike and ltp < df['Close'].iloc[-2]:
                oi_status = "🔴 Put OI Incr"
                op_entry = "⚠️ BIG FISH SELL"
                bg_color = "#f8d7da"

            # HDFC స్పెషల్ మార్క్
            display_name = f"⭐ {s.replace('.NS','')}" if "HDFCBANK" in s else s.replace(".NS","")

            results.append({
                "Stock (LH)": display_name,
                "Price": ltp,
                "Change %": f"{change_p}%",
                "Support": sup,
                "Resistance": res,
                "OI Status (RH)": oi_status,
                "Operator": op_entry,
                "Bg": bg_color
            })
        except: continue

    if results:
        df_final = pd.DataFrame(results)
        st.table(df_final.drop(columns=['Bg']).style.apply(lambda x: [f"background-color: {df_final.loc[x.name, 'Bg']}"]*len(x), axis=1))

# Sidebar & Execution
sector_choice = st.sidebar.selectbox("Select Sector", list(sector_data.keys()))
st.title(f"⚡ Live Scanner: {sector_choice}")
run_live_scan(sector_data[sector_choice])
