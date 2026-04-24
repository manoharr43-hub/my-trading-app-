import streamlit as st
import pandas as pd
import pyotp
from datetime import datetime
from NorenRestApiPy import NorenApi
import time

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🤖 AUTO TRADING BOT", layout="wide")
st.title("🤖 NSE AUTO BUY/SELL BOT")

# =============================
# USER INPUT (SAFE)
# =============================
user_id = st.text_input("User ID")
password = st.text_input("Password", type="password")
api_secret = st.text_input("API Secret", type="password")
totp_key = st.text_input("TOTP Key", type="password")

enable_live = st.checkbox("⚠️ Enable LIVE Trading (Danger)")

# =============================
# API CLASS
# =============================
class ShoonyaApiPy(NorenApi):
    def __init__(self):
        super().__init__(
            host='https://api.shoonya.com/NorenWClientTP/',
            websocket='wss://api.shoonya.com/NorenWSTP/'
        )

# =============================
# LOGIN
# =============================
def login():
    api = ShoonyaApiPy()
    otp = pyotp.TOTP(totp_key).now()

    ret = api.login(
        userid=user_id,
        password=password,
        twoFA=otp,
        vendor_code="FA",
        api_secret=api_secret,
        imei="abc1234"
    )
    return api

# =============================
# STRATEGY
# =============================
def generate_signal(df):
    e20 = df['close'].ewm(span=20).mean()
    e50 = df['close'].ewm(span=50).mean()

    if e20.iloc[-1] > e50.iloc[-1]:
        return "BUY"
    elif e20.iloc[-1] < e50.iloc[-1]:
        return "SELL"
    return "WAIT"

# =============================
# ORDER FUNCTION
# =============================
def place_order(api, symbol, side, qty):
    try:
        order = api.place_order(
            buy_or_sell='B' if side == "BUY" else 'S',
            product_type='MIS',
            exchange='NSE',
            tradingsymbol=symbol,
            quantity=qty,
            discloseqty=0,
            price_type='MKT',
            retention='DAY'
        )
        return order
    except Exception as e:
        return str(e)

# =============================
# BOT RUN
# =============================
if st.button("🚀 START BOT"):

    api = login()
    st.success("✅ Logged in")

    stocks = ["RELIANCE","TCS","INFY"]

    while True:
        results = []

        for s in stocks:
            try:
                data = api.get_time_price_series(
                    exchange='NSE',
                    token=s,
                    starttime=int(time.time()) - 3600
                )

                df = pd.DataFrame(data)
                df['close'] = df['lp'].astype(float)

                signal = generate_signal(df)

                if signal != "WAIT":
                    msg = f"{s} → {signal}"
                    st.write(msg)

                    # ================= LIVE ORDER =================
                    if enable_live:
                        order = place_order(api, s, signal, qty=1)
                        st.write(f"ORDER: {order}")

            except Exception as e:
                st.error(f"{s} Error: {e}")

        time.sleep(60)
