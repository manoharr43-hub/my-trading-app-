import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# ==========================================
# CONFIG & TIMEZONE
# ==========================================
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)

st.title("📥 NSE 200 - AUTO EXCEL GENERATOR")

# NSE 200 STOCKS LIST (Sample)
nse_200 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "BHARTIARTL", "HINDUNILVR", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN", "HCLTECH", "ADANIENT", "SUNPHARMA", "TATASTEEL",
    "WIPRO", "ULTRACEMCO", "NTPC", "JSWSTEEL", "POWERGRID", "M&M", "ONGC", "HINDALCO", "TATAMOTORS", "ADANIPORTS",
    "COALINDIA", "GRASIM", "BAJAJFINSV", "BRITANNIA", "EICHERMOT", "DIVISLAB", "CIPLA", "TECHM", "NESTLEIND", "BPCL"
]

def add_indicators(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Support'] = df['Low'].rolling(20).min()
    df['Resistance'] = df['High'].rolling(20).max()
    # ATR for SL/Target
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    return df

# ==========================================
# EXCEL GENERATION LOGIC
# ==========================================
if st.button("🚀 GENERATE & DOWNLOAD EXCEL"):
    with st.spinner("200 స్టాక్స్ డేటా ప్రాసెస్ అవుతోంది..."):
        tickers = [s + ".NS" for s in nse_200]
        data = yf.download(tickers, period="2d", interval="5m", group_by="ticker", threads=True)
        
        final_list = []

        for s in nse_200:
            try:
                df = data[s+".NS"].dropna()
                if len(df) < 20: continue
                df = add_indicators(df)
                
                row = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Signal Logic
                signal = None
                if row['Close'] <= row['Support'] * 1.002: signal = "BUY (SUPPORT)"
                elif row['Close'] >= row['Resistance'] * 0.998: signal = "SELL (RESISTANCE)"
                elif prev['Close'] < prev['EMA20'] and row['Close'] > row['EMA20']: signal = "BUY (CROSSOVER)"
                elif prev['Close'] > prev['EMA20'] and row['Close'] < row['EMA20']: signal = "SELL (CROSSOVER)"
                
                if signal:
                    # SL & Target Calculation (Based on ATR)
                    entry = round(row['Close'], 2)
                    atr = row['ATR']
                    sl = round(entry - (atr * 1.5), 2) if "BUY" in signal else round(entry + (atr * 1.5), 2)
                    target = round(entry + (atr * 2), 2) if "BUY" in signal else round(entry - (atr * 2), 2)
                    
                    final_list.append({
                        "SYMBOL": s,
                        "TIME": df.index[-1].tz_convert(IST).strftime('%H:%M'),
                        "SIGNAL": signal,
                        "ENTRY": entry,
                        "STOPLOSS": sl,
                        "TARGET": target,
                        "VOL_SURGE": "YES" if row['Volume'] > df['Volume'].rolling(20).mean().iloc[-1]*2 else "NO"
                    })
            except: continue

        if final_list:
            df_final = pd.DataFrame(final_list)
            
            # Displaying a small preview
            st.success(f"మొత్తం {len(final_list)} సిగ్నల్స్ లభించాయి.")
            st.dataframe(df_final.head()) 

            # Direct Excel/CSV Download
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 CLICK HERE TO DOWNLOAD EXCEL (CSV)",
                data=csv_data,
                file_name=f"NSE_Signals_{now.strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("ప్రస్తుతానికి ఎటువంటి సిగ్నల్స్ లేవు.")
