import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mentor", layout="centered")

# 2. లోతైన వివరణలతో ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_pyq_questions(year, subject, level):
    prompt = f"""
    Act as a Senior JEE Professor. Generate 5 MCQs for {year} {subject} at {level} level based on last 10 years papers.
    For the 'explanation' field, provide a very DETAILED STEP-BY-STEP solution:
    1. State the core concept/formula used.
    2. Show the calculation steps clearly.
    3. Explain why the correct option is right and why others are traps.
    Return ONLY a JSON list with: 'question', 'options', 'answer', 'explanation'.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except:
        return [{"question": "System busy. Click again.", "options": ["-", "-", "-", "-"], "answer": "-", "explanation": "Detailed explanation will appear here."}]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ టైటిల్
st.title("🎓 SAI RAKSHITH'S JEE ACADEMY")
st.markdown("---")

menu = st.radio("Folder:", ["📝 Exam Center", "📜 Progress Report"], horizontal=True)

if menu == "📝 Exam Center":
    col1, col2 = st.columns(2)
    with col1: year_sel = st.selectbox("Year", ["1st Year", "2nd Year"])
    with col2: sub_sel = st.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    lvl_sel = st.radio("Level", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Fetch 10-Year PYQs with Deep Logic", use_container_width=True):
        with st.spinner("AI ప్రొఫెసర్ ప్రశ్నలను మరియు వివరణలను సిద్ధం చేస్తున్నారు..."):
            st.session_state.ai_questions = fetch_pyq_questions(year_sel, sub_sel, lvl_sel)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
        st.info(q['question'])
        
        choice = st.radio("సరైన ఆప్షన్ ఎంచుకో బాబు:", q['options'], key=f"q_{st.session_state.q_no}")

        if st.button("🔍 View Detailed Explanation", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if choice == q['answer']:
                st.success("**కరెక్ట్! వెరీ గుడ్!** ✅")
            else:
                st.error(f"**తప్పు!** ❌ (సరైన సమాధానం: {q['answer']})")
            
            # ఇక్కడ వివరణ చాలా లోతుగా కనిపిస్తుంది
            st.markdown("### 📖 Step-by-Step Solution & Logic:")
            st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                if choice == q['answer']: st.session_state.score += 1
                if st.session_state.q_no < len(st.session_state.ai_questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Exam": f"{sub_sel} Deep Study", "Score": f"{st.session_state.score}/5"})
                    st.balloons()
                    st.success(f"సెషన్ పూర్తయింది! మార్కులు: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("పై బటన్ నొక్కి లోతైన వివరణలతో చదువు మొదలుపెట్టండి.")

else:
    st.subheader("📜 నీ ప్రోగ్రెస్ రిపోర్ట్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ సెషన్స్ పూర్తి కాలేదు.")

st.divider()
st.caption("Developed by Manohar - Variety Motors | 20+ Years Excellence")
