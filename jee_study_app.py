import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Babu's JEE Pro", page_icon="🚀")
st.title("🎓 BABU'S JEE MAINS & ADVANCED PREP")

# Sidebar for advanced settings
st.sidebar.header("Exam Settings")
year = st.sidebar.radio("Select Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.select_slider("Select Difficulty Level:", options=["Board Level", "JEE Mains", "JEE Advanced"])

# --- Advanced JEE Question Bank ---
quiz_data = {
    "1st Year": {
        "Physics": [
            {
                "level": "JEE Mains",
                "q": "A ball is thrown vertically upwards with velocity 'u'. What is the maximum height reached?",
                "options": ["u/g", "u²/2g", "u²/g", "2u/g"],
                "correct": "u²/2g",
                "exp": "Using kinematic equation $v^2 - u^2 = 2as$. At max height $v=0$, and $a=-g$. So, $0 - u^2 = 2(-g)H \Rightarrow H = u^2/2g$."
            },
            {
                "level": "JEE Advanced",
                "q": "If the error in measurement of radius of a sphere is 2%, what is the error in volume?",
                "options": ["2%", "4%", "6%", "8%"],
                "correct": "6%",
                "exp": "Volume of sphere $V = (4/3)\pi r^3$. Error $\Delta V/V = 3 \times (\Delta r/r)$. So, $3 \times 2\% = 6\%$."
            }
        ],
        "Mathematics": [
            {
                "level": "JEE Mains",
                "q": "What is the number of subsets of a set containing 'n' elements?",
                "options": ["n²", "2n", "2^n", "n!"],
                "correct": "2^n",
                "exp": "Each element has 2 choices (either in the subset or not). For 'n' elements, it is $2 \times 2 \times ... \times 2$ (n times) = $2^n$."
            }
        ]
    },
    "2nd Year": {
        "Physics": [
            {
                "level": "JEE Mains",
                "q": "Two capacitors of 2μF and 3μF are in series. What is the equivalent capacitance?",
                "options": ["5μF", "1.2μF", "6μF", "0.5μF"],
                "correct": "1.2μF",
                "exp": "In series, $1/C_{eq} = 1/C1 + 1/C2$. So, $1/C_{eq} = 1/2 + 1/3 = 5/6$. $C_{eq} = 6/5 = 1.2\mu F$."
            }
        ],
        "Chemistry": [
            {
                "level": "JEE Advanced",
                "q": "Which of the following has the highest boiling point?",
                "options": ["He", "Ne", "Ar", "Kr"],
                "correct": "Kr",
                "exp": "Boiling point increases with atomic size and Van der Waals forces. Krypton (Kr) is the largest among the given noble gases."
            }
        ]
    }
}

# Session State
if 'q_idx' not in st.session_state:
    st.session_state.q_idx = 0

# Filtering questions based on level
all_qs = quiz_data.get(year, {}).get(subject, [])
filtered_qs = [q for q in all_qs if q['level'] == level]

if not filtered_qs:
    st.warning(f"No questions available for {level} in {subject} yet. Try another level!")
else:
    q_item = filtered_qs[st.session_state.q_idx % len(filtered_qs)]
    
    st.subheader(f"📍 {year} - {subject} ({level})")
    st.info(f"Question: {q_item['q']}")
    
    user_choice = st.radio("Select Answer:", q_item['options'], key=f"jee_{year}_{subject}_{level}_{st.session_state.q_idx}")
    
    if st.button('Submit Answer'):
        is_correct = user_choice == q_item['correct']
        if is_correct:
            st.success("Brilliant Babu! That's a JEE level correct answer! 🎯")
            st.balloons()
        else:
            st.error(f"Incorrect. The correct answer is: {q_item['correct']}")
        
        st.markdown(f"### 💡 Conceptual Explanation:")
        st.write(q_item['exp'])

# Navigation
st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button('⬅️ Previous'):
        st.session_state.q_idx -= 1
        st.rerun()
with col2:
    if st.button('Next Question ➡️'):
        st.session_state.q_idx += 1
        st.rerun()
