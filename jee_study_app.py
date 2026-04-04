import streamlit as st
import requests
import random

# 1. పేజీ సెటప్
st.set_page_config(page_title="Sai Rakshith JEE Exam Center", layout="wide")

# 2. ఆటోమేటిక్ ప్రశ్నలు తెచ్చే ఫంక్షన్ (API నుండి)
@st.cache_data(ttl=600) # 10 నిమిషాల వరకు డేటాను గుర్తుంచుకుంటుంది
def fetch_auto_questions():
    # ఇది ఒక ఉచిత ఇంటర్నెట్ క్విజ్ డేటాబేస్ (Science & Maths కోసం)
    url = "https://opentdb.com/api.php?amount=10&category=19&type=multiple"
    try:
        response = requests.get(url)
        data = response.json()
        raw_questions = data['results']
        
        formatted_questions = []
        for q in raw_questions:
            opts = q['incorrect_answers'] + [q['correct_answer']]
            random.shuffle(opts)
            formatted_questions.append({
                "question": q['question'],
                "options": opts,
                "answer": q['correct_answer'],
                "explanation": "This is an auto-generated science question for practice."
            })
        return formatted_questions
    except:
        # ఒకవేళ ఇంటర్నెట్ స్లోగా ఉంటే ఈ బ్యాకప్ ప్రశ్నలు కనిపిస్తాయి
        return [
            {"question": "What is the unit of Force?", "options": ["Newton", "Joule", "Watt", "Volt"], "answer": "Newton", "explanation": "Force is measured in Newtons."},
            {"question": "Value of sin(90)?", "options": ["0", "1", "-1", "0.5"], "answer": "1", "explanation": "Trigonometric value of sin(90) is 1."}
        ]

# 3. సైడ్ బార్ సెటప్
st.sidebar.title("🏥 JEE AUTO-EXAM")
st.sidebar.info("మనోహర్ గారు, ఇక్కడ ప్రశ్నలు ఆటోమేటిక్‌గా ఇంటర్నెట్ నుండి వస్తాయి.")

# సబ్జెక్ట్ సెలెక్షన్ (ప్రస్తుతానికి సైన్స్/మ్యాథ్స్ కలిపి వస్తాయి)
subject = st.sidebar.selectbox("Subject", ["Physics & Maths (Auto)", "Chemistry (Auto)"])

# 4. సెషన్ స్టేట్ (ప్రశ్నలు గుర్తుంచుకోవడానికి)
if 'auto_questions' not in st.session_state:
    st.session_state.auto_questions = fetch_auto_questions()
if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'done' not in st.session_state: st.session_state.done = False

# 5. మెయిన్ స్క్రీన్
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown("---")

if not st.session_state.done:
    current_q = st.session_state.auto_questions[st.session_state.q_idx]
    
    st.subheader(f"Question {st.session_state.q_idx + 1}:")
    st.write(current_q['question'])
    
    user_choice = st.radio("Choose Option:", current_q['options'], key=f"q_{st.session_state.q_idx}")

    if st.button("Submit & Next ➡️"):
        if user_choice == current_q['answer']:
            st.session_state.score += 1
        
        if st.session_state.q_no < len(st.session_state.auto_questions) - 1:
            st.session_state.q_idx += 1
            st.rerun()
        else:
            st.session_state.done = True
            st.rerun()
else:
    # రిజల్ట్ బోర్డ్
    st.success("🎉 ఎగ్జామ్ పూర్తయింది, సాయి రక్షిత్!")
    st.metric("మీ స్కోర్", f"{st.session_state.score} / {len(st.session_state.auto_questions)}")
    
    if st.button("కొత్త ప్రశ్నలతో మళ్ళీ రాయండి (Fetch New Questions)"):
        st.session_state.auto_questions = fetch_auto_questions()
        st.session_state.q_idx = 0
        st.session_state.score = 0
        st.session_state.done = False
        st.rerun()

st.divider()
st.caption("Auto-Question Engine Powered by Manohar - Variety Motors")
