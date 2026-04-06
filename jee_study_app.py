import streamlit as st
import google.generativeai as genai
import json
import time

# 1. AI సెటప్ (సిలబస్ మరియు ప్యాటర్న్ మోడ్)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Sai Rakshith JEE Mains Master", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Super Fast Mode
def fetch_questions_instant_fast():
    # ఇక్కడ AI కి డైరెక్ట్ గా ఇన్స్ట్రక్షన్ ఇచ్చాను తన మెమరీని వాడమని
    prompt = """
    Act as a Senior JEE Mains Expert. 
    Use the current JEE Mains syllabus and 2025 question paper patterns as the database.
    Task: Generate 5 CHALLENGING MCQs strictly for JEE Mains level. 
    Mix: Physics, Chemistry, Mathematics (Mixed).
    Requirement: Provide a VERY LONG, STEP-BY-STEP mathematical explanation for each.
    Return ONLY a raw JSON list: [{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step Logic..."}].
    Do not use markdown.
    """
    
    # Automatic Retry - Safe Mode
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
st.caption("Target: JEE Mains Success | Instant Question Load with Detailed Logic")

st.divider()

if st.button("🚀 START JEE MAINS PRACTICE (SUPER FAST MODE)", use_container_width=True):
    # ఇక్కడ వెంటనే ప్రశ్నలు లోడ్ అవుతాయి
    with st.spinner("ప్రశ్నలను సిద్ధం చేస్తోంది... ఒక్క 2-3 సెకన్లు ఆగండి."):
        qs = fetch_questions_instant_fast()
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("AI కొంచెం ఎక్కువ టైమ్ తీసుకుంటోంది. ఒక్కసారి మళ్ళీ బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_fast_{curr}")

        if st.button("🔍 Check Answer & See Long Solution"):
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
st.caption("Managed by Manohar - Variety Motors | Dedicated to Sai Rakshith's JEE Success")
