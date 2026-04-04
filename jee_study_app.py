import streamlit as st
import google.generativeai as genai
import json
import random

# 1. Gemini AI సెటప్
# ఇక్కడ మీ API KEY ని పేస్ట్ చేయండి
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="Sai Rakshith AI Exam Center", layout="wide")

# 2. Gemini ద్వారా ప్రశ్నలు తయారు చేసే ఫంక్షన్
def fetch_ai_questions(subject, level):
    prompt = f"""
    Generate 5 high-quality {level} questions for {subject}.
    Format the output as a JSON list of objects with these keys:
    'question', 'options' (list of 4), 'answer' (exact string from options), 'explanation'.
    Ensure questions are unique and challenging for a 2nd year student.
    """
    try:
        response = model.generate_content(prompt)
        # AI ఇచ్చే టెక్స్ట్ నుండి JSON ని ఎక్స్‌ట్రాక్ట్ చేయడం
        data = json.loads(response.text.replace('```json', '').replace('```', ''))
        return data
    except:
        st.error("AI కనెక్ట్ అవ్వడంలో ఇబ్బందిగా ఉంది. దయచేసి API Key చెక్ చేయండి.")
        return []

# 3. సెషన్ స్టేట్
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ స్క్రీన్
st.sidebar.title("🤖 AI EXAM GENERATOR")
sub = st.sidebar.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
lvl = st.sidebar.radio("Level", ["JEE Mains", "JEE Advanced"])

if st.sidebar.button("Generate New AI Exam"):
    with st.spinner("Gemini AI ప్రశ్నలను తయారు చేస్తోంది..."):
        st.session_state.ai_questions = fetch_ai_questions(sub, lvl)
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.show_ans = False
        st.rerun()

st.title("🎓 SAI RAKSHITH'S AI PREP CENTER")
st.markdown("---")

if st.session_state.ai_questions:
    questions = st.session_state.ai_questions
    curr = questions[st.session_state.q_no]
    
    st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
    st.subheader(curr['question'])
    
    user_choice = st.radio("Choose Option:", curr['options'], key=f"ai_q_{st.session_state.q_no}")

    if st.button("✅ Check Answer"):
        st.session_state.show_ans = True

    if st.session_state.show_ans:
        if user_choice == curr['answer']:
            st.success(f"కరెక్ట్ ఆన్సర్! ✨ \n\n **వివరణ:** {curr['explanation']}")
        else:
            st.error(f"తప్పు! సరైన ఆన్సర్: {curr['answer']} \n\n **వివరణ:** {curr['explanation']}")
        
        if st.button("Next Question ➡️"):
            if user_choice == curr['answer']: st.session_state.score += 1
            if st.session_state.q_no < len(questions) - 1:
                st.session_state.q_no += 1
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.balloons()
                st.success(f"ప్రాక్టీస్ పూర్తయింది! స్కోర్: {st.session_state.score}/{len(questions)}")
                st.session_state.ai_questions = [] # Reset
else:
    st.write("పక్కన ఉన్న 'Generate New AI Exam' బటన్ నొక్కి ఎగ్జామ్ స్టార్ట్ చేయండి.")

st.divider()
st.caption("AI Engine Powered by Gemini - Managed by Manohar (Variety Motors)")
