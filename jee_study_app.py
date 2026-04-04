import streamlit as st

st.set_page_config(page_title="Babu's JEE Quiz", page_icon="📝")
st.title("🎓 BABU'S JEE QUIZ APP")

# Sidebar
st.sidebar.header("Settings")
year = st.sidebar.radio("Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject:", ["Physics", "Chemistry", "Mathematics"])

# --- Question Bank (ఇక్కడ మరిన్ని ప్రశ్నలు యాడ్ చేయవచ్చు) ---
quiz_data = {
    "1st Year": {
        "Chemistry": [
            {"q": "Atomic number of Hydrogen?", "options": ["1", "2", "3", "4"], "correct": "1"},
            {"q": "Formula of Water?", "options": ["CO2", "H2O", "NaCl", "O2"], "correct": "H2O"},
            {"q": "Which gas is used in balloons?", "options": ["Nitrogen", "Oxygen", "Helium", "Argon"], "correct": "Helium"}
        ],
        "Physics": [
            {"q": "Unit of Force?", "options": ["Joule", "Watt", "Newton", "Pascal"], "correct": "Newton"},
            {"q": "Value of Acceleration due to gravity (g)?", "options": ["8.9 m/s²", "9.8 m/s²", "10.5 m/s²", "7.2 m/s²"], "correct": "9.8 m/s²"}
        ]
    },
    "2nd Year": {
        "Chemistry": [
            {"q": "Formula of Benzene?", "options": ["C6H12", "C6H6", "CH4", "C2H2"], "correct": "C6H6"}
        ]
    }
}

# Session State to track current question
if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

current_list = quiz_data.get(year, {}).get(subject, [{"q": "No questions yet!", "options": ["N/A"], "correct": "N/A"}])

# Reset index if subject/year changes
if st.session_state.q_no >= len(current_list):
    st.session_state.q_no = 0

# Display Question
st.subheader(f"📍 {year} - {subject}")
q_item = current_list[st.session_state.q_no]

st.info(f"Question {st.session_state.q_no + 1}: {q_item['q']}")

# Multiple Choice Selection
user_choice = st.radio("Select your answer:", q_item['options'], key=f"q_{st.session_state.q_no}")

# Submit Button
if st.button('Check Answer'):
    if user_choice == q_item['correct']:
        st.success("✅ Correct! Sabash Babu! 👏")
        st.balloons() # విజయం గుర్తింపుగా బెలూన్లు ఎగురుతాయి
    else:
        st.error(f"❌ Wrong! The correct answer is: {q_item['correct']}")

# Navigation
st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button('⬅️ Previous'):
        if st.session_state.q_no > 0:
            st.session_state.q_no -= 1
            st.rerun()
with col2:
    if st.button('Next ➡️'):
        if st.session_state.q_no < len(current_list) - 1:
            st.session_state.q_no += 1
            st.rerun()

st.caption("All the best for your JEE Preparation, Babu! 👍")
