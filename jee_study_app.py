import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
# మోడల్ ని కొంచెం అప్‌డేట్ చేశాను
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mentor", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ (మరింత బలంగా మార్చాను)
def fetch_pyq_questions(year, subject, level):
    prompt = f"""
    Create 5 tough MCQs for JEE {level} from {year} {subject} syllabus.
    Format: Return ONLY a JSON list. 
    Each object must have: 'question', 'options' (list of 4), 'answer', 'explanation'.
    The explanation must be LONG and DETAILED (step-by-step).
    Do not use any markdown like ```json. Just raw text.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # ఒకవేళ AI చుట్టూ ```json పెడితే దాన్ని తీసేయడం
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        data = json.loads(text)
        return data
    except Exception as e:
        # బ్యాకప్ ప్రశ్నలు - లోడింగ్ ఫెయిల్ అయితే ఇవి కనిపిస్తాయి
        return [
            {"question": "What is the work done in a closed path for a conservative force?", "options": ["Zero", "Positive", "Negative", "Infinite"], "answer": "Zero", "explanation": "Step 1: Define Conservative force (like gravity). Step 2: Work done depends only on initial and final positions. Step 3: Since start and end are same, displacement is zero, so Work = 0."},
            {"question": "Integral of 1/x dx?", "options": ["log x", "x^2", "exp x", "1"], "answer": "log x", "explanation": "Step 1: Use basic integration formula. Step 2: Integral of x^n is x^(n+1)/(n+1). Step 3: For n=-1, the special case is natural log ln(x)."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ టైటిల్
st.title("🎓 SAI RAKSHITH'S JEE ACADEMY")
st.divider()

menu = st.radio("మెనూ ఎంచుకోండి:", ["📝 ఎగ్జామ్ రాయండి", "📜 పాత రిపోర్ట్స్"], horizontal=True)

if menu == "📝 ఎగ్జామ్ రాయండి":
    col1, col2 = st.columns(2)
    with col1: yr = st.selectbox("Year", ["1st Year", "2nd Year"])
    with col2: sb = st.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    lv = st.radio("Level", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Fetch Questions with Deep Logic", use_container_width=True):
        with st.spinner("AI లోతైన వివరణలతో ప్రశ్నలను తయారు చేస్తోంది..."):
            st.session_state.ai_questions = fetch_pyq_questions(yr, sb, lv)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.markdown(f"### ప్రశ్న {st.session_state.q_no + 1}")
        st.info(q['question'])
        
        choice = st.radio("సరైన సమాధానం ఎంచుకో బాబు:", q['options'], key=f"q_{st.session_state.q_no}")

        if st.button("🔍 వివరణ చూడండి (Check & Learn)", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if choice == q['answer']:
                st.success("**కరెక్ట్! శభాష్!** ✅")
            else:
                st.error(f"**తప్పు!** ❌ (సరైన ఆన్సర్: {q['answer']})")
            
            st.markdown("#### 📖 వివరణాత్మక పరిష్కారం (Detailed Solution):")
            st.write(q['explanation'])
            
            if st.button("తర్వాతి ప్రశ్న ➡️", use_container_width=True):
                if choice == q['answer']: st.session_state.score += 1
                if st.session_state.q_no < len(st.session_state.ai_questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({"తేదీ": datetime.now().strftime("%d/%m %H:%M"), "సబ్జెక్ట్": f"{yr} {sb}", "మార్కులు": f"{st.session_state.score}/5"})
                    st.balloons()
                    st.success(f"ఎగ్జామ్ పూర్తయింది! మార్కులు: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("బటన్ నొక్కి 10 ఏళ్ల ప్రశ్నలతో చదువు మొదలుపెట్టండి.")

else:
    st.subheader("📜 నీ ప్రోగ్రెస్ రిపోర్ట్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ సెషన్స్ పూర్తి కాలేదు.")

st.divider()
st.caption("Custom Built by Manohar - Variety Motors | Empowering Education")
