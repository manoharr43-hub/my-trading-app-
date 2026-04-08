import streamlit as st
import pdfplumber
import pandas as pd
import json
import random

st.set_page_config(page_title="📚 JEE Quiz App", layout="wide")
st.title("📚 JEE Mains Practice Quiz App")
st.caption("Upload PDF or JSON of questions → Select questions → Practice → See Answer Analysis")

# =============================
# 1️⃣ Upload PDF or JSON
# =============================
uploaded_file = st.file_uploader("Upload your JEE question paper PDF or JSON", type=["pdf","json"])

questions = []

if uploaded_file is not None:
    if uploaded_file.type == "application/json":
        try:
            questions = json.load(uploaded_file)
            st.success(f"{len(questions)} questions loaded from JSON.")
        except Exception as e:
            st.error(f"Error loading JSON: {e}")
    elif uploaded_file.type == "application/pdf":
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
            st.text_area("Preview extracted text:", full_text[:1000])
            st.info("Manual conversion to JSON recommended for clean quiz practice.")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

# =============================
# 2️⃣ Select Number of Questions
# =============================
if questions:
    total_questions = len(questions)
    num_questions = st.number_input(f"Select number of questions for this session (max {total_questions}):",
                                    min_value=1, max_value=total_questions, value=min(10,total_questions))
    
    if 'quiz_questions' not in st.session_state or st.session_state.get('questions_loaded_for') != uploaded_file.name:
        st.session_state.quiz_questions = random.sample(questions, k=num_questions)
        st.session_state.quiz_idx = 0
        st.session_state.score = 0
        st.session_state.answered = [False]*num_questions
        st.session_state.selected = [""]*num_questions
        st.session_state.questions_loaded_for = uploaded_file.name

    # =============================
    # 3️⃣ Display Current Question
    # =============================
    idx = st.session_state.quiz_idx
    q = st.session_state.quiz_questions[idx]

    st.subheader(f"Question {idx+1} / {num_questions}")
    st.write(q['question'])
    choice = st.radio("Select your answer:", q['options'], key=f"q_{idx}")

    # =============================
    # 4️⃣ Check Answer & Show Explanation
    # =============================
    if st.button("🔍 Check Answer"):
        st.session_state.selected[idx] = choice
        if not st.session_state.answered[idx]:
            if choice == q['answer']:
                st.success("Correct ✅")
                st.session_state.score += 1
            else:
                st.error(f"Wrong ❌. Correct answer: {q['answer']}")
            st.session_state.answered[idx] = True
        with st.expander("📖 Step-by-Step Explanation", expanded=True):
            st.write(q['explanation'])

    # =============================
    # 5️⃣ Navigation
    # =============================
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous") and idx > 0:
            st.session_state.quiz_idx -= 1
    with col2:
        if st.button("➡️ Next"):
            if idx < num_questions-1:
                st.session_state.quiz_idx += 1
            else:
                st.success(f"🎉 Quiz Finished! Score: {st.session_state.score}/{num_questions}")
                if st.button("🔄 Restart Quiz"):
                    st.session_state.quiz_idx = 0
                    st.session_state.score = 0
                    st.session_state.answered = [False]*num_questions
                    st.session_state.selected = [""]*num_questions

    # =============================
    # 6️⃣ Answer Analysis (Diff Table)
    # =============================
    try:
        if st.button("📊 Show Answer Analysis"):
            analysis_data = []
            for i, q in enumerate(st.session_state.quiz_questions):
                sel = st.session_state.selected[i] if st.session_state.selected[i] else "-"
                status = "✅ Correct" if sel == q['answer'] else "❌ Wrong"
                analysis_data.append({
                    "Q No.": i+1,
                    "Question": q['question'],
                    "Your Answer": sel,
                    "Correct Answer": q['answer'],
                    "Status": status
                })
            df = pd.DataFrame(analysis_data)
            st.dataframe(df, use_container_width=True)
            st.write(f"✅ Total Correct: {st.session_state.score} / {num_questions}")
            st.write(f"❌ Total Wrong: {num_questions - st.session_state.score}")
            st.write(f"📈 Percentage: {(st.session_state.score/num_questions)*100:.2f}%")
    except Exception as e:
        st.error(f"Error generating Answer Analysis: {e}")

else:
    st.info("Upload a PDF or JSON file to start the quiz session.")

st.divider()
st.caption("Managed by Manohar | Dedicated to Sai Rakshith's JEE Mains Success")
