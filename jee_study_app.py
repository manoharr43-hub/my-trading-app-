import streamlit as st
import json
import pandas as pd

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your JSON file", type=["json"])

if uploaded_file is not None:
    questions = json.load(uploaded_file)
    total = len(questions)
    
    # --- Session State ---
    if 'quiz_idx' not in st.session_state:
        st.session_state.quiz_idx = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'answered' not in st.session_state:
        st.session_state.answered = [False]*total
    if 'selected' not in st.session_state:
        st.session_state.selected = [""]*total

    # --- Current Question ---
    idx = st.session_state.quiz_idx
    q = questions[idx]
    st.subheader(f"Question {idx + 1} / {total}")
    st.write(q['question'])
    choice = st.radio("Select your answer:", q['options'], key=f"q_{idx}")

    # --- Check Answer ---
    if st.button("🔍 Check Answer"):
        st.session_state.selected[idx] = choice
        if not st.session_state.answered[idx]:
            if choice == q['answer']:
                st.success("Correct! ✅")
                st.session_state.score += 1
            else:
                st.error(f"Wrong! Correct answer: {q['answer']} ❌")
            st.session_state.answered[idx] = True
        with st.expander("📖 Step-by-Step Explanation:", expanded=True):
            st.text(q['explanation'])

    # --- Navigation ---
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

    # --- Answer Analysis Table ---
    if st.button("📊 Show Answer Analysis"):
        data = []
        for i, q in enumerate(questions):
            sel = st.session_state.selected[i] if st.session_state.selected[i] else "-"
            status = "✅ Correct" if sel == q['answer'] else "❌ Wrong"
            data.append({
                "Q No.": i+1,
                "Question": q['question'],
                "Your Answer": sel,
                "Correct Answer": q['answer'],
                "Status": status
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.write(f"✅ Total Correct: {st.session_state.score} / {total}")
        st.write(f"❌ Total Wrong: {total - st.session_state.score}")
        st.write(f"📈 Percentage: {(st.session_state.score/total)*100:.2f}%")
