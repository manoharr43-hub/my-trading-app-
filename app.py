import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from streamlit_autorefresh import st_autorefresh

# =============================
# PAGE CONFIG + AUTO REFRESH
# =============================
st.set_page_config(page_title="🔥 NSE PRO AI SCANNER", layout="wide")
st_autorefresh(interval=20000, key="refresh")

# =============================
# NSE SECTORS
# =============================
sectors = {
    "Nifty 50": ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"],
    "Banking": ["SBIN.NS","HDFCBANK.NS","ICICIBANK.NS","AXISBANK.NS","KOTAKBANK.NS","PNB.NS"],
    "IT": ["INFY.NS","TCS.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS"],
    "Auto": ["TATAMOTORS.NS","MARUTI.NS","M&M.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharma": ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS"],
    "FMCG": ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS"],
    "Energy": ["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS"],
    "Metal": ["TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS","COALINDIA.NS"]
}

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    st.header("📌 Top 10 Big Movers")
    show_big = st.checkbox("Show Top 10 Movers Across All Sectors")

# =============================
# COLOR FUNCTIONS
# =============================
def color_signal(val):
    if "BUY" in str(val):
        return "background-color: green; color: white"
    elif "SELL" in str(val):
        return "background-color: red; color: white"
    return ""

def color_trend(val):
    if val == "UP":
        return "background-color: green; color: white"
    elif val == "DOWN":
        return "background-color: red; color: white"
    return ""

# =============================
# AI ANALYSIS
# =============================
def analyze(df):
    try:
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
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        df.dropna(inplace=True)
        if len(df) < 10:
            return None
        features = ['EMA20','EMA50','RSI','VWAP']
        X = df[features]
        y = df['Target']
        X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,shuffle=False)
        model = RandomForestClassifier(n_estimators=50,max_depth=5,random_state=42)
        model.fit(X_train,y_train)
        acc = round(model.score(X_test,y_test)*100,2)
        pred = model.predict(X.iloc[[-1]])[0]
        ai_signal = "BUY" if pred==1 else "SELL"
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = df['Volume'].iloc[-1]/avg_vol if avg_vol>0 else 1
        return df, vol_ratio, ai_signal, acc
    except:
        return None

# =============================
# RUN SCANNER
# =============================
def run_scanner(tickers):
    results=[]
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()
    for s in tickers:
        try:
            df = data.copy() if len(tickers)==1 else data[s].copy()
            df = df.dropna()
            if df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            res = analyze(df)
            if res is None:
                continue
            df, vol, ai, acc = res
            last = df.iloc[-1]
            ltp = float(last['Close'])
            ema20 = float(last['EMA20'])
            ema50 = float(last['EMA50'])
            rsi = float(last['RSI'])
            vwap = float(last['VWAP'])
            trend = "UP" if ema20>ema50 else "DOWN"
            signal="WAIT"
            if ltp>vwap and trend=="UP" and rsi>50 and ai=="BUY":
                signal="🔥 BUY"
            elif ltp<vwap and trend=="DOWN" and rsi<50 and ai=="SELL":
                signal="🔥 SELL"
            results.append({
                "Stock":s.replace(".NS",""),
                "Price":round(ltp,2),
                "Trend":trend,
                "RSI":round(rsi,1),
                "Volume":round(vol,2),
                "AI":ai,
                "Accuracy":acc,
                "Signal":signal
            })
        except:
            continue
    return pd.DataFrame(results)

# =============================
# TOP 10 BIG MOVERS
# =============================
def get_top_10_movers(sectors_dict):
    combined=[]
    for tickers in sectors_dict.values():
        df = run_scanner(tickers)
        if df.empty:
            continue
        for col in ['Signal','Trend','Price','Stock','AI','Accuracy','Volume']:
            if col not in df.columns:
                df[col]=np.nan
        df['Change']=df['Price']-df['Price'].shift(1)
        df['PctChange']=df['Change']/df['Price'].shift(1)*100
        df.fillna(0,inplace=True)
        combined.append(df)
    if combined:
        all_stocks=pd.concat(combined)
        all_stocks['AbsPctChange']=all_stocks['PctChange'].abs()
        top10=all_stocks.sort_values(by='AbsPctChange',ascending=False).head(10)
        return top10
    return pd.DataFrame()

# =============================
# MAIN UI
# =============================
st.title("🔥 NSE PRO AI SCANNER (NEW FULL VERSION)")
st.write(f"📊 Sector: {sector_name}")

# Scanner per sector
df=run_scanner(sectors[sector_name])
if not df.empty:
    st.subheader("🚀 Live Signals")
    styled_df=df.style.map(color_signal,subset=['Signal']).map(color_trend,subset=['Trend'])
    st.dataframe(styled_df,use_container_width=True)
    selected=st.selectbox("📈 Select Stock",df['Stock'])
    chart=yf.download(selected+".NS",period="1d",interval="5m",progress=False)
    if not chart.empty:
        st.line_chart(chart['Close'])
    else:
        st.warning("Chart not available")
else:
    st.warning("No signals found now")

# Show Top 10 Big Movers
if show_big:
    st.subheader("🚀 Top 10 Big Movers Across All Sectors")
    movers=get_top_10_movers(sectors)
    if not movers.empty:
        styled=movers.style.map(color_signal,subset=['Signal']).map(color_trend,subset=['Trend'])
        st.dataframe(styled,use_container_width=True)
    else:
        st.warning("No big movers found now")
