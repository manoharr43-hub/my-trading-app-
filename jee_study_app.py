import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# మొబైల్ ఫ్రెండ్లీ లేఅవుట్
st.set_page_config(page_title="Sai Rakshith JEE", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ (AI + Backup)
def fetch_ai_questions(year, subject, level):
    prompt = f"Generate 5 JEE {level} MCQs for {year} {subject}. Return ONLY a raw JSON list with keys: 'question', 'options', 'answer', 'explanation'. Do not use markdown."
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except Exception as e:
        # ఒకవేళ AI పని చేయకపోతే ఈ బ్యాకప్ ప్రశ్నలు వస్తాయి
        st.warning("AI కొంచెం బిజీగా ఉంది, ఈ ప్రాక్టీస్ ప్రశ్నలు రాయండి:")
        return [
            {"question": "What is the unit of Force?", "options": ["Newton", "Joule", "Watt", "Volt"], "answer": "Newton", "explanation": "Force is measured in Newtons."},
            {"question": "Value of sin(90)?", "options": ["0", "1", "0.5", "-1"], "answer": "1", "explanation": "sin(90) is always 1."},
            {"question": "Chemical symbol for Gold?", "options": ["Au", "Ag", "Fe", "Cu"], "answer": "Au", "explanation": "Au is Aurum (Gold)."},
            {"question": "Which is a prime number?", "options": ["4", "9", "13", "15"], "answer": "13", "explanation": "13 has no factors other than 1 and itself."},
            {"question": "Unit of Resistance?", "options": ["Ohm", "Ampere", "Volt", "Watt"], "answer": "Ohm", "explanation": "Resistance is measured in Ohms."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. టైటిల్
st.title("🎓 SAI RAKSHITH JEE CENTER")

# ఫోల్డర్ సెలెక్షన్
menu = st.radio("Folder ఎంచుకోండి:", ["📝 Exam", "📜 History"], horizontal=True)

if menu == "📝 Exam":
    # సబ్జెక్ట్ సెలెక్షన్
    year_sel = st.selectbox("Year", ["1st Year", "2nd Year"])
    sub_sel = st.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    lvl_sel = st.radio("Level", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Start New Exam", use_container_width=True):
        with st.spinner("ప్రశ్నలు లోడ్ అవుతున్నాయి..."):
            st.session_state.ai_questions = fetch_ai_questions(year_sel, sub_sel, lvl_sel)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    # ప్రశ్నలు ప్రదర్శన
    if st.session_state.ai_questions:
        q_data = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.subheader(f"Q{st.session_state.q_no + 1}: {q_data['question']}")
        
        choice = st.radio("సరైన ఆప్షన్ ఎంచుకోండి:", q_data['options'], key=f"q_{st.session_state.q_no}")

        if st.button("✅ Check Answer", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if choice == q_data['answer']:
                st.success(f"కరెక్ట్! ✨ \n {q_data['explanation']}")
            else:
                st.error(f"తప్పు! సరైనది: {q_data['answer']} \n {q_data['explanation']}")
            
            if st.button("Next Question ➡️", use_container_width=True):
                if choice == q_data['answer']: st.session_state.score += 1
                if st.session_state.q_no < len(st.session_state.ai_questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    # హిస్టరీలో సేవ్ చేయడం
                    st.session_state.history.append({
                        "Date": datetime.now().strftime("%d/%m %H:%M"),
                        "Exam": f"{year_sel} {sub_sel}",
                        "Score": f"{st.session_state.score}/5"
                    })
                    st.balloons()
                    st.success(f"ఎగ్జామ్ పూర్తయింది! స్కోర్: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("పైన బటన్ నొక్కి ఎగ్జామ్ మొదలుపెట్టండి.")

else:
    # HISTORY
    st.subheader("📜 పాత ఎగ్జామ్ రిపోర్ట్స్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ ఎగ్జామ్స్ రాయలేదు.")

st.divider()
st.caption("Developed for Sai Rakshith by Manohar - Variety Motors")
