# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("📊 Select NSE Sector")
    sector_name = st.selectbox("Sector", list(sectors.keys()))
    st.header("📌 Top 10 Big Movers")
    show_movers = st.checkbox("Show Top 10 Movers Across All Sectors")

    st.header("🔎 Enter Symbol (NSE use .NS)")
    user_symbol = st.text_input("Enter NSE Stock Symbol", value="")
