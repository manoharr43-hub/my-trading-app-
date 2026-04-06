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

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - All Subjects Mixed
def fetch_mixed_mains_questions():
    prompt = """
    Act as a JEE Mains Professor. 
    Task: Scan all uploaded PYQ papers (2025 and previous years).
    Generate 5 CHALLENGING MCQs strictly for JEE Mains level.
    Mix: Include questions from Physics, Chemistry, and Mathematics (randomly mixed).
    Requirement: Provide a VERY LONG, STEP-BY-STEP mathematical solution for each answer.
    Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2..."}].
    Do not use markdown.
    """
    try:
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
st.caption("Mixed Subjects Mode | Strictly JEE Mains PYQs")

st.divider()

# సబ్జెక్ట్ సెలెక్షన్ తీసేసి నేరుగా బటన్ పెట్టాను
if st.button("🚀 START JEE MAINS PRACTICE (MIXED SUBJECTS)", use_container_width=True):
    with st.spinner("అన్ని సబ్జెక్టుల పేపర్లను విశ్లేషిస్తోంది... దయచేసి ఒక్క 5-10 సెకన్లు ఆగండి."):
        qs = fetch_mixed_mains_questions()
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.warning("AI కొంచెం బిజీగా ఉంది. ఒక్కసారి మళ్ళీ బటన్ నొక్కండి.")

# ప్రశ్నలు ప్రదర్శించే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"mains_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution", use_container_width=True):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("శభాష్! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 లోతైన వివరణ (Detailed Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! ఈ మిశ్రమ సబ్జెక్టుల ప్రాక్టీస్ పూర్తి చేసావు.")
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం అన్ని సబ్జెక్టుల నుండి ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Focus: Strictly JEE Mains Mixed")
