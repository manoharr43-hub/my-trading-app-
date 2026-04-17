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

# =============================
# HEADER
# =============================
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
# BACKTEST PANEL (Selected Date Data)
# =============================
st.markdown("---")
st.subheader(f"📅 Backtest Report - {bt_date}")

if st.sidebar.button("📊 RUN BACKTEST"):

    bt_results = []
    breakout_bt_list = []
    target_list = [bt_stock_input] if bt_stock_input else stocks

    with st.spinner("Running Backtest..."):
        for s in target_list:
            try:
                df_hist = yf.Ticker(s + ".NS").history(
                    start=bt_date,
                    end=bt_date + timedelta(days=1),
                    interval="15m"
                )
                df_hist = df_hist.between_time("09:15", "15:30")

                if not df_hist.empty:
                    # 🔍 Normal Backtest Signals
                    for i in range(5, len(df_hist)):
                        sub_df = df_hist.iloc[:i+1]
                        res = analyze_data(sub_df)
                        if res:
                            signal = res[1]
                            bt_results.append({
                                "Time": sub_df.index[-1].strftime('%H:%M'),
                                "Stock": s,
                                "Signal": signal,
                                "Big Player": res[2],
                                "Entry": res[3],
                                "SL": res[4],
                                "Target": res[5],
                                "Trend Score": res[6],
                                "Direction": get_direction(signal)
                            })

                    # 🔥 Breakout Logic (Backtest)
                    opening_data = df_hist.between_time("09:15", "09:30")
                    if not opening_data.empty:
                        opening_high = opening_data['High'].max()
                        opening_low = opening_data['Low'].min()

                        for i in range(1, len(df_hist)-3):
                            prev = df_hist.iloc[i-1]
                            curr = df_hist.iloc[i]
                            time = df_hist.index[i]
                            price = curr['Close']

                            if prev['Close'] <= opening_high and curr['Close'] > opening_high:
                                future = df_hist.iloc[i+1:i+4]
                                up = sum(future['Close'] > curr['Close'])
                                down = sum(future['Close'] <= curr['Close'])
                                signal_type = "🚀 CONFIRMED BUY" if up > down else "⚠️ FAILED BUY → SELL"

                                breakout_bt_list.append({
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
                                future = df_hist.iloc[i+1:i+4]
                                down = sum(future['Close'] < curr['Close'])
                                up = sum(future['Close'] >= curr['Close'])
                                signal_type = "💀 CONFIRMED SELL" if down > up else "⚠️ FAILED SELL → BUY"

                                breakout_bt_list.append({
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
