import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Babu's JEE Master", page_icon="🎓")
st.title("🎓 BABU'S JEE QUIZ & DEEP LEARNING")

# --- History Tracking ---
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.header("Settings")
year = st.sidebar.radio("Select Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])

# --- Detailed Question Bank (English Medium) ---
quiz_data = {
    "1st Year": {
        "Physics": [
            {
                "q": "What is the SI unit of Force?", 
                "options": ["Joule", "Newton", "Watt", "Pascal"], 
                "correct": "Newton",
                "exp": """
                **DEEP EXPLANATION:**
                * **Formula:** Force is defined as mass times acceleration ($F = m \times a$).
                * **Reason:** The unit 'Newton' is named after Sir Isaac Newton for his laws of motion. 1 Newton is the force needed to accelerate 1 kg of mass at 1 m/s².
                * **Other Options:**
                    - *Joule:* Unit of Work and Energy.
                    - *Watt:* Unit of Power ($P = W/t$).
                    - *Pascal:* Unit of Pressure ($P = F/A$).
                """
            },
            {
                "q": "Which of the following is a vector quantity?", 
                "options": ["Speed", "Distance", "Mass", "Velocity"], 
                "correct": "Velocity",
                "exp": """
                **DEEP EXPLANATION:**
                * **Vector Quantity:** It has both magnitude and direction.
                * **Reason:** Velocity includes direction (e.g., 50 km/h towards North), whereas Speed only has magnitude.
                """
            }
        ],
        "Chemistry": [
            {
                "q": "What is the atomic number of Carbon?", 
                "options": ["4", "6", "8", "12"], 
                "correct": "6",
                "exp": """
                **DEEP EXPLANATION:**
                * **Definition:** The atomic number is the total number of protons in an atom's nucleus.
                * **Fact:** Carbon has 6 protons, so its atomic number is 6. It also has 6 electrons in a neutral state.
                """
            }
        ]
    }
}

if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

current_list = quiz_data.get(year, {}).get(subject, [{"q": "No questions yet!", "options": ["N/A"], "correct": "N/A", "exp": "N/A"}])

# Question Display
st.subheader(f"📍 {year} - {subject}")
q_item = current_list[st.session_state.q_no % len(current_list)]

st.info(f"Question: {q_item['q']}")
user_choice = st.radio("Choose the correct option:", q_item['options'], key=f"eng_q_{st.session_state.q_no}")

if st.button('Submit & Save Progress'):
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    is_correct = user_choice == q_item['correct']
    status = "✅ Correct" if is_correct else "❌ Wrong"
    
    st.session_state.history.append({
        "Date": now,
        "Subject": subject,
        "Result": status,
        "Question": q_item['q'],
        "Your Choice": user_choice,
        "Correct Answer": q_item['correct']
    })
    
    if is_correct:
        st.success("Great job, Babu! Correct answer. 👏")
        st.balloons()
    else:
        st.error(f"Incorrect. The correct answer is: {q_item['correct']}")
    
    # Explanation in English
    st.markdown("---")
    st.markdown(f"### 💡 Explanation (Babu's Guide):")
    st.write(q_item['exp'])

# --- History Log ---
st.write("---")
st.subheader("📊 Practice History Log")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
else:
    st.write("No practice history found yet. Start your quiz now!")

# Navigation
col1, col2 = st.columns(2)
with col1:
    if st.button('⬅️ Previous'):
        st.session_state.q_no -= 1
        st.rerun()
with col2:
    if st.button('Next ➡️'):
        st.session_state.q_no += 1
        st.rerun()
