import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Exam Center", layout="wide")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_ai_questions(subject, level):
    prompt = f"Generate 5 high-quality {level} MCQs for {subject}. Return ONLY a raw JSON list with 'question', 'options', 'answer', 'explanation'."
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except:
        return []

# 3. సెషన్ స్టేట్ (డేటా సేవ్ చేయడానికి)
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. సైడ్ బార్ - ఫోల్డర్ సిస్టమ్
st.sidebar.title("🏥 JEE DASHBOARD")
menu = st.sidebar.radio("Go to Folder:", ["📝 Take Exam", "📜 Exam History"])

# --- ఫోల్డర్ 1: TAKE EXAM ---
if menu == "📝 Take Exam":
    st.title("🎓 SAI RAKSHITH'S AI PREP CENTER")
    
    sub = st.sidebar.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
    lvl = st.sidebar.radio("Level", ["JEE Mains", "JEE Advanced"])

    if st.sidebar.button("Generate New AI Exam"):
        st.session_state.ai_questions = fetch_ai_questions(sub, lvl)
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.show_ans = False
        st.rerun()

    if st.session_state.ai_questions:
        curr = st.session_state.ai_questions[st.session_state.q_no]
        st.info(f"Question {st.session_state.q_no + 1} of 5")
        st.subheader(curr['question'])
        user_choice = st.radio("Choose Option:", curr['options'], key=f"q_{st.session_state.q_no}")

        if st.button("✅ Check Answer"):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if user_choice == curr['answer']:
                st.success(f"Correct! \n\n **Exp:** {curr['explanation']}")
            else:
                st.error(f"Wrong! Correct: {curr['answer']} \n\n **Exp:** {curr['explanation']}")
            
            if st.button("Next Question ➡️"):
                if user_choice == curr['answer']: st.session_state.score += 1
                if st.session_state.q_no < 4:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    # ఎగ్జామ్ పూర్తి - హిస్టరీలో సేవ్ చేయడం
                    new_record = {
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Subject": sub,
                        "Level": lvl,
                        "Score": f"{st.session_state.score} / 5"
                    }
                    st.session_state.history.append(new_record)
                    st.success(f"Exam Finished! Score: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.warning("పక్కన ఉన్న బటన్ నొక్కి ఎగ్జామ్ స్టార్ట్ చేయండి.")

# --- ఫోల్డర్ 2: EXAM HISTORY ---
else:
    st.title("📜 PREVIOUS EXAM RECORDS")
    if st.session_state.history:
        # టేబుల్ ఫార్మాట్‌లో చూపించడం
        df = pd.DataFrame(st.session_state.history)
        st.table(df) # తేదీల వారీగా ఇక్కడ కనిపిస్తాయి
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.write("ఇంకా ఎటువంటి ఎగ్జామ్స్ రాయలేదు. 'Take Exam' ఫోల్డర్ కి వెళ్ళండి.")

st.sidebar.divider()
st.sidebar.caption("Managed by Manohar - Variety Motors")
