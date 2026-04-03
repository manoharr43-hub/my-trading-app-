import streamlit as st
import yfinance as yf
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Nifty 50 SMC Scanner", layout="wide", page_icon="🎯")

st.title("🎯 Nifty 50 SMC Pro Max - Auto Filter")
st.caption("Variety Motors Edition - నిఫ్టీ 50 లోని బెస్ట్ స్టాక్స్ ని మాత్రమే చూపిస్తుంది")

# Nifty 50 Stock List
nifty50_stocks = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
    "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
]

if st.button("🚀 Start Nifty 50 Scan"):
    all_results = []
    signals_only = []
    
    status = st.empty()
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(nifty50_stocks):
        status.info(f"Scanning {symbol}... ({i+1}/50)")
        try:
            df = yf.download(symbol, period="1mo", interval="15m", progress=False)
            
            if df is not None and len(df) > 30:
                # Indicators
                ema9 = df['Close'].ewm(span=9, adjust=False).mean()
                ema21 = df['Close'].ewm(span=21, adjust=False).mean()
                vwap = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
                vol_ma = df['Volume'].rolling(window=20).mean()

                # Current Values
                price = df['Close'].iloc[-1].item()
                cur_ema9 = ema9.iloc[-1].item()
                cur_ema21 = ema21.iloc[-1].item()
                cur_vwap = vwap.iloc[-1].item()
                cur_vol = df['Volume'].iloc[-1].item()
                cur_vol_ma = vol_ma.iloc[-1].item()
                
                prev_ema9 = ema9.iloc[-2].item()
                prev_ema21 = ema21.iloc[-2].item()

                # SMC V18 Logic
                is_vol_high = cur_vol > cur_vol_ma
                is_buy = (prev_ema9 <= prev_ema21 and cur_ema9 > cur_ema21) and (price > cur_vwap) and is_vol_high
                is_sell = (prev_ema9 >= prev_ema21 and cur_ema9 < cur_ema21) and (price < cur_vwap) and is_vol_high

                if is_buy or is_sell:
                    signal = "🚀 STRONG BUY" if is_buy else "🔻 STRONG SELL"
                    signals_only.append({
                        "Stock": symbol.replace(".NS", ""),
                        "LTP": round(price, 2),
                        "Signal": signal,
                        "Volume": "High 🔥"
                    })
        except:
            continue
        progress_bar.progress((i + 1) / 50)

    status.empty()
    
    st.subheader("🔥 Top Trading Opportunities (Filtered)")
    if signals_only:
        res_df = pd.DataFrame(signals_only)
        # Displaying the filtered results
        st.success(f"మనోహర్ గారు, 50 స్టాక్స్ లో {len(signals_only)} స్టాక్స్ మీ కండిషన్స్ కి మ్యాచ్ అయ్యాయి!")
        st.table(res_df)
    else:
        st.warning("ప్రస్తుతానికి ఏ స్టాక్ కూడా మీ SMC V18 కండిషన్స్ కి మ్యాచ్ అవ్వలేదు. 'WAIT' లో ఉండండి.")

st.markdown("---")
st.info("💡 ఈ స్కానర్ కేవలం నిఫ్టీ 50 లోని 'Buy' లేదా 'Sell' సిగ్నల్స్ ఉన్న వాటిని మాత్రమే ఏరి చూపిస్తుంది.")
