import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - 100% JEE Mains Focus
def fetch_mains_questions(subject):
    prompt = f"""
    Act as a JEE Mains Professor. 
    TASK: Analyze the uploaded PDF papers from your database.
    Generate 5 HIGH-QUALITY MCQs strictly for JEE MAINS level for {subject}.
    Logic: Provide a VERY DEEP, LONG mathematical explanation for each answer. 
    Show step-by-step how to solve it.
    Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2..."}}].
    Do not use markdown.
    """
    try:
        # response_mime_type వాడటం వల్ల ఎర్రర్లు రావు
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Target: JEE Mains Success | Detailed PYQ Solutions")

# సబ్జెక్ట్ ఎంపిక
sub_choice = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్ నొక్కినప్పుడు ప్రశ్నలు లోడ్ అవుతాయి
if st.button("🚀 Start JEE Mains Practice Session", use_container_width=True):
    with st.spinner("ఫైల్స్ విశ్లేషించి ప్రశ్నలను సిద్ధం చేస్తోంది..."):
        # వేగం కోసం 10 కి బదులు 5 ప్రశ్నలు అడుగుతున్నాను (తర్వాతి బటన్ లో ఇంకో 5 వస్తాయి)
        qs = fetch_mains_questions(sub_choice)
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("AI స్పందించడం లేదు. మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / {len(st.session_state.mains_bank)}:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"mains_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution", use_container_width=True):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Deep Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("తర్వాతి ప్రశ్న ➡️", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! ఈ సెషన్ లోని ముఖ్యమైన JEE Mains ప్రశ్నలు పూర్తి చేసావు.")
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం JEE Mains ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Focus: Strictly JEE Mains")
