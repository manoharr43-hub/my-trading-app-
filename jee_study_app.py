import streamlit as st

# App Title
st.set_page_config(page_title="Babu's JEE Academy", page_icon="🎓")
st.title("🎓 BABU'S JEE STUDY APP")
st.write("ఇంటర్మీడియట్ 1st & 2nd Year ప్రాక్టీస్ కోసం ప్రత్యేకంగా..")

# Sidebar for Year Selection
st.sidebar.header("Select Year")
year = st.sidebar.radio("ఏ సంవత్సరం చదువుతున్నారు?", ["1st Year", "2nd Year"])

# Sidebar for Subject Selection
st.sidebar.header("Select Subject")
subject = st.sidebar.selectbox("సబ్జెక్టు ఎంచుకోండి", ["Physics", "Chemistry", "Mathematics"])

st.subheader(f"📍 {year} - {subject}")

# --- 1st Year Logic ---
if year == "1st Year":
    if subject == "Physics":
        st.info("Question: What is the unit of Power?")
        if st.button('Show Answer'):
            st.success("Answer: Watt (వాట్) ✅")
            
    elif subject == "Chemistry":
        st.info("Question: Atomic number of Hydrogen?")
        if st.button('Show Answer'):
            st.success("Answer: 1 ✅")
            
    elif subject == "Mathematics":
        st.info("Question: Value of sin(90°)?")
        if st.button('Show Answer'):
            st.success("Answer: 1 ✅")

# --- 2nd Year Logic ---
elif year == "2nd Year":
    if subject == "Physics":
        st.info("Question: Lens formula emiti?")
        if st.button('Show Answer'):
            st.success("Answer: 1/f = 1/v - 1/u ✅")
            
    elif subject == "Chemistry":
        st.info("Question: Benzene formula emiti?")
        if st.button('Show Answer'):
            st.success("Answer: C6H6 ✅")
            
    elif subject == "Mathematics":
        st.info("Question: Derivative of x² (d/dx of x²)?")
        if st.button('Show Answer'):
            st.success("Answer: 2x ✅")

st.divider()
st.caption("All the best, Babu! చదువు మీద దృష్టి పెట్టండి. 👍")
