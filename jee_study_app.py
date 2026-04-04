import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Sai Rakshith's JEE Master", page_icon="🎓", layout="wide")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.header("📝 Exam Settings")
year = st.sidebar.radio("Select Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.selectbox("Select Exam Level:", ["Board Level", "JEE Mains", "JEE Advanced"])

# --- Full Question Bank (1st & 2nd Year) ---
quiz_data = [
    # --- 1st YEAR ---
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "What is the SI unit of Force?", "opt": ["Joule", "Newton", "Watt", "Pascal"], "corr": "Newton", "exp": "Force = m x a. SI unit is Newton (N)."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Dimension of G?", "opt": ["[M⁻¹L³T⁻²]", "[ML²T⁻²]", "[M⁻¹L²T⁻¹]", "[MLT⁻²]"], "corr": "[M⁻¹L³T⁻²]", "exp": "Calculated using F = Gm1m2/r²."},
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Identify the intensive property?", "opt": ["Mass", "Volume", "Density", "Heat capacity"], "corr": "Density", "exp": "Density does not depend on the size or amount of matter."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Number of subsets of set with 'n' elements?", "opt": ["n²", "2n", "2^n", "n!"], "corr": "2^n", "exp": "Formula for total subsets is 2^n."},

    # --- 2nd YEAR ---
    # Physics 2nd Year
    {"year": "2nd Year", "sub": "Physics", "lvl": "Board Level", "q": "Ohm's law is V = ?", "opt": ["I/R", "IR", "I²R", "R/I"], "corr": "IR", "exp": "V = IR where R is resistance."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Ideal Voltmeter resistance?", "opt": ["Zero", "Low", "Infinite", "100 Ohm"], "corr": "Infinite", "exp": "Ideal voltmeter should not draw any current."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "What is Lenz's Law based on?", "opt": ["Mass", "Charge", "Energy", "Momentum"], "corr": "Energy", "exp": "Lenz's Law is a consequence of Conservation of Energy."},

    # Chemistry 2nd Year
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "Board Level", "q": "pH of neutral water?", "opt": ["0", "7", "14", "1"], "corr": "7", "exp": "Neutral pH is always 7."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Mains", "q": "Shape of PCl5 molecule?", "opt": ["Square Planar", "Tetrahedral", "Trigonal Bipyramidal", "Octahedral"], "corr": "Trigonal Bipyramidal", "exp": "PCl5 has sp³d hybridization."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Hybridization of Xenon in XeF4?", "opt": ["sp3", "sp3d", "sp3d2", "dsp2"], "corr": "sp3d2", "exp": "XeF4 has 4 bond pairs and 2 lone pairs."},

    # Mathematics 2nd Year
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Derivative of cos(x)?", "opt": ["sin(x)", "-sin(x)", "tan(x)", "cos(x)"], "corr": "-sin(x)", "exp": "d/dx(cos x) = -sin x."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Integration of 1/x dx?", "opt": ["x", "log|x|", "e^x", "1"], "corr": "log|x|", "exp": "Integral of 1/x is natural logarithm."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "Value of Integral e^x(sin x + cos x)dx?", "opt": ["e^x sin x", "e^x cos x", "e^x tan x", "sin x"], "corr": "e^x sin x", "exp": "Using formula integral e^x(f(x) + f'(x)) = e^x f(x)."}
]

# Filtering
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"⚠️ No questions in {year} {subject} at {level} level yet. Try another Level!")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    idx = st.session_state.q_idx % len(current_qs)
    q = current_qs[idx]
    
    st.subheader(f"📍 {year} - {subject} | {level}")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Select Answer:", q['opt'], key=f"q_{year}_{subject}_{level}_{idx}")
    
    if st.button('Submit Answer'):
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        st.session_state.history.append({"Time": datetime.now().strftime("%H:%M"), "Subject": f"{subject}({level})", "Result": res})
        
        if choice == q['corr']:
            st.success("Correct! Excellent, Sai Rakshith! 🎯")
            st.balloons()
        else:
            st.error(f"Incorrect. Correct answer: {q['corr']}")
        st.markdown(f"**Explanation:** {q['exp']}")

# Navigation
st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx += 1
    st.rerun()

# History Table
st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice Log")
if st.session_state.history:
    st.table(pd.DataFrame(st.session_state.history))
