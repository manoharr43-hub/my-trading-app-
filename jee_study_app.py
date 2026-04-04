import streamlit as st

# 1. బాబు పేరు మరియు టైటిల్ సెటప్
st.set_page_config(page_title="Sai Rakshith JEE Prep", layout="wide")
st.sidebar.title("🎓 JEE LEARNING HUB")

# 2. Sidebar లో Year మరియు Subject ఎంచుకునే ఆప్షన్
year = st.sidebar.selectbox("Select Year", ["1st Year", "2nd Year"])
subject = st.sidebar.radio("Select Subject", ["Mathematics", "Physics", "Chemistry"])

st.title(f"🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown(f"### 📍 {year} - {subject} | JEE Mains")

# 3. ప్రశ్నల డేటాబేస్ (నమూనా కోసం కొన్ని ప్రశ్నలు)
# దీన్ని మనం రేపు గూగుల్ షీట్ కి కనెక్ట్ చేద్దాం
data = {
    "2nd Year": {
        "Physics": [
            {"q": "Ideal Ammeter resistance?", "options": ["Zero", "Low", "High", "Infinite"], "answer": "Zero"},
            {"q": "Unit of Capacitance?", "options": ["Volt", "Farad", "Ohm", "Henry"], "answer": "Farad"}
        ],
        "Mathematics": [
            {"q": "Derivative of sin(x)?", "options": ["cos(x)", "-cos(x)", "tan(x)", "sec(x)"], "answer": "cos(x)"}
        ],
        "Chemistry": [
            {"q": "PH of pure water?", "options": ["5", "7", "9", "1"], "answer": "7"}
        ]
    },
    "1st Year": {
        "Physics": [
            {"q": "Dimensional formula of Force?", "options": ["MLT-2", "ML2T-2", "MLT-1", "ML-1T-2"], "answer": "MLT-2"}
        ]
    }
}

# 4. ప్రశ్నలను చూపించే లాజిక్ (Session State)
if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

# ఎంచుకున్న ఇయర్ & సబ్జెక్ట్ లో ప్రశ్నలు ఉన్నాయో లేదో చెక్ చేయడం
if year in data and subject in data[year]:
    questions = data[year][subject]
    
    # ఒకవేళ సబ్జెక్ట్ మారితే ప్రశ్నను మళ్ళీ 0 కి సెట్ చేయడం
    if 'current_sub' not in st.session_state or st.session_state.current_sub != f"{year}_{subject}":
        st.session_state.q_no = 0
        st.session_state.current_sub = f"{year}_{subject}"

    current_q = questions[st.session_state.q_no]

    # ప్రశ్న ప్రదర్శన
    st.info(f"Question {st.session_state.q_no + 1}: {current_q['q']}")
    user_choice = st.radio("Choose Option:", current_q['options'], key=f"{year}_{subject}_{st.session_state.q_no}")

    # Navigation Buttons
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

    if st.button("Submit Answer"):
        if user_choice == current_q['answer']:
            st.success("✅ కరెక్ట్ ఆన్సర్! వెల్డన్ సాయి రక్షిత్!")
        else:
            st.error(f"❌ తప్పు ఆన్సర్. సరైన సమాధానం: {current_q['answer']}")
else:
    st.warning(f"సారీ, {year} {subject} లో ప్రస్తుతం ప్రశ్నలు అందుబాటులో లేవు.")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
