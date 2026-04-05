import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్ (మీ కొత్త కీ ఇక్కడ ఉంది)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mentor", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - 1st & 2nd Year Mixed Syllabus
def fetch_mixed_questions(subject, level):
    prompt = f"""
    Create 5 tough JEE {level} MCQs mixing 1st and 2nd year {subject} syllabus.
    Focus on the patterns of the last 10 years papers.
    For each question, provide a VERY DETAILED STEP-BY-STEP EXPLANATION.
    Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed steps..."}}].
    Do not use markdown like ```json.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except:
        # బ్యాకప్ ప్రశ్నలు (Error రాకుండా)
        return [
            {"question": "Physics: Unit of Magnetic Flux?", "options": ["Weber", "Tesla", "Henry", "Farad"], "answer": "Weber", "explanation": "Step 1: Magnetic flux is B*A. Step 2: SI unit is Weber (Wb). Step 3: Tesla is for Magnetic Field Intensity."},
            {"question": "Maths: Derivative of log(x)?", "options": ["1/x", "exp(x)", "x", "1"], "answer": "1/x", "explanation": "Step 1: Use basic differentiation rule. Step 2: d/dx of ln(x) is always 1/x."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH'S JEE ACADEMY")
st.caption("Mixed 1st & 2nd Year Syllabus | Last 10 Years PYQs")

menu = st.radio("మెనూ:", ["📝 ఎగ్జామ్ రాయండి", "📜 పాత రిపోర్ట్స్"], horizontal=True)

if menu == "📝 ఎగ్జామ్ రాయండి":
    sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])
    lvl = st.radio("లెవల్:", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Start 10-Year Mixed Exam", use_container_width=True):
        with st.spinner("AI 10 ఏళ్ల డేటాని విశ్లేషిస్తోంది..."):
            new_qs = fetch_mixed_questions(sub, lvl)
            if new_qs:
                st.session_state.ai_questions = new_qs
                st.session_state.q_no = 0
                st.session_state.show_ans = False
                st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
        st.info(q['question'])
        
        choice = st.radio("ఆప్షన్ ఎంచుకో బాబు:", q['options'], key=f"q_{st.session_state.q_no}")

        if st.button("🔍 Check Answer & Deep Logic", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if choice == q['answer']: st.success("శభాష్! కరెక్ట్ ఆన్సర్! ✅")
            else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 లోతైన వివరణ (Detailed Explanation):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                if st.session_state.q_no < 4:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Sub": sub, "Level": lvl})
                    st.balloons()
                    st.success("ఈరోజు సెషన్ పూర్తయింది! వెరీ గుడ్ బాబు!")
                    st.session_state.ai_questions = []
    else:
        st.write("పై బటన్ నొక్కి 10 ఏళ్ల మిక్సెడ్ సిలబస్ ప్రాక్టీస్ మొదలుపెట్టండి.")

else:
    st.subheader("📜 నీ ప్రోగ్రెస్ రిపోర్ట్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.write("ఇంకా ఏమీ రాయలేదు.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Dedicated to Sai Rakshith's Future")
