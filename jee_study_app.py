import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Sai Rakshith's JEE Master", page_icon="🎓")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar settings
st.sidebar.header("Study Settings")
year = st.sidebar.radio("Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.selectbox("Exam Level:", ["JEE Advanced", "JEE Mains", "Board Level"])

# --- Expanded Question Bank with JEE Advanced Questions ---
quiz_data = [
    # --- 1st Year PHYSICS (Advanced) ---
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "If the error in measurement of radius of a sphere is 2%, what is the error in volume?", "opt": ["2%", "4%", "6%", "8%"], "corr": "6%", "exp": "Volume $V = (4/3) \pi r^3$. Error $\Delta V/V = 3 \times (\Delta r/r) = 3 \times 2% = 6%$."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "A particle moves in a circle of radius R with constant speed v. What is the magnitude of change in velocity when it rotates by 60°?", "opt": ["v", "v/2", "v√3", "2v"], "corr": "v", "exp": "$\Delta v = 2v \sin(\theta/2)$. For $\theta=60$, $\Delta v = 2v \sin(30) = 2v(1/2) = v$."},

    # --- 1st Year CHEMISTRY (Advanced) ---
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Which of the following is an intensive property?", "opt": ["Mass", "Volume", "Enthalpy", "Temperature"], "corr": "Temperature", "exp": "Intensive properties do not depend on the amount of matter (Mass/Volume depend on amount)."},

    # --- 1st Year MATHEMATICS (Advanced) ---
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "Number of subsets of a set with 'n' elements is?", "opt": ["n²", "2n", "2^n", "n!"], "corr": "2^n", "exp": "Each element has 2 choices (in or out). So $2 \times 2 ... \times 2 = 2^n$."},

    # --- 2nd Year PHYSICS (Advanced) ---
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "Two charges +q and -q are separated by distance d. What is the work done in moving a test charge across the perpendicular bisector?", "opt": ["qd", "Zero", "q/d", "2qd"], "corr": "Zero", "exp": "The perpendicular bisector is an equipotential line ($V=0$). So Work $W = q \Delta V = 0$."},

    # --- 2nd Year CHEMISTRY (Advanced) ---
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Hybridization of Carbon in Ethyne ($C_2H_2$)?", "opt": ["sp", "sp2", "sp3", "dsp2"], "corr": "sp", "exp": "Ethyne has a triple bond, leading to sp hybridization."},

    # --- 2nd Year MATHEMATICS (Advanced) ---
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "Derivative of $x^x$ is?", "opt": ["$x^x(1 + \log x)$", "$x \cdot x^{x-1}$", "$1 + \log x$", "$x^x \log x$"], "corr": "$x^x(1 + \log x)$", "exp": "Using logarithmic differentiation: $y=x^x \Rightarrow \log y = x \log x \Rightarrow (1/y)y' = 1 + \log x$."},

    # (Previous Board/Mains questions remain here...)
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "Define 1 Newton of Force.", "opt": ["1 kg.m/s", "1 kg.m/s²", "1 g.cm/s²", "1 kg.m²/s²"], "corr": "1 kg.m/s²", "exp": "1 Newton = 1kg mass accelerated at 1m/s²."}
]

# Filtering questions
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"⚠️ No questions in {subject} for {level} yet. Please check another Level or Subject!")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    idx = st.session_state.q_idx % len(current_qs)
    q = current_qs[idx]
    
    st.subheader(f"📍 {year} - {subject} ({level})")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Select Answer:", q['opt'], key=f"{year}_{subject}_{level}_{idx}")
    
    if st.button('Submit Answer'):
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        st.session_state.history.append({"Time": datetime.now().strftime("%H:%M"), "Subject": f"{subject}({level})", "Result": res})
        
        if choice == q['corr']:
            st.success("Correct! Advanced Level Cleared! 🎯")
            st.balloons()
        else:
            st.error(f"Incorrect. The correct answer is: {q['corr']}")
        st.markdown(f"**Explanation:** {q['exp']}")

# History Table
st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice History")
if st.session_state.history:
    st.table(pd.DataFrame(st.session_state.history))

st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx = (st.session_state.get('q_idx', 0) + 1)
    st.rerun()
