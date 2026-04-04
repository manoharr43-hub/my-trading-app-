import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Sai Rakshith's JEE Academy", page_icon="🎓")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar settings
st.sidebar.header("Study Settings")
year = st.sidebar.radio("Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.selectbox("Exam Level:", ["Board Level", "JEE Mains", "JEE Advanced"])

# --- Expanded Question Bank ---
quiz_data = [
    # 1st Year Physics
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "Define 1 Newton of Force.", "opt": ["1 kg.m/s", "1 kg.m/s²", "1 g.cm/s²", "1 kg.m²/s²"], "corr": "1 kg.m/s²", "exp": "1 Newton is the force required to accelerate 1kg mass at 1m/s²."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Work done by a centripetal force is?", "opt": ["Positive", "Negative", "Zero", "Infinite"], "corr": "Zero", "exp": "Since force and displacement are perpendicular, $W = Fd \cos(90) = 0$."},
    
    # 1st Year Maths
    {"year": "1st Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Value of tan(45°)?", "opt": ["0", "1", "√3", "1/√3"], "corr": "1", "exp": "Standard value: tan(45) = 1."},
    
    # 2nd Year Physics
    {"year": "2nd Year", "sub": "Physics", "lvl": "Board Level", "q": "What is the unit of Power of a Lens?", "opt": ["Meter", "Dioptre", "Watt", "Candela"], "corr": "Dioptre", "exp": "Power of lens $P = 1/f$ is measured in Dioptres (D)."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Resistance of an ideal ammeter is?", "opt": ["High", "Low", "Zero", "Infinite"], "corr": "Zero", "exp": "An ideal ammeter should not affect the current, so its resistance must be zero."}
]

# Filtering questions
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"⚠️ No {level} questions in {subject} yet. Try 'JEE Mains' or another Subject!")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    q = current_qs[st.session_state.q_idx % len(current_qs)]
    
    st.subheader(f"📍 {year} - {subject} ({level})")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Select Answer:", q['opt'], key=f"{year}_{subject}_{level}")
    
    if st.button('Submit Answer'):
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        st.session_state.history.append({"Time": datetime.now().strftime("%H:%M"), "Subject": f"{subject}({level})", "Result": res})
        
        if choice == q['corr']:
            st.success("Correct! Well done Sai Rakshith! 🎯")
            st.balloons()
        else:
            st.error(f"Wrong. Correct Answer: {q['corr']}")
        st.write(f"**Explanation:** {q['exp']}")

# History Table
st.markdown("---")
st.subheader("📊 Practice History")
if st.session_state.history:
    st.table(pd.DataFrame(st.session_state.history))

st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx = (st.session_state.get('q_idx', 0) + 1)
    st.rerun()
