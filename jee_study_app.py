import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import time

# 1. AI సెటప్ (Gemini 1.5 Flash - ఇది చాలా వేగంగా ఉంటుంది)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Optimized for Flash Speed
def fetch_mains_only_questions(subject):
    # ఇక్కడ AI కి డైరెక్ట్ గా ఇన్స్ట్రక్షన్ ఇచ్చాను వేగం కోసం
    prompt = f"""
    Act as a Senior JEE Mains Expert. 
    Task: Generate 5 HIGH-QUALITY MCQs strictly for JEE Mains level for {subject}.
    Logic: Provide a VERY LONG, STEP-BY-STEP mathematical explanation for each answer. Show core concept, then solution.
    Format: Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step..."}}].
    Do not use markdown.
    """
    
    # Retry Loop for Safety
    for attempt in range(3):
        try:
            # JSON Mode వాడటం వల్ల ఎర్రర్లు రావు
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            if response and response.text:
                return json.loads(response.text)
        except:
            time.sleep(1) # 1 సెకను ఆగి మళ్ళీ ట్రై చేస్తుంది
            continue
    return []

# 3. సెషన్ స్టేట్
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE MAINS MASTER")
st.caption("Flash Mode: Instant Question Load with Detailed Long Solutions")

st.divider()

# సబ్జెక్ట్ ఎంపిక (Mains Only)
selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్
if st.button("🚀 Start JEE Mains Practice Session", use_container_width=True):
    # ఇక్కడ వెంటనే ప్రశ్నలు లోడ్ అవుతాయి
    with st.spinner("ఫైల్స్ విశ్లేషిస్తోంది... దయచేసి 5 సెకన్లు ఆగండి."):
        # Bulk Loading తీసేసి 5 ప్రశ్నలు అడుగుతున్నాము, వేగం కోసం
        qs = fetch_mains_only_questions(selected_sub)
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("AI కొంచెం ఎక్కువ టైమ్ తీసుకుంటోంది. మళ్ళీ ఒక్కసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"mains_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution"):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Long Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️"):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success("వెరీ గుడ్ బాబు! ఈ సెషన్ పూర్తి చేసావు.")
        st.session_state.mains_bank = []
else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం Mains ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Dedicated to Sai Rakshith's JEE Mains Success")
