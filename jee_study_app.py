import streamlit as st
import google.generativeai as genai
import json
import time

# 1. AI సెటప్ (సిలబస్ మరియు ప్యాటర్న్ మోడ్)
GEMINI_API_KEY = "AIzaSyBcHJe7mUNPBsm_TcvY4_EiX3N5ly_srCw" 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.set_page_config(page_title="Sai Rakshith JEE Fast-Track", layout="centered")

# 2. ప్రశ్నలు తెచ్చే ఫంక్షన్ - Strictly by Subject
def fetch_questions_by_subject(subject):
    # ఇక్కడ AI కి ఖచ్చితమైన సమాచారం ఇచ్చాను వేగం కోసం
    prompt = f"""
    Act as a JEE Mains Expert. 
    Use the current JEE Mains syllabus and 2025 question paper patterns as the database.
    Task: Generate 5 HIGH-QUALITY MCQs strictly for JEE MAINS level for {subject} only. 
    Mix: Focus on core concepts and high-weightage topics from {subject}.
    Requirement: Provide a VERY LONG, STEP-BY-STEP solution for each answer. Show core concept, then solution.
    Return ONLY raw JSON list: [{{"question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Detailed Step-by-Step..."}}].
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
if 'current_subject' not in st.session_state: st.session_state.current_subject = ""

# 4. UI డిజైన్
st.title("🎓 SAI RAKSHITH JEE FAST-TRACK")
st.caption("Auto-Retry Mode: Instant Questions with Long Solutions")

st.divider()

# --- సబ్జెక్ట్ సెలెక్షన్ మెనూ (బాబుకి కన్ఫ్యూజన్ లేకుండా) ---
# ఇక్కడ బాబు ఒక సబ్జెక్ట్ ని సెలెక్ట్ చేసుకోగలడు
selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి (JEE Mains Only):", ["Mathematics", "Physics", "Chemistry"])

# బటన్ - AI ఇప్పుడు కేవలం సెలెక్ట్ చేసిన సబ్జెక్ట్ ఫైల్స్ మాత్రమే చూస్తుంది (చాలా ఫాస్ట్ గా ఉంటుంది)
if st.button(f"🚀 Prepare {selected_sub} Exam Paper", use_container_width=True):
    with st.spinner(f"మీ {selected_sub} PDF ఫైల్స్ విశ్లేషిస్తోంది..."):
        # 5 ప్రశ్నలు లోడ్ అవ్వడానికి 5-10 సెకన్లు పడుతుంది (Retry loop వల్ల లోడ్ పడదు)
        qs = fetch_questions_by_subject(selected_sub)
        if qs:
            st.session_state.mains_bank = qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.session_state.current_subject = selected_sub
            st.rerun()
        else:
            st.warning("AI కొంచెం ఎక్కువ టైమ్ తీసుకుంటోంది. దయచేసి మళ్ళీ ఒకసారి బటన్ నొక్కండి.")

# ప్రశ్నలు చూపే భాగం - Safety Check యాడ్ చేశాను IndexError రాదు
if st.session_state.mains_bank and st.session_state.current_subject == selected_sub:
    curr = st.session_state.idx
    if curr < len(st.session_state.mains_bank):
        q = st.session_state.mains_bank[curr]
        st.divider()
        st.subheader(f"ప్రశ్న {curr + 1} / 5 ({selected_sub}):")
        st.info(q['question'])
        
        # correct_ans ని curr లో స్టోర్ చేశాను, దీనివల్ల index out of range రాదు
        correct_ans = q['answer']
        choice = st.radio("నీ సమాధానం:", q['options'], key=f"q_{selected_sub}_{curr}")

        if st.button("🔍 Check Answer & Detailed Solution"):
            st.session_state.ans_show = True

        if st.session_state.ans_show:
            if choice == correct_ans: 
                st.success("అద్భుతం! సరైన సమాధానం! ✅")
            else: 
                st.error(f"తప్పు! సరైన సమాధానం: {correct_ans} ❌")
            
            with st.expander("📖 ఈ లెక్క వెనుక ఉన్న పూర్తి లాజిక్ (Long Solution):", expanded=True):
                st.write(q['explanation'])
            
            if st.button("Next Question ➡️"):
                st.session_state.idx += 1
                st.session_state.ans_show = False
                st.rerun()
    else:
        st.balloons()
        st.success(f"వెరీ గుడ్ బాబు! ఈ {selected_sub} సెషన్ పూర్తి చేసావు.")
        st.session_state.mains_bank = []
        st.session_state.current_subject = ""
elif not st.session_state.mains_bank:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కు. నీ కోసం Mains ప్రశ్నలు సిద్ధంగా ఉంటాయి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Focus: Strictly JEE Mains mixed by Subject")
