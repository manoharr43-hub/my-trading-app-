import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🔥 MANOHAR NSE AI PRO", layout="wide")
st_autorefresh(interval=60000, key="refresh")

st.title("🚀 MANOHAR NSE AI PRO TERMINAL")
st.markdown("---")

# =============================
# DIRECTION FUNCTION
# =============================
def get_direction(signal):
    if signal == "🚀 CONFIRMED BUY":
        return "🟢 UP"
    elif signal == "💀 CONFIRMED SELL":
        return "🔴 DOWN"
    elif signal == "⚠️ FAILED SELL → BUY":
        return "🟢 UP"
    elif signal == "⚠️ FAILED BUY → SELL":
        return "🔴 DOWN"
    else:
        return "⚪ WAIT"

# =============================
# ANALYSIS FUNCTION
# =============================
def analyze_data(df):
    if df is None or len(df) < 20:
        return None

    e20 = df['Close'].ewm(span=20).mean()
    e50 = df['Close'].ewm(span=50).mean()

    vol = df['Volume']
    avg_vol = vol.rolling(window=20).mean()

    curr_price = df['Close'].iloc[-1]
    curr_e20 = e20.iloc[-1]
    curr_e50 = e50.iloc[-1]
    curr_vol = vol.iloc[-1]
    curr_avg_vol = avg_vol.iloc[-1]

    if pd.isna(curr_avg_vol) or curr_avg_vol == 0:
        return None

    cp_strength = "🔵 CALL STRONG" if curr_e20 > curr_e50 else "🔴 PUT STRONG"

    if curr_vol > curr_avg_vol * 2:
        big_player = "🔥 EXTREME INSTITUTIONAL"
    elif curr_vol > curr_avg_vol * 1.5:
        big_player = "🐋 BIG PLAYER ACTIVE"
    else:
        big_player = "💤 NORMAL"

    observation = "WAIT"
    entry, sl, target = 0, 0, 0

    recent_high = df['High'].iloc[-10:].max()
    recent_low = df['Low'].iloc[-10:].min()
    risk = (recent_high - recent_low) if (recent_high - recent_low) > 0 else curr_price * 0.01

    if curr_e20 > curr_e50 and curr_vol > curr_avg_vol:
        observation = "🚀 CONFIRMED BUY"
        entry = curr_price
        sl = curr_price - (risk * 0.5)
        target = curr_price + risk

    elif curr_e20 < curr_e50 and curr_vol > curr_avg_vol:
        observation = "💀 CONFIRMED SELL"
        entry = curr_price
        sl = curr_price + (risk * 0.5)
        target = curr_price - risk

    try:
        ema_score = abs(curr_e20 - curr_e50) / curr_price * 100
        vol_score = curr_vol / curr_avg_vol
        momentum = (curr_price - df['Close'].iloc[-5]) / curr_price * 100
        range_strength = (recent_high - recent_low) / curr_price * 100

        trend_score = (
            ema_score * 0.3 +
            vol_score * 20 * 0.3 +
            abs(momentum) * 0.2 +
            range_strength * 0.2
        )
        trend_score = min(100, round(trend_score, 2))
    except:
        trend_score = 0

    return (
        cp_strength,
        observation,
        big_player,
        round(entry, 2),
        round(sl, 2),
        round(target, 2),
        trend_score
    )

# =============================
# SECTORS
# =============================
all_sectors = {
    "Nifty 50": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","BHARTIARTL"],
    "Banking": ["SBIN","AXISBANK","KOTAKBANK","HDFCBANK","ICICIBANK","PNB","CANBK","FEDERALBNK"],
    "Auto": ["TATAMOTORS","MARUTI","M&M","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR"],
    "Metal": ["TATASTEEL","JINDALSTEL","HINDALCO","JSWSTEEL","NATIONALUM","SAIL","VEDL"],
    "IT Sector": ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","COFORGE"],
    "Pharma": ["SUNPHARMA","DRREDDY","CIPLA","APOLLOHOSP","DIVISLAB"]
}

# =============================
# SIDEBAR
# =============================
st.sidebar.title("📂 Backtest Panel")
bt_date = st.sidebar.date_input("Select Date", datetime.now() - timedelta(days=1))
bt_stock_input = st.sidebar.text_input("Stock (optional)", "").upper()

# =============================
# MAIN SCANNER
# =============================
selected_sector = st.selectbox("📂 Select Sector", list(all_sectors.keys()))
stocks = all_sectors[selected_sector]

if st.button("🔍 START LIVE SCANNER", use_container_width=True):

    results = []
    breakout_day_list = []

    with st.spinner("AI Scanning Market..."):
        for s in stocks:
            try:
                df = yf.Ticker(s + ".NS").history(period="1d", interval="15m")
                if df is None or df.empty:
                    continue

                res = analyze_data(df)
                if res:
                    signal = res[1]
                    results.append({
                        "Stock": s,
                        "Price": round(df['Close'].iloc[-1], 2),
                        "Trend": res[0],
                        "Signal": signal,
                        "Big Player": res[2],
                        "Entry": res[3],
                        "SL": res[4],
                        "Target": res[5],
                        "Trend Score": res[6],
                        "Direction": get_direction(signal),
                        "Time": df.index[-1].strftime('%H:%M')
                    })

                # 🔥 Breakout Logic
                opening_data = df.between_time("09:15", "09:30")
                if not opening_data.empty:
                    opening_high = opening_data['High'].max()
                    opening_low = opening_data['Low'].min()

                    for i in range(1, len(df)-3):
                        prev = df.iloc[i-1]
                        curr = df.iloc[i]
                        time = df.index[i]
                        price = curr['Close']

                        if prev['Close'] <= opening_high and curr['Close'] > opening_high:
                            future = df.iloc[i+1:i+4]
                            up = sum(future['Close'] > curr['Close'])
                            down = sum(future['Close'] <= curr['Close'])
                            signal_type = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"

                            breakout_day_list.append({
                                "Stock": s,
                                "Price": round(price, 2),
                                "Type": signal_type,
                                "Time": time.strftime('%H:%M'),
                                "Entry": round(price, 2),
                                "Stoploss": round(price - (price * 0.01), 2),
                                "Exit": round(price + (price * 0.02), 2)
                            })
                            break

                        elif prev['Close'] >= opening_low and curr['Close'] < opening_low:
                            future = df.iloc[i+1:i+4]
                            down = sum(future['Close'] < curr['Close'])
                            up = sum(future['Close'] >= curr['Close'])
                            signal_type = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"

                            breakout_day_list.append({
                                "Stock": s,
                                "Price": round(price, 2),
                                "Type": signal_type,
                                "Time": time.strftime('%H:%M'),
                                "Entry": round(price, 2),
                                "Stoploss": round(price + (price * 0.01), 2),
                                "Exit": round(price - (price * 0.02), 2)
                            })
                            break
            except:
                continue

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.error("No Data Found")

    st.markdown("---")
    st.subheader("🔥 SMART BREAKOUT STOCKS (DIRECTION CONFIRMED)")
    if breakout_day_list:
        st.dataframe(pd.DataFrame(breakout_day_list), use_container_width=True)
    else:
        st.info("No Breakout Stocks
