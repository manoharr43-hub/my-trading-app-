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

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Error Handling తో
def fetch_mixed_mains_questions():
    prompt = """
    Act as a JEE Mains Professor. Scan all uploaded papers.
    Generate 5 CHALLENGING MCQs for JEE Mains. Mix Physics, Chemistry, Maths.
    Provide a VERY LONG, STEP-BY-STEP solution for each.
    Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1..."}].
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        if response and response.text:
            return json.loads(response.text)
        return []
    except Exception as e:
        return []

# 3. సెషన్ స్టేట్ (Safety Checks యాడ్ చేశాను)
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Mixed Subjects Mode | Strictly JEE Mains")

if st.button("🚀 START JEE MAINS PRACTICE", use_container_width=True):
    with st.spinner("అన్ని సబ్జెక్టుల పేపర్లను విశ్లేషిస్తోంది..."):
        qs = fetch_mixed_mains_questions()
        if qs and len(qs) > 0:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("AI స్పందించడానికి సమయం పడుతోంది. దయచేసి ఇంకొకసారి బటన్ నొక్కండి.")

# ఇక్కడ Safety Check ఉంది - IndexError రాదు
if st.session_state.mains_bank and st.session_state.idx < len(st.session_state.mains_bank):
    curr = st.session_state.idx
    q = st.session_state.mains_bank[curr]
    st.divider()
    st.subheader(f"ప్రశ్న {curr + 1} / {len(st.session_state.mains_bank)}:")
    st.info(q['question'])
    
    choice = st.radio("నీ సమాధానం:", q['options'], key=f"mains_{curr}")

    if st.button("🔍 Check Answer & Detailed Solution"):
        st.session_state.ans_show = True

    if st.session_state.ans_show:
        if choice == q['answer']: st.success("శభాష్! సరైన సమాధానం! ✅")
        else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
        
        with st.expander("📖 లోతైన వివరణ (Detailed Solution):", expanded=True):
            st.write(q['explanation'])
        
        if st.button("Next Question ➡️"):
            st.session_state.idx += 1
            st.session_state.ans_show = False
            st.rerun()
elif not st.session_state.mains_bank:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం ప్రశ్నలు సిద్ధంగా ఉంటాయి.")
