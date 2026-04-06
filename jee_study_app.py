import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime
import time

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE PYQ Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ (With Retry Logic)
def fetch_all_pyq_questions(subject):
    prompt = f"""
    Role: Senior JEE Mains Expert.
    Context: Use all uploaded Previous Year Papers (2025, 2024, etc.).
    Task: Create 5 challenging MCQs for {subject}.
    Detailed Requirement: Provide a VERY LONG AND DEEP step-by-step mathematical explanation for each answer.
    Output Format: Return ONLY a raw JSON list.
    JSON structure: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..."}}].
    No markdown, no talk.
    """
    
    # AI కి 3 సార్లు అవకాశం ఇస్తున్నాము (Load అవ్వడానికి)
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                text = response.text.strip().replace('```json', '').replace('```', '')
                return json.loads(text)
        except Exception as e:
            time.sleep(2) # 2 సెకన్లు ఆగి మళ్ళీ ట్రై చేస్తుంది
            continue
    return None

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE PYQ MASTER")
st.caption("Analyzing All Uploaded Previous Year Papers (2025 & Older)")

menu = st.radio("మెనూ:", ["📝 Start PYQ Practice", "📜 Progress Report"], horizontal=True)

if menu == "📝 Start PYQ Practice":
    sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])
    
    if st.button("🚀 Analyze All PYQs & Start", use_container_width=True):
        with st.spinner("అన్ని సంవత్సరాల పేపర్లను విశ్లేషిస్తోంది... దయచేసి 10 సెకన్లు ఆగండి."):
            questions = fetch_all_pyq_questions(sub)
            if questions:
                st.session_state.ai_questions = questions
                st.session_state.q_no = 0
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.error("సర్వర్ బిజీగా ఉంది. దయచేసి మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

    if st.session_state.ai_questions:
        if st.session_state.q_no < len(st.session_state.ai_questions):
            q = st.session_state.ai_questions[st.session_state.q_no]
            st.divider()
            st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
            st.info(q['question'])
            
            ans = st.radio("నీ సమాధానం:", q['options'], key=f"ans_{st.session_state.q_no}")

            if st.button("🔍 Check Answer & See Detailed Solution", use_container_width=True):
                st.session_state.show_ans = True

            if st.session_state.show_ans:
                if ans == q['answer']: st.success("శభాష్! సరైన సమాధానం! ✅")
                else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
                
                with st.expander("📖 లోతైన వివరణ (Long Step-by-Step Solution):", expanded=True):
                    st.write(q['explanation'])
                
                if st.button("తర్వాతి ప్రశ్న ➡️", use_container_width=True):
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
        else:
            st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Sub": sub, "Ref": "All PYQs"})
            st.balloons()
            st.success("సెషన్ పూర్తి! వెరీ గుడ్ బాబు!")
            st.session_state.ai_questions = []
    else:
        st.write("పైన ఉన్న బటన్ నొక్కి ప్రాక్టీస్ మొదలుపెట్టు బాబు.")

else:
    st.subheader("📜 నీ ప్రోగ్రెస్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ పరీక్షలు రాయలేదు.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | 20+ Years Industry Excellence")
