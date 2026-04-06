import streamlit as st
import google.generativeai as genai
import json
import time

# 1. AI సెటప్ (Gemini 1.5 Flash - ఇది చాలా వేగంగా ఉంటుంది)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.set_page_config(page_title="Sai Rakshith JEE Fast-Track", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Optimized for Flash Speed
def fetch_mains_only_questions(subject):
    prompt = f"""
    Act as a Senior JEE Mains Expert. 
    Task: Scan all uploaded PDF papers (2025 Jan shifts and previous years).
    Generate 5 HIGH-QUALITY MCQs strictly for JEE MAINS level for {subject}.
    Requirement: Provide a VERY LONG, STEP-BY-STEP solution for each answer. Show core concept, then solution.
    Format: Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step..."}}].
    Do not use markdown.
    """
    
    # Retry Loop for Safety
    for attempt in range(3):
        try:
            # response_mime_type వాడటం వల్ల JSON పక్కాగా వస్తుంది
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
st.title("🎓 SAI RAKSHITH JEE FAST-TRACK")
st.caption("Auto-Preload Mode: Continuous Practice without Waiting")

selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్
if st.button("🚀 Start JEE Mains Practice Session", use_container_width=True):
    with st.spinner("ఫైల్స్ విశ్లేషిస్తోంది..."):
        # Bulk Questions Load
        qs = fetch_mains_only_questions(selected_sub)
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.rerun()
        else:
            st.error("AI స్పందించడం లేదు. మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం
if st.session_state.mains_bank:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5:")
        st.info(q['question'])
        
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_final_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution", use_container_width=True):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == q['answer']: 
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Long Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️", use_container_width=True):
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
