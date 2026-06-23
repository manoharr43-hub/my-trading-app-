import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import io, time, base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 1. PAGE SETUP
# ==========================================
st.set_page_config(page_title="NSE AI PRO V11.12", layout="wide", page_icon="🚀")
st.title("🚀 NSE AI PRO V11.12 - Institutional Hybrid")
st.markdown("**CISD/SMC Timing | Gap Momentum | VWAP Bounce | RVOL System | XGBoost AI**")
st.markdown("---")

if 'v11_master_data' not in st.session_state:
    st.session_state.v11_master_data = pd.DataFrame()

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Settings & Controls")
    auto_refresh = st.checkbox("🔄 Auto Refresh (Every 3 Mins)")
    interval = st.selectbox("Interval", ["5m","15m","30m","1h","1d"], index=1)
    period = st.selectbox("Period", ["5d","1mo","3mo","6mo","1y"], index=2)
    sector_stocks = {
        "Banking":["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK"],
        "IT":["TCS","INFY","WIPRO","HCLTECH","TECHM"],
        "Pharma":["SUNPHARMA","CIPLA","DIVISLAB","DRREDDY"],
        "Energy":["RELIANCE","ONGC","BPCL","NTPC"],
        "Auto":["TATAMOTORS","M&M","EICHERMOT","HEROMOTOCO"],
        "FMCG":["ITC","HINDUNILVR","BRITANNIA","DABUR"]
    }
    sector = st.selectbox("Sector", ["All NSE500"] + list(sector_stocks.keys()))
    st.markdown("---")
    run_button = st.button("🚀 RUN ULTIMATE SCANNER", type="primary", use_container_width=True)

# ==========================================
# 3. CORE FUNCTIONS
# ==========================================
@st.cache_data(ttl=86400)
def load_nse500():
    try:
        import requests
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent':'Mozilla/5.0'}
        df = pd.read_csv(io.StringIO(requests.get(url,headers=headers,timeout=5).text))
        return sorted(df["Symbol"].dropna().unique().tolist())
    except:
        return ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","ITC","LT","AXISBANK"]

stocks = load_nse500()

@st.cache_data(ttl=120)
def get_data(symbol, interval, period):
    try:
        df = yf.download(f"{symbol}.NS" if "^" not in symbol else symbol, interval=interval, period=period, auto_adjust=True, progress=False)
        if isinstance(df.columns,pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def add_indicators(df, interval):
    if len(df)<60: return df
    df["EMA20"]=df["Close"].ewm(span=20).mean()
    df["EMA50"]=df["Close"].ewm(span=50).mean()
    delta=df["Close"].diff()
    df["RSI"]=100-(100/(1+(delta.clip(lower=0).ewm(com=13).mean()/-delta.clip(upper=0).ewm(com=13).mean())))
    df["MACD_Line"]=df["Close"].ewm(span=12).mean()-df["Close"].ewm(span=26).mean()
    df["Signal_Line"]=df["MACD_Line"].ewm(span=9).mean()
    tp=(df['High']+df['Low']+df['Close'])/3
    if 'd' not in interval:
        df['Date']=df.index.date
        df['VWAP']=(df['Volume']*tp).groupby(df['Date']).cumsum()/df['Volume'].groupby(df['Date']).cumsum()
    else:
        df['VWAP']=(df['Volume']*tp).rolling(20).sum()/df['Volume'].rolling(20).sum()
    df["AVG_VOL"]=df["Volume"].rolling(20).mean()
    df['ATR']=(df[['High','Low','Close']].max(axis=1)-df[['High','Low','Close']].min(axis=1)).rolling(14).mean()
    return df

def train_xgboost_predictor(df):
    if len(df)<50: return "Neutral",0.0
    try:
        df_ml=df.copy()
        df_ml['Hour']=df_ml.index.hour if hasattr(df_ml.index,'hour') else 0
        df_ml['Minute']=df_ml.index.minute if hasattr(df_ml.index,'minute') else 0
        for col in ['Close','Volume','RSI','AVG_VOL','EMA20','EMA50']:
            df_ml[col]=pd.to_numeric(df_ml[col],errors='coerce')
        df_ml['Return']=df_ml['Close'].pct_change()
        df_ml['RSI_Norm']=df_ml['RSI']/100.0
        df_ml['Vol_Ratio']=np.where(df_ml['AVG_VOL']>0,df_ml['Volume']/df_ml['AVG_VOL'],1.0)
        df_ml['EMA_Gap']=np.where(df_ml['EMA50']>0,(df_ml['EMA20']-df_ml['EMA50'])/df_ml['EMA50'],0.0)
        df_ml['Target_Direction']=np.where(df_ml['Close'].shift(-1)>df_ml['Close'],1,0)
        df_ml.replace([np.inf,-np.inf],np.nan,inplace=True)
        df_ml.dropna(inplace=True)
