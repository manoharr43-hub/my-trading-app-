import streamlit as st
import google.generativeai as genai
import json
import random

# 1. Gemini AI సెటప్ (మీరు ఇచ్చిన కీ ఇక్కడ యాడ్ చేశాను)
GEMINI_API_KEY = "AIzaSyCUIAUEx6TobpaSyn7kD5MmUHt3EEqu53Y" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # వేగంగా పనిచేసే మోడల్

# పేజీ సెటప్
st.set_page_config(page_title="Sai Rakshith AI Exam Center", layout="wide")

# 2. Gemini ద్వారా ప్రశ్నలు తయారు చేసే ఫంక్షన్
def fetch_ai_questions(subject, level):
    prompt = f"""
    Generate 5 high-quality {level} multiple choice questions for {subject} (suitable for 11th/12th grade JEE preparation).
    Return ONLY a raw JSON list of objects with these exact keys:
    "question", "options", "answer", "explanation".
    "options" must be a list of 4 strings.
    "answer" must be the exact string from the options.
    Do not include markdown formatting like ```json.
    """
    try:
        response = model.generate_content(prompt)
        # JSON క్లీన్ చేయడం
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        data = json.loads(clean_text)
        return data
    except Exception as e:
        # ఒకవేళ AI పని చేయకపోతే బ్యాకప్ ప్రశ్నలు
        return [
            {"question": "What is the unit of Electric Current?", "options": ["Ampere", "Volt", "Ohm", "Watt"], "answer": "Ampere", "explanation": "Electric current is measured in Amperes (A)."},
            {"question": "Value of Acceleration due to gravity (g)?", "options": ["9.8 m/s²", "10.8 m/s²", "8.8 m/s²", "7.8 m/s²"], "answer": "9.8 m/s²", "explanation": "Standard gravity is 9.8 m/s²."}
        ]

# 3. సెషన్ స్టేట్ మేనేజ్మెంట్
if 'ai_questions' not in st.session_state: st.session_state.ai_questions = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'show_ans' not in st.session_state: st.session_state.show_ans = False

# 4. సైడ్ బార్ సెటప్
st.sidebar.title("🤖 AI EXAM GENERATOR")
st.sidebar.write("మనోహర్ గారు, ఇక్కడ సబ్జెక్ట్ సెలెక్ట్ చేయండి.")

sub = st.sidebar.selectbox("Subject", ["Physics", "Mathematics", "Chemistry"])
lvl = st.sidebar.radio("Level", ["JEE Mains", "JEE Advanced"])

if st.sidebar.button("Generate New AI Exam"):
    with st.spinner("Gemini AI కొత్త ప్రశ్నలను తయారు చేస్తోంది..."):
        st.session_state.ai_questions = fetch_ai_questions(sub, lvl)
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.show_ans = False
        st.rerun()

# 5. మెయిన్ స్క్రీన్
st.title("🎓 SAI RAKSHITH'S AI PREP CENTER")
st.markdown("---")

if st.session_state.ai_questions:
    questions = st.session_state.ai_questions
    curr = questions[st.session_state.q_no]
    
    st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
    st.subheader(curr['question'])
    
    # ఆప్షన్లు చూపించడం
    user_choice = st.radio("Choose Option:", curr['options'], key=f"ai_q_{st.session_state.q_no}")

    if st.button("✅ Check Answer"):
        st.session_state.show_ans = True

    if st.session_state.show_ans:
        if user_choice == curr['answer']:
            st.success(f"కరెక్ట్ ఆన్సర్! ✨ \n\n **వివరణ:** {curr['explanation']}")
        else:
            st.error(f"తప్పు! సరైన సమాధానం: {curr['answer']} \n\n **వివరణ:** {curr['explanation']}")
        
        if st.button("Next Question ➡️"):
            if user_choice == curr['answer']: st.session_state.score += 1
            if st.session_state.q_no < len(questions) - 1:
                st.session_state.q_no += 1
                st.session_state.show_ans = False
                st.rerun()
            else:
                st.balloons()
                st.success(f"ఎగ్జామ్ పూర్తయింది! సాయి రక్షిత్ స్కోర్: {st.session_state.score}/{len(questions)}")
                st.session_state.ai_questions = [] # మళ్ళీ మొదలు పెట్టడానికి క్లియర్ చేస్తున్నాం
else:
    st.warning("పక్కన ఉన్న 'Generate New AI Exam' బటన్ నొక్కి ప్రశ్నలను లోడ్ చేయండి.")

st.divider()
st.caption("AI Engine Powered by Gemini - Managed by Manohar (Variety Motors)")
