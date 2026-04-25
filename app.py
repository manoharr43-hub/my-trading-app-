# =============================
# AFTER LIVE RESULTS
# =============================
if st.session_state.live_res:

    df_res = pd.DataFrame(st.session_state.live_res)

    # SORTING LOGIC
    priority = {
        "🚀 STRONG BUY": 1,
        "BUY": 2,
        "⚠️ WAIT": 3,
        "SELL": 4,
        "💀 STRONG SELL": 5
    }

    df_res["Rank"] = df_res["FINAL"].map(priority)
    df_res = df_res.sort_values("Rank")

    # SPLIT STRONG / WEAK
    strong = df_res[df_res["FINAL"] == "🚀 STRONG BUY"]
    weak = df_res[df_res["FINAL"] == "💀 STRONG SELL"]

    st.subheader("🚀 STRONG BUY STOCKS")
    if not strong.empty:
        st.dataframe(strong.drop(columns=["Rank"]), use_container_width=True)
    else:
        st.info("No Strong Buy Stocks")

    st.subheader("💀 STRONG SELL STOCKS")
    if not weak.empty:
        st.dataframe(weak.drop(columns=["Rank"]), use_container_width=True)
    else:
        st.info("No Strong Sell Stocks")

    st.subheader("📊 ALL LIVE SIGNALS")
    st.dataframe(df_res.drop(columns=["Rank"]), use_container_width=True)

    # BREAKOUT
    df_bo = pd.DataFrame(st.session_state.live_bo)

    st.subheader("🔥 LIVE BREAKOUT")
    if not df_bo.empty:
        st.dataframe(df_bo.drop(columns=["DateTime"]), use_container_width=True)
    else:
        st.info("No Breakouts Today")

    # CHART
    stock = st.selectbox("📈 Live Chart", df_res["Stock"].unique())

    df_chart = yf.Ticker(stock + ".NS").history(period="1d", interval="5m")
    df_chart = df_chart.between_time("09:15","15:30")

    plot_chart(df_chart, stock, breakout_engine(df_chart, stock))
