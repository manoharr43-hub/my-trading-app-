import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
# ఇక్కడ మోడల్‌ని కొంచెం అప్‌డేట్ చేశాను వేగం కోసం
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ (Optimized for Speed)
def fetch_questions_fast(subject):
    # AI కి సింపుల్ అండ్ డైరెక్ట్ ఇన్స్ట్రక్షన్స్
    prompt = f"""
    You are a Senior JEE Mains Expert. 
    Task: Scan the uploaded JEE Previous Year Papers (especially 2025 Jan shifts).
    Generate 5 high-quality MCQs for {subject}.
    Logic: Provide a VERY DETAILED LONG solution for each question.
    Format: Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2... Step 3..."}}].
    Do not include any extra text or markdown.
    """
    try:
        # response_mime_type వాడటం వల్ల JSON పక్కాగా వస్తుంది
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        return []

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MASTER")
st.caption("Latest PYQs with Deep Logical Solutions")

menu = st.radio("మెనూ:", ["📝 Practice Session", "📜 Progress Report"], horizontal=True)

if menu == "📝 Practice Session":
    sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])
    
    if st.button("🚀 Start Deep Practice", use_container_width=True):
        with st.spinner("ఫైల్స్ విశ్లేషిస్తోంది... దయచేసి ఒక్క నిమిషం ఆగండి."):
            questions = fetch_questions_fast(sub)
            if questions:
                st.session_state.ai_questions = questions
                st.session_state.q_no = 0
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.warning("AI కొంచెం ఎక్కువ టైమ్ తీసుకుంటోంది. దయచేసి మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

    if st.session_state.ai_questions:
        if st.session_state.q_no < len(st.session_state.ai_questions):
            q = st.session_state.ai_questions[st.session_state.q_no]
            st.divider()
            st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
            st.info(q['question'])
            
            ans = st.radio("నీ సమాధానం:", q['options'], key=f"ans_{st.session_state.q_no}")

            if st.button("🔍 Check Answer & See Deep Logic", use_container_width=True):
                st.session_state.show_ans = True

            if st.session_state.show_ans
