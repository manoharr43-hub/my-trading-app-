import streamlit as st
import requests
import random

# 1. పేజీ సెటప్
st.set_page_config(page_title="Sai Rakshith JEE Exam Center", layout="wide")

# 2. ఆటోమేటిక్ ప్రశ్నలు తెచ్చే ఫంక్షన్
@st.cache_data(ttl=600)
def fetch_auto_questions():
    url = "https://opentdb.com/api.php?amount=10&category=19&type=multiple"
    try:
        response = requests.get(url)
        data = response.json()
        raw_questions = data['results']
        
        formatted_questions = []
        for q in raw_questions:
            # HTML కోడ్స్‌ని క్లీన్ చేయడం (ఉదా: &quot; ని " లా మార్చడం)
            clean_q = q['question'].replace('&quot;', '"').replace('&#039;', "'")
            opts = [opt.replace('&quot;', '"').replace('&#039;', "'") for opt in q['incorrect_answers']]
            correct = q['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")
            
            opts.append(correct)
            random.shuffle(opts)
            formatted_questions.append({
                "question": clean_q,
                "options": opts,
                "answer": correct
            })
        return formatted_questions
    except:
        return [
            {"question": "Ideal Ammeter resistance?", "options": ["Zero", "Low", "High", "Infinite"], "answer": "Zero"},
            {"question": "Value of sin(90)?", "options": ["0", "1", "-1", "0.5"], "answer": "1"}
        ]

# 3. సెషన్ స్టేట్ (రీసెట్ సమస్య లేకుండా ఉండటానికి)
if 'auto_questions' not in st.session_state:
    st.session_state.auto_questions = fetch_auto_questions()
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'done' not in st.session_state: st.session_state.done = False

# 4. మెయిన్ స్క్రీన్
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown("---")

if not st.session_state.done:
    questions = st.session_state.auto_questions
    curr = questions[st.session_state.q_no]
    
    st.subheader(f"Question {st.session_state.q_no + 1}:")
    st.write(curr['question'])
    
    user_choice = st.radio("Choose Option:", curr['options'], key=f"q_{st.session_state.q_no}")

    if st.button("Submit & Next ➡️"):
        if user_choice == curr['answer']:
            st.session_state.score += 1
        
        # ఇక్కడ తప్పు జరిగింది (q_no వాడాలి)
        if st.session_state.q_no < len(questions) - 1:
            st.session_state.q_no += 1
            st.rerun()
        else:
            st.session_state.done = True
            st.rerun()
else:
    st.success("🎉 ఎగ్జామ్ పూర్తయింది, సాయి రక్షిత్!")
    st.metric("మీ స్కోర్ (Total Marks)", f"{st.session_state.score} / {len(st.session_state.auto_questions)}")
    
    if st.button("కొత్త ప్రశ్నలతో మళ్ళీ రాయండి"):
        st.session_state.auto_questions = fetch_auto_questions()
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.done = False
        st.rerun()

st.divider()
st.caption("Auto-Exam System Managed by Manohar - Variety Motors")
