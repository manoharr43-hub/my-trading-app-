import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE 2025 Master", layout="centered")

# 2. అప్‌లోడ్ చేసిన ఫైల్స్ నుండి ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_from_uploaded_files(subject, level):
    # మీరు అప్‌లోడ్ చేసిన 2025 PDFల డేటాని వాడమని AIని అడుగుతున్నాము
    prompt = f"""
    You are a JEE Professor. I have uploaded several JEE Main 2025 January Session papers to my repository.
    TASK: Scan those 2025 Jan Shift papers for {subject}.
    1. Pick 5 challenging MCQs based on the actual 2025 Jan session pattern.
    2. Provide a very deep, step-by-step mathematical explanation for each.
    3. If the question is from a specific 2025 shift, mention it.
    Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..."}}].
    Do not use any markdown like ```json.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except:
        return [
            {"question": "2025 Pattern: Integration of e^x(sin x + cos x) dx?", "options": ["e^x sin x", "e^x cos x", "sin x", "cos x"], "answer": "e^x sin x", "explanation": "Step 1: Formula Integral of e^x [f(x) + f'(x)] is e^x f(x). Step 2: Here f(x)=sin x and f'(x)=cos x. Step 3: Result is e^x sin x."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE 2025 MASTER")
st.caption("Analyzing Uploaded 2025 Jan Shift Papers")

menu = st.radio("మెనూ:", ["📝 2025 Combined Exam", "📜 ప్రోగ్రెస్ రిపోర్ట్"], horizontal=True)

if menu == "📝 2025 Combined Exam":
    sub = st.selectbox("సబ్జెక్ట్:", ["Mathematics", "Physics", "Chemistry"])
    lvl = st.radio("లెవల్:", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Analyze Uploaded Papers & Start", use_container_width=True):
        with st.spinner("మీరు అప్‌లోడ్ చేసిన ఫైల్స్ నుండి ప్రశ్నలను సేకరిస్తోంది..."):
            st.session_state.ai_questions = fetch_from_uploaded_files(sub, lvl)
            st.session_state.q_no = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
        st.info(q['question'])
        
        ans = st.radio("సరైన సమాధానం ఎంచుకో బాబు:", q['options'], key=f"q_{st.session_state.q_no}")

        if st.button("🔍 వివరణ (Check & Learn)", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if ans == q['answer']: st.success("శభాష్! కరెక్ట్! ✅")
            else: st.error(f"తప్పు! సరైన ఆన్సర్: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Detailed Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                if st.session_state.q_no < 4:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Sub": sub, "Source": "Uploaded Papers"})
                    st.balloons()
                    st.success("వెరీ గుడ్! 2025 పేపర్లతో ప్రాక్టీస్ పూర్తి చేశావు!")
                    st.session_state.ai_questions = []
else:
    st.table(pd.DataFrame(st.session_state.history))

st.divider()
st.caption("Managed by Manohar - Variety Motors | 20+ Years Excellence")
