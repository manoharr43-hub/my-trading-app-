import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from xgboost import XGBClassifier
import warnings

# Warnings suppress
warnings.filterwarnings('ignore')

# ==========================================
# 1. PAGE SETUP & CONFIGURATION
# ==========================================
st.set_page_config(page_title="NSE AI PRO V11.10", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .css-1r6slp0 { padding: 2rem; }
    .stSidebar { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 NSE AI PRO V11.10 - Institutional Ultimate")
st.markdown("**Perfect Signal Time Tracker | RVOL System | Advanced SMC & CISD | XGBoost AI**")
st.markdown("---")

# Session State Memory
if 'v11_master_data' not in st.session_state:
    st.session_state.v11_master_data = pd.DataFrame()

# ==========================================
# 2. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings & Controls")
    auto_refresh = st.checkbox("🔄 Auto Refresh (Every 3 Mins)")
    interval = st.selectbox("Interval", ["5m","15m","30m","1h","1d"], index=1)
    period = st.selectbox("Period", ["5d","1mo","3mo","6mo", "1y"], index=2) # 3mo default
    
    sector_stocks = {
        "Banking": ["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
        "IT": ["TCS","INFY","WIPRO","HCLTECH","TECHM"],
        "Pharma": ["SUNPHARMA","CIPLA","DIVISLAB","DRREDDY"],
        "Energy": ["RELIANCE","ONGC","BPCL","NTPC"],
        "Auto": ["TATAMOTORS","M&M","EICHERMOT","HEROMOTOCO"],
        "FMCG": ["ITC","HINDUNILVR","BRITANNIA","DABUR"]
    }
    sector = st.selectbox("Sector", ["All NSE500"] + list(sector_stocks.keys()))
    
    st.markdown("---")
    run_button = st.button("🚀 RUN ULTIMATE SCANNER", type="primary", use_container_width=True)

# ==========================================
# 3. CORE MATHEMATICS & AI ENGINE
# ==========================================
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        import requests
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        df = pd.read_csv(io.StringIO(response.text))
        return sorted(df["Symbol"].dropna().unique().tolist())
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK","TRAVELFOOD","SYRMA","SBICARD"]

stocks = load_nse500()

@st.cache_data(ttl=120)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS" if "^" not in symbol else symbol, interval=interval, period=period, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

def predict_trend_ai(prices):
    if len(prices) < 20: return "Neutral", 0
    y = prices[-20:].values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    correlation = np.corrcoef(x, y)[0,1]
    confidence = min(round(abs(correlation) * 100, 2), 99)
    if slope > 0 and confidence > 50: return "UP 🚀", confidence
    elif slope < 0 and confidence > 50: return "DOWN 🔻", confidence
    else: return "SIDEWAYS ➖", confidence

def calculate_smc_and_cisd(df):
    if len(df) < 30: return "Range ➖", "None", "Normal", "N/A"
    try:
        df = df.copy()
        df['Prev_High'] = df['High'].shift(1)
        df['Prev_Low'] = df['Low'].shift(1)
        df['Bullish_CISD'] = (df['Low'] < df['Prev_Low']) & (df['Close'] > df['Prev_High'])
        df['Bearish_CISD'] = (df['High'] > df['Prev_High']) & (df['Close'] < df['Prev_Low'])
        
        df['Local_High'] = df['High'].rolling(window=10).max().shift(1)
        df['Local_Low'] = df['Low'].rolling(window=10).min().shift(1)
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['Bullish_Trend'] = df['EMA20'] > df['EMA50']
        
        df['Break_Up'] = df['Close'] > df['Local_High']
        df['Break_Down'] = df['Close'] < df['Local_Low']
        
        recent_df = df.tail(20)
        cisd_events = recent_df[recent_df['Bullish_CISD'] | recent_df['Bearish_CISD']]
        cisd_signal = "None"
        cisd_time_str = "N/A"
        
        if not cisd_events.empty:
            last_cisd_idx = cisd_events.index[-1]
            is_bull = cisd_events['Bullish_CISD'].iloc[-1]
            cisd_signal = "Bullish CISD 🚀" if is_bull else "Bearish CISD 🩸"
            cisd_time_str = last_cisd_idx.strftime("%d-%b %I:%M %p")
            
        smc_events = recent_df[recent_df['Break_Up'] | recent_df['Break_Down']]
        smc_structure = "Range ➖"
        smc_time_str = "N/A"
        smc_alert = "Normal"
        
        if not smc_events.empty:
            last_smc_idx = smc_events.index[-1]
            is_up = smc_events['Break_Up'].iloc[-1]
            is_bull_trend = smc_events['Bullish_Trend'].iloc[-1]
            
            if is_up:
                smc_structure = "BOS 📈" if is_bull_trend else "CHOCH 🐂"
                smc_alert = "Structure Broken Upward"
            else:
                smc_structure = "BOS 📉" if not is_bull_trend else "CHOCH 🐻"
                smc_alert = "Trend Reversal Bearish"
            smc_time_str = last_smc_idx.strftime("%d-%b %I:%M %p")
            
        final_time = "N/A"
        if cisd_signal != "None": final_time = cisd_time_str
        elif smc_structure != "Range ➖": final_time = smc_time_str
            
        return smc_structure, cisd_signal, smc_alert, final_time
    except:
        return "Range ➖", "None", "Normal", "N/A"

def train_xgboost_predictor(df):
    if len(df) < 50: return "Neutral", 0.0
    try:
        df_ml = df.copy()
        df_ml['Hour'] = df_ml.index.hour
        df_ml['Minute'] = df_ml.index.minute
        df_ml['Return'] = df_ml['Close'].pct_change()
        df_ml['RSI_Norm'] = df_ml['RSI'] / 100.0
        df_ml['Vol_Ratio'] = df_ml['Volume'] / df_ml['AVG_VOL']
        df_ml['EMA_Gap'] = (df_ml['EMA20'] - df_ml['EMA50']) / df_ml['EMA50']
        df_ml['Target_Direction'] = np.where(df_ml['Close'].shift(-1) > df_ml['Close'], 1, 0)
        df_ml.dropna(inplace=True)
        
        if len(df_ml) < 30: return "Neutral", 0.0
        feature_cols = ['Return', 'RSI_Norm', 'Vol_Ratio', 'EMA_Gap', 'Hour', 'Minute']
        X = df_ml[feature_cols].values
        y = df_ml['Target_Direction'].values
        
        model = XGBClassifier(n_estimators=25, max_depth=4, learning_rate=0.05, eval_metric='logloss', random_state=42)
        model.fit(X[:-1], y[:-1])
        
        latest_vector = X[-1].reshape(1, -1)
        prediction = model.predict(latest_vector)[0]
        probabilities = model.predict_proba(latest_vector)[0]
        confidence = round(probabilities[prediction] * 100, 2)
        
        return "BULLISH 🚀" if prediction == 1 else "BEARISH 🔻", confidence
    except:
        return "Neutral", 0.0

def calculate_supertrend(df, period=10, multiplier=3):
    high, low, close = df['High'], df['Low'], df['Close']
    tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    atr = tr.rolling(window=period).mean()
    hl2 = (high + low) / 2
    upperband, lowerband = hl2 + (multiplier * atr), hl2 - (multiplier * atr)
    supertrend, direction = np.zeros(len(df)), np.zeros(len(df))
    
    for i in range(1, len(df)):
        if close.iloc[i] > upperband.iloc[i-1]: direction[i] = 1
        elif close.iloc[i] < lowerband.iloc[i-1]: direction[i] = -1
        else: direction[i] = direction[i-1]
            
        if direction[i] == 1:
            lowerband.iloc[i] = max(lowerband.iloc[i], lowerband.iloc[i-1])
            supertrend[i] = lowerband.iloc[i]
        else:
            upperband.iloc[i] = min(upperband.iloc[i], upperband.iloc[i-1])
            supertrend[i] = upperband.iloc[i]
    df['Supertrend'], df['ST_Direction'] = supertrend, direction
    return df

def get_candlestick_pattern(df):
    if len(df) < 2: return "None"
    O1, C1 = df['Open'].iloc[-2], df['Close'].iloc[-2]
    O2, C2, H2, L2 = df['Open'].iloc[-1], df['Close'].iloc[-1], df['High'].iloc[-1], df['Low'].iloc[-1]
    body = abs(C2 - O2)
    rng = H2 - L2 if (H2 - L2) > 0 else 0.001
    if body <= (rng * 0.1): return "Doji"
    if C1 < O1 and C2 > O2 and O2 < C1 and C2 > O1: return "Bullish Engulfing"
    if C1 > O1 and C2 < O2 and O2 > C1 and C2 < O1: return "Bearish Engulfing"
    lower_shadow, upper_shadow = min(O2, C2) - L2, H2 - max(O2, C2)
    if lower_shadow > 2 * body and upper_shadow < 0.2 * body: return "Hammer"
    return "Normal"

def add_indicators(df, interval):
    if len(df) < 60: return df
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    delta = df["Close"].diff()
    df["RSI"] = 100 - (100 / (1 + (delta.clip(lower=0).ewm(com=13, adjust=False).mean() / -delta.clip(upper=0).ewm(com=13, adjust=False).mean())))
    df["MACD_Line"] = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()
    df["Signal_Line"] = df["MACD_Line"].ewm(span=9, adjust=False).mean()
    
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    if 'd' not in interval and 'wk' not in interval and 'mo' not in interval:
        df['Date'] = df.index.date
        df['VWAP'] = (df['Volume'] * tp).groupby(df['Date']).cumsum() / df['Volume'].groupby(df['Date']).cumsum()
    else:
        df['VWAP'] = (df['Volume'] * tp).rolling(20).sum() / df['Volume'].rolling(20).sum()

    df = calculate_supertrend(df)
    df['Pivot'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
    df['Resistance_1'] = (2 * df['Pivot']) - df['Low'].shift(1)
    df['Support_1'] = (2 * df['Pivot']) - df['High'].shift(1)
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()
    return df

# ==========================================
# 4. MASTER PROCESSOR THREAD
# ==========================================
def process_stock_thread(symbol, interval, period, h52w, l52w, nifty_return, daily_close_series):
    df = get_data(symbol, interval, period)
    if df.empty or len(df) < 60: return None
    df = add_indicators(df, interval)
    close = float(df["Close"].iloc[-1])
    score = 0
    
    stock_return = ((close - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    rs_score = round(stock_return - nifty_return, 2) if nifty_return is not None else 0
    rs_status = "💪 Outperform" if rs_score > 0 else "📉 Underperform"

    ai_trend, ai_conf = predict_trend_ai(df["Close"])
    xgb_prediction, xgb_confidence = train_xgboost_predictor(df)
    smc_structure, cisd_signal, smc_alert, exact_signal_time = calculate_smc_and_cisd(df)
    
    mtf_status = "Not Aligned"
    if daily_close_series is not None and len(daily_close_series) >= 50:
        d_ema20 = daily_close_series.ewm(span=20, adjust=False).mean().iloc[-1]
        d_ema50 = daily_close_series.ewm(span=50, adjust=False).mean().iloc[-1]
        if (d_ema20 > d_ema50) == (df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]):
            mtf_status = "ALIGNED 🟢" if (d_ema20 > d_ema50) else "ALIGNED 🔻"

    alerts = []
    rvol_val = 0.0
    avg_vol = float(df["AVG_VOL"].iloc[-1])
    current_vol = float(df["Volume"].iloc[-1])
    
    if pd.notna(avg_vol) and avg_vol > 0:
        rvol_val = current_vol / avg_vol
        
    rvol_str = f"{rvol_val:.2f}x"
    if rvol_val >= 2.0:
        rvol_str += " 🔥"
        alerts.append("🔥 High RVOL")
    elif rvol_val >= 1.5:
        rvol_str += " 🟢"
        
    rsi_val = float(df["RSI"].iloc[-1])
    if rsi_val > 70: alerts.append("🚨 RSI Overbought")
    elif rsi_val < 30: alerts.append("⚠️ RSI Oversold")
    if smc_alert != "Normal": alerts.append(f"🏛️ {smc_structure}")
    if cisd_signal != "None": alerts.append(f"⚡ {cisd_signal}")
    
    breakout_high = df["High"].rolling(20).max().shift(1).iloc[-1]
    breakout_low = df["Low"].rolling(20).min().shift(1).iloc[-1]
    brk_sig = "NO"
    if close > breakout_high: brk_sig, _ = "BULLISH", alerts.append("📈 Breakout High")
    elif close < breakout_low: brk_sig, _ = "BEARISH", alerts.append("📉 Breakout Low")
        
    pattern = get_candlestick_pattern(df)
    if pattern in ["Bullish Engulfing", "Hammer"]: alerts.append(f"✨ {pattern}")
    alert_str = ", ".join(alerts) if alerts else "No Alerts"

    macd_val = "BULLISH" if df["MACD_Line"].iloc[-1] > df["Signal_Line"].iloc[-1] else "BEARISH"
    st_dir = "UP" if df["ST_Direction"].iloc[-1] == 1 else "DOWN"
    vwap_sig = "ABOVE" if close > float(df["VWAP"].iloc[-1]) else "BELOW"
    
    if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]: score += 1
    else: score -= 1
    if rsi_val > 55: score += 1
    elif rsi_val < 45: score -= 1
    if macd_val == "BULLISH": score += 1
    else: score -= 1
    if st_dir == "UP": score += 1
    else: score -= 1
    if vwap_sig == "ABOVE": score += 1
    else: score -= 1
    if brk_sig == "BULLISH": score += 1
    elif brk_sig == "BEARISH": score -= 1
    if smc_structure in ["BOS 📈", "CHOCH 🐂"] or cisd_signal == "Bullish CISD 🚀": score += 1

    signal = "STRONG BUY" if score >= 4
