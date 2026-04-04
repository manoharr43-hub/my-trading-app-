import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Babu's JEE Revision", page_icon="📅")
st.title("🎓 BABU'S JEE QUIZ & REVISION LOG")

# --- Session State for History ---
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.header("Settings")
year = st.sidebar.radio("Year Selection:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject Selection:", ["Physics", "Chemistry", "Mathematics"])

# --- Question Bank ---
quiz_data = {
    "1st Year": {
        "Physics": [
            {"q": "What is the unit of Force?", "options": ["Joule", "Newton", "Watt", "Pascal"], "correct": "Newton", "exp": "Force = m × a. Unit is Newton."},
            {"q": "Value of 'g'?", "options": ["9.8 m/s²", "8.8 m/s²", "10 m/s²", "7 m/s²"], "correct": "9.8 m/s²", "exp": "Standard gravity is 9.8 m/s²."}
        ],
        "Chemistry": [
            {"q": "Atomic number of Helium?", "options": ["1", "2", "3", "4"], "correct": "2", "exp": "Helium is the 2nd element."}
        ]
    }
}

if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

current_list = quiz_data.get(year, {}).get(subject, [{"q": "No questions!", "options": ["N/A"], "correct": "N/A", "exp": "N/A"}])

# Display Question
st.subheader(f"📍 {year} - {subject}")
q_item = current_list[st.session_state.q_no % len(current_list)]

st.info(f"Question: {q_item['q']}")
user_choice = st.radio("Choose option:", q_item['options'], key=f"rev_{st.session_state.q_no}")

if st.button('Submit & Save to History'):
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    status = "✅ Correct" if user_choice == q_item['correct'] else "❌ Wrong"
    
    # సేవ్ చేయడం
    st.session_state.history.append({
        "Date & Time": now,
        "Subject": subject,
        "Question": q_item['q'],
        "Result": status
    })
    
    if user_choice == q_item['correct']:
        st.success(f"{status}! Sabash Babu.")
    else:
        st.error(f"{status}! Correct: {q_item['correct']}")
    st.warning(f"💡 Explanation: {q_item['exp']}")

# --- Revision Table (Date Column) ---
st.write("---")
st.subheader("📚 Babu's Practice History (Revision Log)")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    # టేబుల్ ని అందంగా చూపించడం
    st.table(df)
    
    if st.button('Clear History'):
        st.session_state.history = []
        st.rerun()
else:
    st.write("ఇంకా ప్రాక్టీస్ మొదలుపెట్టలేదు. All the best!")

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
