import streamlit as st
import pandas as pd

# 1. Setup Mock Data (Replace with your actual questions)
questions = [
    {"question": "What is the capital of France?", "options": ["London", "Paris", "Berlin"], "answer": "Paris"},
    {"question": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter"], "answer": "Mars"},
    {"question": "What is 5 + 5?", "options": ["10", "12", "15"], "answer": "10"},
]

total = len(questions)

# 2. Initialize Session State
if 'selected' not in st.session_state:
    st.session_state.selected = [None] * total
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

st.title("🚀 Python Quiz App")

# 3. Quiz Interface
for i, q in enumerate(questions):
    st.subheader(f"Q{i+1}: {q['question']}")
    # Radio button for each question
    st.session_state.selected[i] = st.radio(
        f"Select an answer for Q{i+1}:", 
        q['options'], 
        index=None, 
        key=f"q_{i}",
        disabled=st.session_state.submitted
    )
    st.divider()

# 4. Submit Logic
if st.button("Submit Quiz") and not st.session_state.submitted:
    correct_count = 0
    for i, q in enumerate(questions):
        if st.session_state.selected[i] == q['answer']:
            correct_count += 1
    
    st.session_state.score = correct_count
    st.session_state.submitted = True
    st.rerun()

# 5. Answer Analysis (Your logic with UI enhancements)
if st.session_state.submitted:
    st.success(f"Quiz Completed! Your Score: {st.session_state.score} / {total}")
    
    if st.button("📊 Show Detailed Answer Analysis"):
        try:
            analysis_data = []
            for i, q in enumerate(questions):
                sel = st.session_state.selected[i] if st.session_state.selected[i] else "No Answer"
                status = "✅ Correct" if sel == q['answer'] else "❌ Wrong"
                
                analysis_data.append({
                    "Q No.": i+1,
                    "Question": q['question'],
                    "Your Answer": sel,
                    "Correct Answer": q['answer'],
                    "Status": status
                })
            
            df = pd.DataFrame(analysis_data)
            
            # Applying conditional formatting to the Status column
            def color_status(val):
                color = '#28a745' if "✅" in val else '#dc3545'
                return f'color: {color}; font-weight: bold'

            styled_df = df.style.map(color_status, subset=['Status'])

            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Summary Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Correct", st.session_state.score)
            c2.metric("Wrong", total - st.session_state.score)
            c3.metric("Grade", f"{(st.session_state.score/total)*100:.1f}%")

        except Exception as e:
            st.error(f"Error generating analysis: {e}")

    if st.button("🔄 Restart Quiz"):
        st.session_state.clear()
        st.rerun()
