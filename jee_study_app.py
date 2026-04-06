import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Previous Years Master", layout="centered")

# 2. అన్ని అప్‌లోడ్ చేసిన పేపర్ల నుండి ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_all_pyq_questions(subject):
    prompt = f"""
    You are a Senior JEE Expert. I have uploaded several Previous Year Question (PYQ) papers (2025 and earlier).
    TASK: Analyze ALL uploaded papers for {subject}.
    1. Select 5 high-weightage MCQs based on the patterns of these previous years.
    2. For each question, provide a VERY LONG, STEP-BY-STEP MATHEMATICAL EXPLANATION.
    3. Include the core formula used and the logic behind every step so the student understands perfectly.
    4. Mention which year/shift the question or pattern belongs to if possible.
    Return ONLY a raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..."}}].
    Do not use markdown.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except Exception as e:
        return []

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
        with st.spinner("అన్ని సంవత్సరాల పేపర్ల నుండి లోతైన వివరణలతో ప్రశ్నలను సిద్ధం చేస్తోంది..."):
            questions = fetch_all_pyq_questions(sub)
            if questions:
                st.session_state.ai_questions = questions
                st.session_state.q_no = 0
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.error("ప్రశ్నలు లోడ్ కాలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి.")

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
            st.success("ఈ సెషన్ పూర్తి చేసావు! వెరీ గుడ్ బాబు!")
            st.session_state.ai_questions = []
    else:
        st.write("పైన ఉన్న బటన్ నొక్కి అన్ని సంవత్సరాల పేపర్లతో ప్రాక్టీస్ మొదలుపెట్టు బాబు.")

else:
    st.subheader("📜 నీ ప్రోగ్రెస్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ పరీక్షలు రాయలేదు.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | 20+ Years Excellence")
