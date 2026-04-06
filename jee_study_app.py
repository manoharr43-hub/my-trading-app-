import streamlit as st
import google.generativeai as genai
import json
import time

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Automatic Retry Mode
def fetch_questions_power_mode():
    prompt = """
    Act as a Senior JEE Mains Expert. 
    Use the patterns from uploaded PDF papers.
    Generate 5 HIGH-QUALITY MCQs strictly for JEE Mains level. 
    (Mix Physics, Chemistry, Maths).
    Requirement: Provide a VERY LONG, STEP-BY-STEP SOLUTION for each.
    Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed step-by-step logic..."}].
    Do not use markdown.
    """
    
    # ఎర్రర్ రాకుండా 3 సార్లు ఆటోమేటిక్ గా ట్రై చేస్తుంది
    for attempt in range(3):
        try:
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            if response and response.text:
                return json.loads(response.text)
        except:
            time.sleep(2) # 2 సెకన్లు ఆగి మళ్ళీ ట్రై చేస్తుంది
            continue
    return []

# 3. సెషన్ స్టేట్
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Power-Retry Mode: Ensuring No Waiting Time")

st.divider()

if st.button("🚀 START JEE MAINS PRACTICE SESSION", use_container_width=True):
    with st.spinner("AI విశ్లేషిస్తోంది... దయచేసి ఒక్క 5-10 సెకన్లు ఆగండి."):
        qs = fetch_questions_power_mode()
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("సర్వర్ చాలా బిజీగా ఉంది. దయచేసి ఇంకొకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_final_{curr}")

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
