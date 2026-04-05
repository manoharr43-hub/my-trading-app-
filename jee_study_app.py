import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime

# 1. Gemini AI సెటప్ (మనోహర్ గారు, కీ కరెక్ట్ గా ఉందో లేదో ఒక్కసారి చూడండి)
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Center", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - 1st & 2nd Year Mix Syllabus
def fetch_mixed_questions(subject, level):
    prompt = f"""
    Role: Senior JEE Expert.
    Task: Combine 1st Year and 2nd Year syllabus for {subject} and generate 5 tough {level} MCQs.
    Database: Use the patterns of ACTUAL QUESTIONS from the LAST 10 YEARS of JEE {level}.
    Requirements:
    1. Provide 5 questions with 4 options each.
    2. Provide a VERY LONG AND DETAILED STEP-BY-STEP EXPLANATION for every question.
    3. Output ONLY in raw JSON format: [{{"question": "...", "options": ["...", "..."], "answer": "...", "explanation": "..."}}].
    No markdown, no backticks.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except Exception as e:
        # ఒకవేళ AI ఫెయిల్ అయితే వచ్చే పక్కా JEE ప్రశ్నలు
        return [
            {"question": "JEE Concept: Potential energy of a spring is kx²/2. If compressed by 2x, what is the new energy?", "options": ["2 times", "4 times", "8 times", "Half"], "answer": "4 times", "explanation": "Step 1: Formula U = 1/2 kx². Step 2: New displacement is 2x. Step 3: New U' = 1/2 k(2x)² = 1/2 k(4x²) = 4 * (1/2 kx²). Step 4: So energy becomes 4 times."},
            {"question": "Chemistry: Which has the highest boiling point?", "options": ["H2O", "H2S", "H2Se", "H2Te"], "answer": "H2O", "explanation": "Step 1: Check Hydrogen bonding. Step 2: Water has strong intermolecular H-bonding. Step 3: Others only have Van der Waals forces. Step 4: H-bonding requires more energy to break, hence highest boiling point."}
        ]

# 3. సెషన్ స్టేట్
if 'history' not in st.session_state: st.session_state.history = []
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. యూజర్ ఇంటర్ఫేస్
st.title("🎓 SAI RAKSHITH JEE ACADEMY")
st.caption("1st & 2nd Year Combined Syllabus | Last 10 Years PYQs")

menu = st.radio("మెనూ:", ["📝 ఎగ్జామ్ రాయండి", "📜 పాత రిపోర్ట్స్"], horizontal=True)

if menu == "📝 ఎగ్జామ్ రాయండి":
    # ఇక్కడ Year ఆప్షన్ తీసేశాను, డైరెక్ట్ సబ్జెక్ట్
    sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])
    lvl = st.radio("ఎగ్జామ్ లెవల్:", ["JEE Mains", "JEE Advanced"], horizontal=True)

    if st.button("🚀 Start 10-Year Mix Paper", use_container_width=True):
        with st.spinner("AI 10 ఏళ్ల డేటా నుండి ప్రశ్నలను మిక్స్ చేస్తోంది..."):
            st.session_state.ai_questions = fetch_mixed_questions(sub, lvl)
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.show_ans = False
            st.rerun()

    if st.session_state.ai_questions:
        q = st.session_state.ai_questions[st.session_state.q_no]
        st.divider()
        st.subheader(f"ప్రశ్న {st.session_state.q_no + 1}:")
        st.info(q['question'])
        
        ans = st.radio("నీ సమాధానం:", q['options'], key=f"ans_{st.session_state.q_no}")

        if st.button("🔍 Check Answer & Deep Logic", use_container_width=True):
            st.session_state.show_ans = True

        if st.session_state.show_ans:
            if ans == q['answer']: st.success("అద్భుతం! కరెక్ట్ ఆన్సర్! ✅")
            else: st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి వివరణ (Step-by-Step):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("తర్వాతి ప్రశ్న ➡️", use_container_width=True):
                if ans == q['answer']: st.session_state.score += 1
                if st.session_state.q_no < 4:
                    st.session_state.q_no += 1
                    st.session_state.show_ans = False
                    st.rerun()
                else:
                    st.session_state.history.append({"Date": datetime.now().strftime("%d/%m %H:%M"), "Sub": sub, "Score": f"{st.session_state.score}/5"})
                    st.balloons()
                    st.success(f"సెషన్ పూర్తి! స్కోర్: {st.session_state.score}/5")
                    st.session_state.ai_questions = []
    else:
        st.write("పై బటన్ నొక్కి ప్రాక్టీస్ మొదలుపెట్టండి బాబు.")

else:
    st.subheader("📜 నీ పాత రికార్డులు")
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history))
    else:
        st.info("ఇంకా ఏ సెషన్స్ పూర్తి కాలేదు.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | 20+ Years Excellence")
