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

# 2. ప్రశ్నలు ముందే తయారు చేసే ఫంక్షన్
def fetch_bulk_questions(subject):
    prompt = f"""
    Analyze ALL uploaded PYQs and 2025 Jan papers for {subject}.
    Generate 10 HIGH-QUALITY JEE Mains MCQs.
    Provide a VERY LONG, STEP-BY-STEP logical explanation for each.
    Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Step 1... Step 2..."}}].
    Do not use markdown.
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్ (డేటాని దాచి ఉంచడానికి)
if 'history' not in st.session_state: st.session_state.history = []
if 'q_bank' not in st.session_state: st.session_state.q_bank = []
if 'index' not in st.session_state: st.session_state.index = 0
if 'ans_visible' not in st.session_state: st.session_state.ans_visible = False

# 4. UI
st.title("🎓 SAI RAKSHITH JEE FAST-TRACK")
st.caption("Auto-Preload Mode: Continuous Practice without Waiting")

selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])

# బటన్ నొక్కినప్పుడు 10 ప్రశ్నలు లోడ్ అవుతాయి
if st.button("🚀 Prepare 10 Questions (Instant Access)", use_container_width=True):
    with st.spinner("AI ప్రశ్నలను సిద్ధం చేస్తోంది... ఒక్క నిమిషం ఆగండి."):
        new_qs = fetch_bulk_questions(selected_sub)
        if new_qs:
            st.session_state.q_bank = new_qs
            st.session_state.index = 0
            st.session_state.ans_visible = False
            st.rerun()

# ప్రశ్నలు చూపే భాగం
if st.session_state.q_bank:
    idx = st.session_state.index
    if idx < len(st.session_state.q_bank):
        q = st.session_state.q_bank[idx]
        st.divider()
        st.subheader(f"ప్రశ్న {idx + 1} / 10:")
        st.info(q['question'])
        
        user_choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_fast_{idx}")

        if st.button("🔍 Check Answer & Detailed Solution", use_container_width=True):
            st.session_state.ans_visible = True

        if st.session_state.ans_visible:
            if user_choice == q['answer']: st.success("శభాష్! కరెక్ట్! ✅")
            else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 లోతైన వివరణ (Deep Logic Solution):", expanded=True):
                st.write(q['explanation'])
            
            # ఇక్కడ 'Next' నొక్కినప్పుడు చాలా వేగంగా మారుతుంది
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.index += 1
                st.session_state.ans_visible = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! 10 ప్రశ్నలు పూర్తి చేసావు. మళ్ళీ బటన్ నొక్కి ఇంకో 10 ప్రశ్నలు లోడ్ చేసుకో.")
        st.session_state.q_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం 10 ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | 20+ Years Excellence")
