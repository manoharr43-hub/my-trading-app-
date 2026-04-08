import streamlit as st
import google.generativeai as genai
import json
import os

# =============================
# 1️⃣ Gemini AI Setup
# =============================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# =============================
# 2️⃣ Load old questions
# =============================
QUESTIONS_FILE = 'jee_mains_questions.json'
try:
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            old_questions = json.load(f)
    else:
        old_questions = []
except json.JSONDecodeError:
    old_questions = []

# =============================
# 3️⃣ Generate New Questions
# =============================
def generate_new_questions(subject, count=5):
    prompt = f"""
    Act as a JEE Mains Expert.
    Generate {count} HIGH-QUALITY MCQs strictly for {subject}.
    Each question must have:
    - question
    - options ["A","B","C","D"]
    - answer
    - explanation (step-by-step solution)
    Return ONLY raw JSON list.
    """
    try:
        response = model.generate_text(prompt=prompt)
        text = response.text.strip().replace("\n", " ").replace("'", '"')
        new_questions = json.loads(text)
        if isinstance(new_questions, list):
            return new_questions
        else:
            st.error("AI JSON response list కాకుండా వచ్చింది.")
            return []
    except Exception as e:
        st.error(f"AI response parsing లో problem: {e}")
        return []

# =============================
# 4️⃣ Streamlit Session State
# =============================
if 'mains_bank' not in st.session_state: st.session_state.mains_bank = []
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans_show' not in st.session_state: st.session_state.ans_show = False
if 'current_subject' not in st.session_state: st.session_state.current_subject = ""

# =============================
# 5️⃣ UI Design
# =============================
st.title("🎓 SAI RAKSHITH JEE FAST-TRACK")
st.caption("Auto-Retry Mode: Instant Questions with Long Solutions")
st.divider()

# Subject selection
selected_sub = st.selectbox("సబ్జెక్ట్ ఎంచుకోండి:", ["Mathematics", "Physics", "Chemistry"])

# =============================
# 6️⃣ Generate New Questions Button
# =============================
if st.button(f"🚀 Generate 5 New {selected_sub} Questions"):
    with st.spinner("AI నుండి కొత్త ప్రశ్నలు సృష్టిస్తోంది..."):
        new_qs = generate_new_questions(selected_sub, count=5)
        if new_qs:
            all_questions = old_questions + new_qs
            st.session_state.mains_bank = new_qs
            st.session_state.idx = 0
            st.session_state.ans_show = False
            st.session_state.current_subject = selected_sub

            with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_questions, f, indent=4, ensure_ascii=False)

            st.success(f"{len(new_qs)} కొత్త ప్రశ్నలు సృష్టించబడ్డాయి! మొత్తం questions: {len(all_questions)}")
        else:
            st.error("AI కొత్త questions generate చేయలేకపోయింది. Retry చేయండి.")

# =============================
# 7️⃣ Display Questions
# =============================
if st.session_state.mains_bank and st.session_state.current_subject == selected_sub:
    curr = st.session_state.idx
    total = len(st.session_state.mains_bank)
    
    q = st.session_state.mains_bank[curr]
    st.divider()
    st.subheader(f"ప్రశ్న {curr + 1} / {total} ({selected_sub}):")
    st.info(q['question'])

    choice = st.radio("నీ సమాధానం ఎంచుకో:", q['options'], key=f"mains_{curr}")

    # Buttons
    check = st.button("🔍 Check Answer & Detailed Solution", key=f"check_{curr}")
    prev = st.button("⬅️ Previous Question", key=f"prev_{curr}")
    nxt = st.button("➡️ Next Question", key=f"next_{curr}")

    # Check Answer
    if check:
        st.session_state.ans_show = True

    if st.session_state.ans_show:
        if choice == q['answer']:
            st.success("అద్భుతం! సరైన సమాధానం! ✅")
        else:
            st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")
        with st.expander("📖 Step-by-Step Long Solution:", expanded=True):
            st.write(q['explanation'])

    # Previous Question
    if prev and curr > 0:
        st.session_state.idx -= 1
        st.session_state.ans_show = False
        st.experimental_rerun()

    # Next Question
    if nxt:
        if curr < total - 1:
            st.session_state.idx += 1
            st.session_state.ans_show = False
            st.experimental_rerun()
        else:
            st.success("వెరీ గుడ్ బాబు! ఈ సెషన్ పూర్తి చేసావు.")
            st.session_state.mains_bank = []
            st.session_state.current_subject = ""

else:
    st.write("బాబు, పైన ఉన్న బటన్ నొక్కి కొత్త questions generate చేయండి.")

st.divider()
st.caption("Managed by Manohar - Variety Motors | Dedicated to Sai Rakshith's JEE Mains Success")
