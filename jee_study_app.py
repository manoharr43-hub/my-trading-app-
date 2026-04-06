import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్ (Gemini 1.5 Flash - ఇది చాలా వేగంగా ఉంటుంది)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ (Optimized for Speed)
def fetch_questions_instantly(subject):
    prompt = f"""
    Act as a JEE Mains Expert. 
    Use the uploaded PYQ files for {subject}.
    Generate 5 CHALLENGING MCQs strictly for JEE Mains.
    Requirement: Provide a VERY DEEP, LONG STEP-BY-STEP solution for each.
    Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2..."}}].
    Do not use markdown.
    """
    try:
        # response_mime_type ని JSON కి సెట్ చేయడం వల్ల AI చాలా వేగంగా స్పందిస్తుంది
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
st.caption("Optimized Speed Mode | Strictly JEE Mains Solutions")

sub_choice = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్
if st.button("🚀 Start JEE Mains Practice Session", use_container_width=True):
    with st.spinner("AI విశ్లేషిస్తోంది... దయచేసి ఒక్క 5 సెకన్లు ఆగండి."):
        # ఒకేసారి 5 ప్రశ్నలు లోడ్ అయిపోతాయి
        qs = fetch_questions_instantly(sub_choice)
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
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 లోతైన వివరణ (Detailed Solution):", expanded=True):
                st.write(q['explanation'])
            
            # ఇక్కడ 'Next' నొక్కితే మళ్ళీ లోడింగ్ ఉండదు, వెంటనే వస్తుంది
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! ఈ సెషన్ పూర్తి చేసావు.")
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం JEE Mains ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Focus: Strictly JEE Mains")
