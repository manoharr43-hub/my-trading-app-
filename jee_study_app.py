import streamlit as st
import json

# =============================
# 1️⃣ Sample Questions (Manual JSON)
# =============================
# Replace or extend with your 40 questions from GitHub PDF
questions = [
    {
        "question": "Math: What is the value of 2+2?",
        "options": ["3", "4", "5", "6"],
        "answer": "4"
    },
    {
        "question": "Physics: What is acceleration due to gravity?",
        "options": ["9.8 m/s²", "10 m/s²", "8 m/s²", "12 m/s²"],
        "answer": "9.8 m/s²"
    },
    {
        "question": "Chemistry: H2O is called?",
        "options": ["Hydrogen", "Oxygen", "Water", "Hydroxide"],
        "answer": "Water"
    },
    # Add remaining 37 questions here...
]

# =============================
# 2️⃣ Streamlit Session State
# =============================
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0

# =============================
# 3️⃣ Quiz UI
# =============================
st.title("🎓 SAI RAKSHITH JEE QUIZ")
st.caption("Manual Questions JSON Mode | No AI Required")
st.divider()

if questions:
    idx = st.session_state.quiz_idx
    total = len(questions)
    q = questions[idx]

    st.subheader(f"ప్రశ్న {idx + 1} / {total}")
    st.write(q['question'])

    choice = st.radio("నీ సమాధానం ఎంచుకో:", q['options'], key=f"q_{idx}")

    # Buttons
    check = st.button("🔍 Check Answer", key=f"check_{idx}")
    prev = st.button("⬅️ Previous", key=f"prev_{idx}")
    nxt = st.button("➡️ Next", key=f"next_{idx}")

    # Check Answer
    if check:
        if choice == q['answer']:
            st.success("అద్భుతం! సరైన సమాధానం! ✅")
            st.session_state.score += 1
        else:
            st.error(f"తప్పు! సరైన సమాధానం: {q['answer']} ❌")

    # Previous
    if prev and idx > 0:
        st.session_state.quiz_idx -= 1
        st.experimental_rerun()

    # Next
    if nxt:
        if idx < total - 1:
            st.session_state.quiz_idx += 1
            st.experimental_rerun()
        else:
            st.success(f"వెరీ గుడ్ బాబు! Quiz పూర్తయింది. Final Score: {st.session_state.score}/{total}")
            st.session_state.quiz_idx = 0
            st.session_state.score = 0

else:
    st.info("Questions JSON empty. Add your 40 questions manually.")
