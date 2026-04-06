import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Super Fast Response
def fetch_questions_instant():
    # ఇక్కడ AI కి చాలా డైరెక్ట్ గా ఇన్స్ట్రక్షన్ ఇచ్చాను వేగం కోసం
    prompt = """
    Act as a Senior JEE Mains Expert. 
    Generate 5 HIGH-QUALITY MCQs strictly for JEE MAINS level. 
    Mix: Physics, Chemistry, Mathematics.
    Requirement: For each question, provide a VERY LONG, STEP-BY-STEP SOLUTION.
    Format: Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step Solution..."}].
    Do not use markdown like ```json.
    """
    try:
        # JSON మోడ్ వాడటం వల్ల ఎర్రర్లు రావు
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
st.caption("Super Fast Mode: Instant Questions with Long Solutions")

st.divider()

if st.button("🚀 START JEE MAINS PRACTICE (INSTANT LOAD)", use_container_width=True):
    with st.spinner("ప్రశ్నలను సిద్ధం చేస్తోంది..."):
        # ఇక్కడ నేరుగా ప్రశ్నలు వచ్చేస్తాయి
        qs = fetch_questions_instant()
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("ఒక్కసారి మళ్ళీ బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution"):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 లోతైన వివరణ (Detailed Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️"):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! ఈ సెషన్ పూర్తి చేసావు.")
        st.session_state.mains_bank = []
