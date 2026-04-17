@@ -0,0 +1,29 @@
import streamlit as st
import requests

BASE_URL = "https://api.shoonya.com/NorenWClient"
CLIENT_ID = "FA189165_U"
SECRET_KEY = "fHYIfEf8A3cHQGONHONKb2XyGjnI7nLDfQbm2AEkyIAy2cf9QdAAgeODl9YB6myN"

def shoonya_login():
    payload = {
        "uid": CLIENT_ID,
        "pwd": "your_password",
        "factor2": "your_TOTP_or_PIN",
        "vc": "your_vendor_code",
        "apikey": SECRET_KEY,
        "appkey": SECRET_KEY,
        "imei": "your_device_id",
        "algoid": "MANOHAR_AI_SCANNER"
    }
    res = requests.post(BASE_URL + "/QuickAuth", data=payload)
    return res.json()

# Streamlit UI
st.title("🚀 MANOHAR NSE AI PRO TERMINAL (Shoonya API)")
login_data = shoonya_login()

if login_data.get("susertoken"):
    st.success("Shoonya API Login Successful ✅")
else:
    st.error("Login Failed ❌")
