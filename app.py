import streamlit as st
from streamlit_autorefresh import st_autorefresh

# =============================
# AUTO REFRESH
# =============================
count = st_autorefresh(interval=60000, key="refresh")  # 60 sec

st.title("🔄 Auto Refresh Test")

st.write(f"Refresh count: {count}")

# =============================
# MANUAL REFRESH BUTTON
# =============================
if st.button("🔄 Refresh Now"):
    st.rerun()
