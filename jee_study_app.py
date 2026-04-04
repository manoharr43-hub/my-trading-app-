import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Dashboard", layout="wide")

# 2. AI ప్రశ్నలు తెచ్చే ఫంక్షన్
def fetch_ai_questions(year, subject, level):
    prompt = f"""
    Generate 5 high-quality {level} MCQs for {year} {subject}.
    Target: JEE preparation. 
    Return ONLY a raw JSON list with these keys: 'question', 'options', 'answer', 'explanation'.
    'options' must be a list of 4 strings.
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except:
        return []

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. సైడ్ బార్ - మెనూ
st.sidebar.title("🏥 JEE DASHBOARD")
menu = st.sidebar.radio("Go to Folder:", ["📝 Take Exam", "📜 Exam History"])

if menu == "📝 Take Exam":
    st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
    
    # ఇయర్ మరియు సబ్జెక్ట్ సెలెక్షన్
    year_select = st.sidebar.selectbox("Select Year", ["1st Year", "2nd Year"])
    sub_select = st.sidebar.selectbox("Subject", ["Mathematics", "Physics", "Chemistry"])
    lvl_select = st.sidebar.radio("Level", ["JEE Mains", "JEE Advanced"])

    if st.sidebar.button("Generate New AI Exam"):
        with st.spinner(f"Gemini AI {year_select} {sub_select} ప్రశ్నలను తయారు చేస్తోంది..."):
            st.session_state.ai_questions = fetch_ai_questions(year_select, sub_select, lvl_select)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        curr = st.session_state.ai_questions[st.session_state.q_no]
        st.info(f"Target: {year_select} - {sub_select} ({lvl_select})")
        st.subheader(f"Q{st.session_state.q_no + 1}: {curr['question']}")
        
        user_choice = st.radio("Choose Option:", curr['options'], key=f"q_{st.session_state.q_no}")

        if st.button("✅ Check Answer"):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if user_choice == curr['answer']:
                st.success(f"Correct! ✨ \n\n **Explanation:** {curr['explanation']}")
            else:
                st.error(f"Wrong! Correct Answer: {curr['answer']} \n\n **Explanation:** {curr['explanation']}")
            
            if st.button("Next Question ➡️"):
                if user_choice == curr['answer']: st.session_state.score += 1
                if st.session_state.q_no < len(st.session_state.ai_questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    # ఎగ్జామ్ పూర్తి - డేట్ వైస్ హిస్టరీ సేవ్
                    new_record = {
                        "Date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                        "Year": year_select,
                        "Subject": sub_select,
                        "Level": lvl_select,
                        "Score": f"{st.session_state.score} / {len(st.session_state.ai_questions)}"
                    }
                    st.session_state.history.append(new_record)
                    st.balloons()
                    st.success(f"ఎగ్జామ్ పూర్తయింది! స్కోర్: {st.session_state.score}/{len(st.session_state.ai_questions)}")
                    st.session_state.ai_questions = []
    else:
        st.warning("పక్కన ఉన్న 'Generate New AI Exam' బటన్ నొక్కి స్టార్ట్ చేయండి.")

else:
    # ఫోల్డర్ 2: EXAM HISTORY (Date-wise)
    st.title("📜 PREVIOUS EXAM RECORDS (Date-wise)")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        # టేబుల్ రూపంలో డేట్ వైస్ మార్కులు
        st.table(df)
    else:
        st.info("ఇంకా ఎటువంటి ఎగ్జామ్స్ రికార్డ్ అవ్వలేదు.")

st.sidebar.divider()
st.sidebar.caption(f"Managed by Manohar - Variety Motors (Date: {datetime.now().strftime('%Y')})")
