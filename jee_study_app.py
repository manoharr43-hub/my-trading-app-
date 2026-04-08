import streamlit as st

# =============================
# 1️⃣ 40 JEE Questions with Step-by-Step Explanation
# =============================
# For demo, 10 questions shown; copy/paste to make full 40
questions = [
    {
        "question": "Mathematics: Solve for x: 2x + 3 = 7",
        "options": ["1", "2", "3", "4"],
        "answer": "2",
        "explanation": """Step-by-Step:
1. 2x + 3 = 7
2. 2x = 4
3. x = 2"""
    },
    {
        "question": "Physics: Time to fall 20 m freely under gravity?",
        "options": ["2 s", "4 s", "3 s", "5 s"],
        "answer": "2 s",
        "explanation": """Step-by-Step:
s = 0.5*g*t^2
20 = 0.5*10*t^2
20 = 5*t^2
t^2=4 => t=2 s"""
    },
    {
        "question": "Chemistry: Molecular formula of water?",
        "options": ["H2O", "H2O2", "HO", "O2H2"],
        "answer": "H2O",
        "explanation": "Step-by-Step:\nWater has 2 H + 1 O → H2O"
    },
    {
        "question": "Mathematics: Value of 3^2 + 4^2?",
        "options": ["25", "12", "7", "10"],
        "answer": "25",
        "explanation": "Step-by-Step:\n3^2 + 4^2 = 9 + 16 = 25"
    },
    {
        "question": "Physics: Speed formula?",
        "options": ["s = d/t", "v = t/d", "v = s*t", "v = d^2/t"],
        "answer": "s = d/t",
        "explanation": "Step-by-Step:\nSpeed = distance / time"
    },
    {
        "question": "Chemistry: Atomic number of Oxygen?",
        "options": ["8", "16", "12", "6"],
        "answer": "8",
        "explanation": "Step-by-Step:\nOxygen has 8 protons → atomic number = 8"
    },
    {
        "question": "Mathematics: Solve x^2 = 9",
        "options": ["3", "-3", "±3", "0"],
        "answer": "±3",
        "explanation": """Step-by-Step:
1. x^2 = 9
2. x = ±3"""
    },
    {
        "question": "Physics: Unit of Force?",
        "options": ["Newton", "Pascal", "Watt", "Joule"],
        "answer": "Newton",
        "explanation": "Step-by-Step:\nForce unit in SI = Newton (N)"
    },
    {
        "question": "Chemistry: pH of neutral solution?",
        "options": ["7", "0", "14", "1"],
        "answer": "7",
        "explanation": "Step-by-Step:\nNeutral solution pH = 7"
    },
    {
        "question": "Mathematics: Value of sin 90°?",
        "options": ["0", "1", "0.5", "√2/2"],
        "answer": "1",
        "explanation": "Step-by-Step:\nsin 90° = 1"
    }
    # Copy-paste similar blocks to make total 40 questions
]

# =============================
# 2️⃣ Session State
# =============================
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'answered' not in st.session_state:
    st.session_state.answered = [False]*len(questions)

# =============================
# 3️⃣ Streamlit UI
# =============================
st.title("🎓 JEE Mains Practice Quiz")
st.caption("Continuous Quiz | Step-by-Step Solutions | Score Tracking")
st.divider()

idx = st.session_state.quiz_idx
total = len(questions)
q = questions[idx]

st.subheader(f"Question {idx + 1} / {total}")
st.write(q['question'])

choice = st.radio("Select your answer:", q['options'], key=f"q_{idx}")

# Check Answer Button
if st.button("🔍 Check Answer") and not st.session_state.answered[idx]:
    if choice == q['answer']:
        st.success("Correct! ✅")
        st.session_state.score += 1
    else:
        st.error(f"Wrong! Correct answer: {q['answer']} ❌")
    
    with st.expander("📖 Step-by-Step Explanation:", expanded=True):
        st.text(q['explanation'])
    
    st.session_state.answered[idx] = True

# Previous / Next Buttons (No st.experimental_rerun needed)
col1, col2 = st.columns(2)
with col1:
    if st.button("⬅️ Previous") and idx > 0:
        st.session_state.quiz_idx -= 1
with col2:
    if st.button("➡️ Next"):
        if idx < total - 1:
            st.session_state.quiz_idx += 1
        else:
            st.success(f"Quiz Finished! Final Score: {st.session_state.score}/{total}")
            # Reset for new session
            st.session_state.quiz_idx = 0
            st.session_state.score = 0
            st.session_state.answered = [False]*len(questions)
