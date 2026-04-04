import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_ai_questions(year, subject, level):
    prompt = f"""
    Generate 5 JEE {level} MCQs for {year} {subject}. 
    For each question, provide a detailed explanation in simple English.
    Return ONLY a JSON list with: 'question', 'options', 'answer', 'explanation'.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except Exception as e:
        return [
            {"question": "Unit of Force?", "options": ["Newton", "Joule", "Watt", "Volt"], "answer": "Newton", "explanation": "Force is defined as mass times acceleration (F=ma). The SI unit is Newton (N)."},
            {"question": "Value of sin(90)?", "options": ["0", "1", "0.5", "-1"], "answer": "1", "explanation": "In trigonometry, the sine of 90 degrees is the maximum value in the unit circle, which is 1."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ స్క్రీన్
st.title("🎓 SAI RAKSHITH JEE CENTER")

menu = st.radio("Folder:", ["📝 Exam", "📜 History"], horizontal=True)

if menu == "📝 Exam":
    year_sel = st.selectbox("Year", ["1st Year", "2nd Year"])
    sub_sel = st.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    lvl_sel = st.radio("Level", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Start Exam", use_container_width=True):
        with st.spinner("AI వివరిస్తూ ప్రశ్నలను తయారు చేస్తోంది..."):
            st.session_state.ai_questions = fetch_ai_questions(year_sel, sub_sel, lvl_sel)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.markdown(f"### Question {st.session_state.q_no + 1}")
        st.info(q['question'])
        
        choice = st.radio("సరైన సమాధానాన్ని ఎంచుకో బాబు:", q['options'], key=f"q_{st.session_state.q_no}")

        if st.button("🔍 Check Answer & Explanation", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if choice == q['answer']:
                st.success(f"**కరెక్ట్!** ✅")
            else:
                st.error(f"**తప్పు!** ❌ (సరైన సమాధానం: {q['answer']})")
            
            # ఇక్కడ వివరణ స్పష్టంగా కనిపిస్తుంది
            st.markdown("#### 📖 వివరణ (Explanation):")
            st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                if choice == q['answer']: st.session_state.score += 1
                if st.session_state.q_no < len(st.session_state.ai_questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({
                        "Date": datetime.now().strftime("%d/%m %H:%M"),
                        "Exam": f"{year_sel} {sub_sel}",
                        "Score": f"{st.session_state.score}/5"
                    })
                    st.balloons()
                    st.success(f"Exam Done! Final Score: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("బటన్ నొక్కి ఎగ్జామ్ మొదలుపెట్టండి.")

else:
    st.subheader("📜 పాత ఎగ్జామ్ రికార్డ్స్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ ఎగ్జామ్స్ రాయలేదు.")

st.divider()
st.caption("Developed by Manohar (Variety Motors) for Sai Rakshith's Success")
