import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Fast-Track", layout="centered")

# 2. ప్రశ్నల బ్యాంక్ ని ముందే సిద్ధం చేసే ఫంక్షన్
def prepare_question_bank(subject):
    prompt = f"""
    Analyze all uploaded PYQs (2025 Jan shift, 2024, etc.) for {subject}.
    Generate a set of 10 tough JEE Mains MCQs at once.
    Each question must have a VERY DEEP, LONG STEP-BY-STEP SOLUTION.
    Format: Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2..."}}].
    Do not use markdown.
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్ (పాత డేటాని భద్రపరచడానికి)
if 'history' not in st.session_state: st.session_state.history = []
if 'question_bank' not in st.session_state: st.session_state.question_bank = []
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE FAST-TRACK")
st.caption("Continuous Processing: No Waiting Time for Questions")

sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])

# ప్రశ్నలు లోడ్ చేసే బటన్
if st.button("🚀 Prepare Exam Paper (Fast Load)", use_container_width=True):
    with st.spinner("AI ప్రశ్నలను సిద్ధం చేస్తోంది... ఒక్క నిమిషం ఆగండి."):
        bank = prepare_question_bank(sub)
        if bank:
            st.session_state.question_bank = bank
            st.session_state.current_idx = 0
            st.session_state.show_ans = False
            st.rerun()

# బాబుకి ప్రశ్నలు చూపించే విధానం
if st.session_state.question_bank:
    idx = st.session_state.current_idx
    if idx < len(st.session_state.question_bank):
        q = st.session_state.question_bank[idx]
        st.divider()
        st.subheader(f"ప్రశ్న {idx + 1} / {len(st.session_state.question_bank)}:")
        st.info(q['question'])
        
        ans = st.radio("నీ సమాధానం:", q['options'], key=f"q_{idx}")

        if st.button("🔍 Check Answer & Detailed Logic", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if ans == q['answer']: st.success("శభాష్! కరెక్ట్! ✅")
            else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Deep Explanation):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.current_idx += 1
                st.session_state.show_ans = False
                st.rerun()
    else:
        st.balloons()
        st.success("ఈ సెషన్ లోని అన్ని ప్రశ్నలు పూర్తి చేసావు! వెరీ గుడ్ బాబు!")
        st.session_state.question_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. AI నీ కోసం 10 ప్రశ్నలను ముందే సిద్ధం చేసి ఉంచుతుంది.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Ensuring Smooth Learning for Sai Rakshith")
