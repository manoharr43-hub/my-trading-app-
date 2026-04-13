import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="🔥 NSE AI Scanner PRO MAX", layout="wide")

# =============================
# BACKTEST SETTINGS (NEW)
# =============================
st.sidebar.title("📅 Data Settings")

days = st.sidebar.selectbox("Select Period", ["5d", "7d", "1mo", "3mo"])
interval = st.sidebar.selectbox("Select Interval", ["5m", "15m", "30m", "1h"])

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# AI ANALYSIS
# =============================
def analyze(df):
    if df is None or len(df) < 40:
        return None

    df = df.copy()

    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['VWAP'] = (df['Close']*df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    delta = df['Close'].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100/(1+rs))

    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    df.dropna(inplace=True)

    if len(df) < 10:
        return None

    X = df[['EMA20','EMA50','RSI','VWAP']]
    y = df['Target']

    X_train, _, y_train, _ = train_test_split(X,y,test_size=0.2,shuffle=False)

    model = RandomForestClassifier(n_estimators=50,max_depth=5,random_state=42)
    model.fit(X_train,y_train)

    pred = model.predict(X.iloc[[-1]])[0]
    signal = "BUY" if pred==1 else "SELL"

    avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = df['Volume'].iloc[-1]/avg_vol if avg_vol>0 else 1

    big_player = "Big Buyer" if vol_ratio>2 else ("Big Seller" if vol_ratio<0.5 else "")

    return df, signal, big_player

# =============================
# SUPPORT RESISTANCE
# =============================
def support_resistance(df):
    closes = df['Close'].tail(50)
    return round(closes.min(),2), round(closes.max(),2)

# =============================
# HIGHLIGHT FIX
# =============================
def get_highlight(price, support, resistance, signal):
    range_val = price * 0.01

    if abs(price-support) <= range_val and signal=="BUY":
        return "🟢 Near Support"
    elif abs(price-resistance) <= range_val and signal=="SELL":
        return "🔴 Near Resistance"
    else:
        return ""

# =============================
# TRADE LEVELS
# =============================
def trade_levels(price, support, resistance, signal):

    if signal=="BUY":
        risk = price - support
        entry = round(price + 0.5,2)
        stoploss = round(support,2)
        target1 = round(entry + risk,2)
        target2 = round(entry + (risk*2),2)

    else:
        risk = resistance - price
        entry = round(price - 0.5,2)
        stoploss = round(resistance,2)
        target1 = round(entry - risk,2)
        target2 = round(entry - (risk*2),2)

    return entry, stoploss, target1, target2

# =============================
# SCANNER
# =============================
def run_scanner(tickers):

    results=[]

    try:
        data = yf.download(tickers, period=days, interval=interval, group_by='ticker', progress=False)
    except:
        return pd.DataFrame()

    for s in tickers:
        try:
            df = data.copy() if len(tickers)==1 else data[s].copy()
            df = df.dropna()

            if df.empty or "Close" not in df.columns:
                continue

            result = analyze(df)
            if result is None:
                continue

            df, signal, big_player = result

            price = round(df['Close'].iloc[-1],2)

            change_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            trend = "UP" if change_pct>0 else "DOWN"

            support, resistance = support_resistance(df)

            entry, stoploss, target1, target2 = trade_levels(price, support, resistance, signal)
            highlight = get_highlight(price, support, resistance, signal)

            results.append({
                "Ticker": s,
                "Price": price,
                "AI Signal": signal,
                "Trend": trend,
                "Support": support,
                "Resistance": resistance,
                "Entry": entry,
                "Stoploss": stoploss,
                "Target1": target1,
                "Target2": target2,
                "Big Player": big_player,
                "Highlight": highlight
            })

        except:
            continue

    return pd.DataFrame(results)

# =============================
# DISPLAY
# =============================
def show_table(df, title):
    st.subheader(title)

    if df.empty:
        st.warning("⚠️ No data found.")
    else:
        df_display = df.copy()
        df_display['AI Signal'] = df_display['AI Signal'].apply(lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL")
        df_display['Trend'] = df_display['Trend'].apply(lambda x: "🟢 UP" if x=="UP" else "🔴 DOWN")
        st.dataframe(df_display, hide_index=True)

# =============================
# MAIN UI
# =============================
st.title("🔥 NSE AI Scanner PRO MAX (Backtest Enabled)")

all_stocks = [t for sec in sectors.values() for t in sec]

if st.button("🚀 Run Scanner"):
    df = run_scanner(all_stocks)
    show_table(df, "📊 AI Signals with Backtest Data")
