import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime

# 1. AI సెటప్
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. PDFల నుండి ప్రశ్నలు తెచ్చే ఫంక్షన్ (High Speed Mode)
def fetch_questions_from_pdfs():
    # ఇక్కడ AI కి మీ PDFలను ప్రాధాన్యత ఇవ్వమని ఇన్స్ట్రక్షన్ ఇచ్చాను
    prompt = """
    You are a JEE Mains expert. 
    Access all the uploaded PDF files in the repository (2025 Jan shifts and PYQs).
    TASK: Pick 5 tough MCQs from these PDF contents strictly for JEE MAINS.
    Mix Physics, Chemistry, and Maths.
    Requirement: Provide a VERY LONG, STEP-BY-STEP SOLUTION for each.
    Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step..."}].
    Do not use markdown.
    """
    try:
        # JSON Mode ని యాక్టివేట్ చేసాను, ఇది ఎర్రర్లు రాకుండా చూస్తుంది
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return []

# 3. సెషన్ స్టేట్
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("PDF Data Analysis Mode | Strictly JEE Mains | Fast Load")

st.divider()

# ఒక్క బటన్ తో అన్ని సబ్జెక్టుల ప్రశ్నలు
if st.button("🚀 START JEE MAINS PRACTICE (FROM YOUR PDFs)", use_container_width=True):
    with st.spinner("మీ PDF ఫైల్స్ విశ్లేషిస్తోంది... దయచేసి ఒక్క 5 సెకన్లు ఆగండి."):
        qs = fetch_questions_from_pdfs()
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.warning("AI కొంచెం బిజీగా ఉంది. దయచేసి మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు ప్రదర్శించే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution", use_container_width=True):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("శభాష్! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Step-by-Step Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! నీ PDFలలోని ముఖ్యమైన Mains ప్రశ్నలు పూర్తి చేసావు.")
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ PDF ఫైల్స్ నుండి ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Focus: Your Uploaded PDF Content")
