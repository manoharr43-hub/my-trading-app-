import streamlit as st
import json
import pdfplumber

# =============================
# 1️⃣ Upload PDF or load from GitHub
# =============================
uploaded_file = st.file_uploader("Upload JEE PDF Question Paper", type="pdf")

questions = []

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Basic splitting based on numbering (1., 2., etc.)
            for line in text.split("\n"):
                if line.strip().startswith(tuple(str(i)+'.' for i in range(1,101))):
                    # Simple parsing: split question and options
                    parts = line.split(")")  # assuming options end with A) B) C) D)
                    if len(parts) >= 5:
                        question_text = parts[0]
                        options = [parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()]
                        # For demo, set answer to first option (can manually edit JSON later)
                        questions.append({
                            "question": question_text,
                            "options": options,
                            "answer": options[0]
                        })

# =============================
# 2️⃣ Session State for Quiz
# =============================
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0

# =============================
# 3️⃣ Display Quiz
# =============================
if questions:
    idx = st.session_state.quiz_idx
    total = len(questions)
    q = questions[idx]

    st.subheader(f"Question {idx+1}/{total}")
    st.write(q['question'])

    choice = st.radio("Select your answer:", q['options'], key=f"q_{idx}")

    if st.button("Check Answer"):
        if choice == q['answer']:
            st.success("Correct! ✅")
            st.session_state.score += 1
        else:
            st.error(f"Wrong! Correct answer: {q['answer']} ❌")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous") and idx > 0:
            st.session_state.quiz_idx -= 1
    with col2:
        if st.button("Next") and idx < total-1:
            st.session_state.quiz_idx += 1

    st.write(f"Current Score: {st.session_state.score}/{total}")
else:
    st.info("Upload a PDF question paper to start the quiz.")
