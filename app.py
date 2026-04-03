import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 Option Chain OI Strength - Variety Motors")

# Select Index
index_choice = st.selectbox("Select Index", ["^NSEI", "^NSEBANK"])
name = "NIFTY" if index_choice == "^NSEI" else "BANKNIFTY"

if st.button("🔍 Check OI Strength"):
    try:
        ticker = yf.Ticker(index_choice)
        # Get nearest expiry date
        expiry = ticker.options[0]
        opt_chain = ticker.option_chain(expiry)
        
        # 1. Calculate Call & Put OI
        total_call_oi = opt_chain.calls['openInterest'].sum()
        total_put_oi = opt_chain.puts['openInterest'].sum()
        
        # 2. Strength Calculation
        pcr = total_put_oi / total_call_oi
        
        # 3. Display Logic (మీరు అడిగినట్లు)
        st.subheader(f"📈 {name} OI Analysis (Expiry: {expiry})")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Call OI (Resistance)", f"{int(total_call_oi)}")
        col2.metric("Put OI (Support)", f"{int(total_put_oi)}")
        col3.metric("PCR Ratio", round(pcr, 2))

        # --- మీ కండిషన్ ప్రకారం సిగ్నల్ ---
        if total_call_oi > total_put_oi:
            st.error("🔻 CALL SIDE STRONG (OI): MARKET DOWN అయ్యే అవకాశం ఉంది (Resistance is Heavy)")
            st.button("📉 వ్యూ: SELL ON RISE")
        elif total_put_oi > total_call_oi:
            st.success("🚀 PUT SIDE STRONG (OI): MARKET UP అయ్యే అవకాశం ఉంది (Support is Heavy)")
            st.button("📈 వ్యూ: BUY ON DIPS")
        else:
            st.warning("⚖️ OI EQUAL: మార్కెట్ సైడ్ వేస్ (Sideways) ఉండే ఛాన్స్ ఉంది.")

    except Exception as e:
        st.error("ఆప్షన్స్ డేటా ప్రస్తుతం అందుబాటులో లేదు. కాసేపటి తర్వాత ప్రయత్నించండి.")

st.markdown("---")
st.info("💡 గమనిక: Call Side OI ఎక్కువగా ఉంటే మార్కెట్ పడటానికి, Put Side OI ఎక్కువగా ఉంటే మార్కెట్ పెరగడానికి అవకాశం ఉంటుంది.")
