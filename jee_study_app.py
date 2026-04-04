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

# --- Expanded Question Bank with Chemistry & Maths ---
quiz_data = [
    # --- 1st Year PHYSICS ---
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "Define 1 Newton of Force.", "opt": ["1 kg.m/s", "1 kg.m/s²", "1 g.cm/s²", "1 kg.m²/s²"], "corr": "1 kg.m/s²", "exp": "1 Newton is the force required to accelerate 1kg mass at 1m/s²."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Work done by a centripetal force is?", "opt": ["Positive", "Negative", "Zero", "Infinite"], "corr": "Zero", "exp": "Since force and displacement are perpendicular, $W = Fd \cos(90) = 0$."},

    # --- 1st Year CHEMISTRY ---
    {"year": "1st Year", "sub": "Chemistry", "lvl": "Board Level", "q": "What is the atomic number of Oxygen?", "opt": ["6", "7", "8", "16"], "corr": "8", "exp": "Oxygen has 8 protons in its nucleus, so its atomic number is 8."},
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Mains", "q": "Which of the following has the smallest size?", "opt": ["Na+", "Mg2+", "Al3+", "F-"], "corr": "Al3+", "exp": "These are isoelectronic species. As positive charge increases, effective nuclear charge increases, making the size smaller."},

    # --- 1st Year MATHEMATICS ---
    {"year": "1st Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Value of cos(0°)?", "opt": ["0", "1", "1/2", "Undefined"], "corr": "1", "exp": "According to the trigonometric table, cos(0) = 1."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "What is the slope of the line $2x + 3y = 6$?", "opt": ["2", "3", "-2/3", "2/3"], "corr": "-2/3", "exp": "For $ax+by=c$, slope $m = -a/b$. Here $m = -2/3$."},

    # --- 2nd Year PHYSICS ---
    {"year": "2nd Year", "sub": "Physics", "lvl": "Board Level", "q": "What is the unit of Power of a Lens?", "opt": ["Meter", "Dioptre", "Watt", "Candela"], "corr": "Dioptre", "exp": "Power of lens $P = 1/f$ is measured in Dioptres (D)."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Resistance of an ideal ammeter is?", "opt": ["High", "Low", "Zero", "Infinite"], "corr": "Zero", "exp": "An ideal ammeter should not affect the current, so its resistance must be zero."},

    # --- 2nd Year CHEMISTRY ---
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "Board Level", "q": "What is the pH of a neutral solution at 25°C?", "opt": ["0", "7", "14", "1"], "corr": "7", "exp": "Neutral solutions like pure water have a pH of 7."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Hybridization of Carbon in Ethyne ($C_2H_2$)?", "opt": ["sp", "sp2", "sp3", "dsp2"], "corr": "sp", "exp": "Ethyne has a triple bond ($C \equiv C$), so each carbon is sp hybridized."},

    # --- 2nd Year MATHEMATICS ---
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "Board Level", "q": "What is the derivative of $\sin(x)$?", "opt": ["$\cos(x)$", "$-\cos(x)$", "$\tan(x)$", "$\sec^2(x)$"], "corr": "$\cos(x)$", "exp": "The basic formula for differentiation of sin(x) is cos(x)."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Integration of $e^x dx$ is?", "opt": ["$e^x + C$", "$x e^x + C$", "$\log(x) + C$", "$1/e^x + C$"], "corr": "$e^x + C$", "exp": "Exponential function $e^x$ remains the same after integration."}
]

# Filtering questions based on sidebar selection
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"⚠️ No {level} questions in {subject} yet. Try switching 'Exam Level' to 'JEE Mains' or check another Subject!")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    # Ensure index is within range
    idx = st.session_state.q_idx % len(current_qs)
    q = current_qs[idx]
    
    st.subheader(f"📍 {year} - {subject} ({level})")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Select your Answer:", q['opt'], key=f"{year}_{subject}_{level}_{idx}")
    
    if st.button('Submit & Save Progress'):
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        st.session_state.history.append({
            "Time": datetime.now().strftime("%H:%M"), 
            "Subject": f"{subject}({level})", 
            "Result": res,
            "Correct Ans": q['corr']
        })
        
        if choice == q['corr']:
            st.success("Great job, Sai Rakshith! Correct Answer. 🎯")
            st.balloons()
        else:
            st.error(f"Keep trying! The correct answer is: {q['corr']}")
        
        st.markdown(f"**Explanation:** {q['exp']}")

# --- History Log (Visible Always) ---
st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice History")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.table(df)
else:
    st.write("No practice history yet. Pick a subject and start!")

# Navigation
st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx = (st.session_state.get('q_idx', 0) + 1)
    st.rerun()
