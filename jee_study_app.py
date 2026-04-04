import streamlit as st

st.set_page_config(page_title="Sai Rakshith JEE Prep", layout="wide")

# 1. సైడ్ బార్ సెటప్ (Year, Subject, Exam Type)
st.sidebar.title("🎓 JEE LEARNING HUB")
year = st.sidebar.selectbox("Select Year", ["1st Year", "2nd Year"])
subject = st.sidebar.radio("Select Subject", ["Mathematics", "Physics", "Chemistry"])
exam_type = st.sidebar.selectbox("Exam Level", ["JEE Mains", "JEE Advanced"])

st.title(f"🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown(f"### 📍 {year} - {subject} | {exam_type}")

# 2. ప్రశ్నల డేటాబేస్ (Example Questions)
data = {
    "2nd Year": {
        "Physics": {
            "JEE Mains": [
                {"q": "Ideal Ammeter resistance?", "options": ["Zero", "Low", "High", "Infinite"], "answer": "Zero"},
                {"q": "Unit of Capacitance?", "options": ["Volt", "Farad", "Ohm", "Henry"], "answer": "Farad"}
            ],
            "JEE Advanced": [
                {"q": "Current in a superconductor is?", "options": ["Zero", "Infinite", "Constant", "Decreasing"], "answer": "Constant"}
            ]
        },
        "Mathematics": {
            "JEE Mains": [
                {"q": "Derivative of sin(x)?", "options": ["cos(x)", "-cos(x)", "tan(x)", "sec(x)"], "answer": "cos(x)"}
            ]
        }
    }
}

# 3. Session State (ప్రశ్నలు మరియు మార్కుల కోసం)
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'completed' not in st.session_state: st.session_state.completed = False

# సబ్జెక్ట్ లేదా ఎగ్జామ్ మారితే రీసెట్ చేయడం
current_key = f"{year}_{subject}_{exam_type}"
if 'last_key' not in st.session_state or st.session_state.last_key != current_key:
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.last_key = current_key

# 4. క్విజ్ లాజిక్
try:
    questions = data[year][subject][exam_type]
    
    if not st.session_state.completed:
        current_q = questions[st.session_state.q_no]
        st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
        st.subheader(current_q['q'])
        
        user_choice = st.radio("Choose Option:", current_q['options'], key=f"opt_{st.session_state.q_no}")

        if st.button("Submit & Next"):
            if user_choice == current_q['answer']:
                st.session_state.score += 1
            
            if st.session_state.q_no < len(questions) - 1:
                st.session_state.q_no += 1
                st.rerun()
            else:
                st.session_state.completed = True
                st.rerun()
    else:
        # 5. రిజల్ట్ మరియు మార్కులు చూపించడం
        st.success(f"🎉 ప్రాక్టీస్ పూర్తయింది, సాయి రక్షిత్!")
        total = len(questions)
        st.metric(label="మీ స్కోర్ (Total Marks)", value=f"{st.session_state.score} / {total}")
        
        if st.button("మళ్ళీ ప్రాక్టీస్ చేయండి (Restart)"):
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.completed = False
            st.rerun()

except KeyError:
    st.warning(f"సారీ, {year} {subject} {exam_type} లో ప్రస్తుతం ప్రశ్నలు లేవు. త్వరలో యాడ్ చేస్తాము!")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
