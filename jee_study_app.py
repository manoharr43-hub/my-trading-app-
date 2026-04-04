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
            clean_q = q['question'].replace('&quot;', '"').replace('&#039;', "'")
            opts = [opt.replace('&quot;', '"').replace('&#039;', "'") for opt in q['incorrect_answers']]
            correct = q['correct_answer'].replace('&quot;', '"').replace('&#039;', "'")
            
            opts.append(correct)
            random.shuffle(opts)
            formatted_questions.append({
                "question": clean_q,
                "options": opts,
                "answer": correct,
                "explanation": f"The correct answer is {correct}. Practice more to understand the logic!"
            })
        return formatted_questions
    except:
        return [{"question": "What is 5+5?", "options": ["10", "11", "9", "8"], "answer": "10", "explanation": "Simple addition: 5+5 = 10."}]

# 3. సెషన్ స్టేట్
if 'auto_questions' not in st.session_state:
    st.session_state.auto_questions = fetch_auto_questions()
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'done' not in st.session_state: st.session_state.done = False
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ స్క్రీన్
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown("---")

if not st.session_state.done:
    questions = st.session_state.auto_questions
    curr = questions[st.session_state.q_no]
    
    st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
    st.subheader(curr['question'])
    
    user_choice = st.radio("Choose Option:", curr['options'], key=f"q_{st.session_state.q_no}")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Check Answer"):
            st.session_state.show_ans = True

    # ఆన్సర్ మరియు వివరణ చూపించడం
    if st.session_state.show_ans:
        if user_choice == curr['answer']:
            st.success(f"కరెక్ట్ ఆన్సర్! 👏 \n\n **వివరణ:** {curr['explanation']}")
        else:
            st.error(f"తప్పు సమాధానం! సరైనది: {curr['answer']} \n\n **వివరణ:** {curr['explanation']}")
        
        if st.button("Next Question ➡️"):
            if user_choice == curr['answer']:
                st.session_state.score += 1
            
            if st.session_state.q_no < len(questions) - 1:
                st.session_state.q_no += 1
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.session_state.done = True
                st.rerun()
else:
    st.success(f"🎉 ఎగ్జామ్ పూర్తయింది! మీ స్కోర్: {st.session_state.score} / {len(st.session_state.auto_questions)}")
    if st.button("కొత్త ప్రశ్నలతో మళ్ళీ రాయండి"):
        st.session_state.auto_questions = fetch_auto_questions()
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.done = False
        st.session_state.show_ans = False
        st.rerun()

st.divider()
st.caption("Auto-Learning System Managed by Manohar - Variety Motors")
