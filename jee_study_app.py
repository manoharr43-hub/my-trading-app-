import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్ (మీ API Key ఇక్కడ ఉంది)
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# మొబైల్ కోసం LAYOUT సెటప్ (Centered అంటే మధ్యలోకి వస్తుంది)
st.set_page_config(page_title="Sai Rakshith JEE", layout="centered")

# 2. AI ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_ai_questions(year, subject, level):
    prompt = f"Generate 5 JEE {level} MCQs for {year} {subject}. Return ONLY a raw JSON list with 'question', 'options', 'answer', 'explanation'."
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return []

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. మెయిన్ టైటిల్
st.title("🎓 SAI RAKSHITH JEE CENTER")

# 5. ఫోల్డర్ సెలెక్షన్ (ఇప్పుడు ఇది స్క్రీన్ పైనే కనిపిస్తుంది, సైడ్ బార్ లో కాదు)
menu = st.segmented_control("Folder సెలెక్ట్ చేయండి:", ["📝 Exam", "📜 History"], default="📝 Exam")

if menu == "📝 Exam":
    # సెలెక్షన్ బాక్సులు
    col1, col2 = st.columns(2)
    with col1:
        year_select = st.selectbox("Year", ["1st Year", "2nd Year"])
    with col2:
        sub_select = st.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    
    lvl_select = st.radio("Level", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Generate New Exam", use_container_width=True):
        with st.spinner("AI ప్రశ్నలను తెస్తోంది..."):
            st.session_state.ai_questions = fetch_ai_questions(year_select, sub_select, lvl_select)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    # ప్రశ్నలు ప్రదర్శించడం
    if st.session_state.ai_questions:
        curr = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.info(f"Q{st.session_state.q_no + 1} of 5 ({sub_select})")
        st.subheader(curr['question'])
        
        user_choice = st.radio("ఆప్షన్ ఎంచుకోండి:", curr['options'], key=f"q_{st.session_state.q_no}")

        if st.button("✅ Check Answer", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if user_choice == curr['answer']:
                st.success(f"Correct! 👏 \n\n {curr['explanation']}")
            else:
                st.error(f"Wrong! Correct: {curr['answer']} \n\n {curr['explanation']}")
            
            if st.button("Next Question ➡️", use_container_width=True):
                if user_choice == curr['answer']: st.session_state.score += 1
                if st.session_state.q_no < 4:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    # సేవ్ చేయడం
                    st.session_state.history.append({
                        "Date": datetime.now().strftime("%d/%m %H:%M"),
                        "Sub": f"{year_select}-{sub_select}",
                        "Score": f"{st.session_state.score}/5"
                    })
                    st.balloons()
                    st.success(f"ఎగ్జామ్ పూర్తి! స్కోర్: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("పైన బటన్ నొక్కి ఎగ్జామ్ స్టార్ట్ చేయండి.")

else:
    # HISTORY ఫోల్డర్
    st.subheader("📜 పాత ఎగ్జామ్ రిపోర్ట్స్")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ ఎగ్జామ్స్ రాయలేదు.")

st.divider()
st.caption("Managed by Manohar - Variety Motors")
