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

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Optimized for Success
def fetch_mains_questions_safe(subject):
    # ఇక్కడ AI కి చాలా సింపుల్ గా ఇన్స్ట్రక్షన్స్ ఇచ్చాను వేగం కోసం
    prompt = f"""
    Act as a JEE Mains Expert. 
    Task: Generate 5 high-quality MCQs for {subject} based on ACTUAL JEE Mains Previous Years patterns.
    Rules: 
    1. Provide a VERY LONG, STEP-BY-STEP MATHEMATICAL SOLUTION for each answer.
    2. Ensure questions are strictly JEE Mains level.
    Return ONLY a JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed step-by-step..."}}].
    Do not use markdown.
    """
    try:
        # AI స్పందన కోసం 30 సెకన్ల టైమ్ ఇస్తున్నాము
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        if response and response.text:
            return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Strictly JEE Mains Mode | Detailed Logical Solutions")

# సబ్జెక్ట్ ఎంపిక
sub_choice = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్
if st.button("🚀 Start JEE Mains Practice Session", use_container_width=True):
    with st.spinner("ఫైల్స్ విశ్లేషించి ప్రశ్నలను సిద్ధం చేస్తోంది..."):
        qs = fetch_mains_questions_safe(sub_choice)
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.warning("AI కొంచెం ఎక్కువ టైమ్ తీసుకుంటోంది. దయచేసి మళ్ళీ ఒక్కసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
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
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Step-by-Step):", expanded=True):
                st.write(q['explanation'])
            
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
