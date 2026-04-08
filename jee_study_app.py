# =============================
# 6️⃣ Answer Analysis (Diff Format)
# =============================
if st.button("📊 Show Answer Analysis"):
    try:
        analysis_data = []
        for i, q in enumerate(questions):
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
        st.write(f"✅ Total Correct: {st.session_state.score} / {total}")
        st.write(f"❌ Total Wrong: {total - st.session_state.score}")
        st.write(f"📈 Percentage: {(st.session_state.score/total)*100:.2f}%")
    except Exception as e:
        st.error(f"Error generating Answer Analysis: {e}")
