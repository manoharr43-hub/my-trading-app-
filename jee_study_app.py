import streamlit as st

# టైటిల్ మరియు డిజైన్
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown("### 📍 2nd Year - Physics | JEE Mains")

# 1. ప్రశ్నల లిస్ట్ (ఇక్కడ మరిన్ని ప్రశ్నలు యాడ్ చేసుకోవచ్చు)
questions = [
    {
        "q": "Ideal Ammeter resistance?",
        "options": ["Zero", "Low", "High", "Infinite"],
        "answer": "Zero"
    },
    {
        "q": "Unit of Capacitance?",
        "options": ["Volt", "Farad", "Ohm", "Henry"],
        "answer": "Farad"
    },
    {
        "q": "Ohm's Law is valid for?",
        "options": ["Insulators", "Semiconductors", "Conductors", "Diodes"],
        "answer": "Conductors"
    }
]

# 2. Session State ని సెట్ చేయడం (ప్రశ్నల నంబర్ గుర్తుంచుకోవడానికి)
if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

# ప్రస్తుతం ఏ ప్రశ్న చూపిస్తున్నామో అది
current_q = questions[st.session_state.q_no]

# 3. ప్రశ్నను చూపించడం
with st.container():
    st.info(f"Question {st.session_state.q_no + 1}: {current_q['q']}")
    
    user_choice = st.radio("Choose Option:", current_q['options'], key=f"q_{st.session_state.q_no}")

# 4. బటన్స్ సెటప్ (Next & Previous)
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.session_state.q_no > 0:
        if st.button("⬅️ Previous"):
            st.session_state.q_no -= 1
            st.rerun()

with col3:
    if st.session_state.q_no < len(questions) - 1:
        if st.button("Next Question ➡️"):
            st.session_state.q_no += 1
            st.rerun()
    else:
        st.success("🎉 మీరు అన్ని ప్రశ్నలు పూర్తి చేశారు!")

# 5. సబ్మిట్ బటన్ (ఆన్సర్ కరెక్టో కాదో చెప్పడానికి)
if st.button("Submit Answer"):
    if user_choice == current_q['answer']:
        st.success("✅ కరెక్ట్ ఆన్సర్! వెల్డన్ సాయి రక్షిత్!")
    else:
        st.error(f"❌ తప్పు ఆన్సర్. సరైన సమాధానం: {current_q['answer']}")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
