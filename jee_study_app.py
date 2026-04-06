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

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Strictly JEE Mains
def fetch_mains_questions(subject):
    prompt = f"""
    You are a Senior JEE Mains Professor. 
    Task: Scan all uploaded PDF papers (2025 Jan shifts and previous years).
    Generate 10 HIGH-QUALITY MCQs strictly for JEE Mains level for {subject}.
    Logic: Provide a VERY DEEP, LONG mathematical explanation for each answer. 
    Explain why other options are wrong if necessary.
    Format: Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Concept: ... Step 1: ... Step 2: ... Step 3: ..."}}].
    Do not use markdown.
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Focus: JEE Mains PYQs | Deep Logical Solutions | 10 Question Sets")

selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])

# బటన్ నొక్కితే 10 ప్రశ్నలు ఒకేసారి వస్తాయి
if st.button("🚀 Prepare 10 Mains Questions (Instant)", use_container_width=True):
    with st.spinner("అన్ని సంవత్సరాల పేపర్లను విశ్లేషించి 10 ప్రశ్నలు సిద్ధం చేస్తోంది..."):
        mains_qs = fetch_mains_questions(selected_sub)
        if mains_qs:
            st.session_state.mains_bank = mains_qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.warning("AI స్పందించడం లేదు. మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు ప్రదర్శించే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 10:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"mains_{curr}")

        if st.button("🔍 Check Answer & See Long Solution", use_container_width=True):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("అద్భుతం! కరెక్ట్ ఆన్సర్! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Detailed Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! 10 ముఖ్యమైన Mains ప్రశ్నలు పూర్తి చేసావు.")
        st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Sub": selected_sub})
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం 10 Mains ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Dedicated to Sai Rakshith's JEE Mains Success")
