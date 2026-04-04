import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Sai Rakshith's JEE Master", page_icon="🎓", layout="wide")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar settings
st.sidebar.header("📝 Exam Settings")
year = st.sidebar.radio("Select Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.selectbox("Select Exam Level:", ["Board Level", "JEE Mains", "JEE Advanced"])

# --- Comprehensive Database (All 18 Combinations Covered) ---
quiz_data = [
    # 1st Year Physics
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "What is the unit of Force?", "opt": ["Joule", "Newton", "Watt", "Pascal"], "corr": "Newton", "exp": "Force = mass x acceleration. Unit is Newton (N)."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Dimensions of G?", "opt": ["[M-1L3T-2]", "[ML2T-2]", "[M-1L2T-1]", "[MLT-2]"], "corr": "[M-1L3T-2]", "exp": "Calculated from F = Gm1m2/r²."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "Error in volume if radius error is 2%?", "opt": ["2%", "4%", "6%", "8%"], "corr": "6%", "exp": "V = 4/3 pi r^3. Error = 3 * 2% = 6%."},
    
    # 1st Year Chemistry
    {"year": "1st Year", "sub": "Chemistry", "lvl": "Board Level", "q": "Atomic number of Oxygen?", "opt": ["6", "7", "8", "16"], "corr": "8", "exp": "Oxygen has 8 protons."},
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Mains", "q": "Radial nodes in 3p?", "opt": ["1", "2", "3", "0"], "corr": "1", "exp": "Nodes = n - l - 1 = 3 - 1 - 1 = 1."},
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Intensive property example?", "opt": ["Mass", "Volume", "Density", "Heat capacity"], "corr": "Density", "exp": "Density doesn't depend on amount."},
    
    # 1st Year Mathematics (Ensuring all levels work)
    {"year": "1st Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Value of cos(60°)?", "opt": ["0", "1/2", "1", "sqrt(3)/2"], "corr": "1/2", "exp": "Standard trig value: cos(60) = 0.5."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Subsets of set with 'n' elements?", "opt": ["2n", "n^2", "2^n", "n!"], "corr": "2^n", "exp": "Formula for total subsets is 2^n."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "Proper subsets for 'n' elements?", "opt": ["2^n", "2^n - 1", "2^n - 2", "n!"], "corr": "2^n - 1", "exp": "Excludes the set itself."},

    # 2nd Year Physics
    {"year": "2nd Year", "sub": "Physics", "lvl": "Board Level", "q": "Ohm's Law formula?", "opt": ["V=I/R", "V=IR", "V=I+R", "V=R/I"], "corr": "V=IR", "exp": "V = IR is the standard Ohm's law."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Ideal Ammeter resistance?", "opt": ["Zero", "Low", "High", "Infinite"], "corr": "Zero", "exp": "Ideal ammeter has no resistance."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "Lenz's Law follows conservation of?", "opt": ["Mass", "Charge", "Energy", "Momentum"], "corr": "Energy", "exp": "Lenz's law is energy conservation."},

    # 2nd Year Chemistry
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "Board Level", "q": "pH of neutral water?", "opt": ["0", "7", "14", "1"], "corr": "7", "exp": "Neutral pH is 7."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Mains", "q": "Shape of PCl5?", "opt": ["Square", "Tetrahedral", "Trigonal Bipyramidal", "Octahedral"], "corr": "Trigonal Bipyramidal", "exp": "PCl5 is sp3d hybridized."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "XeF4 hybridization?", "opt": ["sp3", "sp3d", "sp3d2", "dsp2"], "corr": "sp3d2", "exp": "XeF4 has 4 bond pairs and 2 lone pairs."},

    # 2nd Year Mathematics
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Derivative of sin(x)?", "opt": ["cos(x)", "-cos(x)", "tan(x)", "sin(x)"], "corr": "cos(x)", "exp": "d/dx(sin x) = cos x."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Integral of 1/x dx?", "opt": ["x", "log|x|", "e^x", "1"], "corr": "log|x|", "exp": "Standard integral of 1/x is log|x|."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "Derivative of x^x?", "opt": ["x^x(1+log x)", "x.x^x-1", "1+log x", "log x"], "corr": "x^x(1+log x)", "exp": "Using log differentiation: y=x^x => y'=x^x(1+log x)."}
]

# Filtering with safety check
filtered_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not filtered_qs:
    st.warning(f"⚠️ Something went wrong. Showing default question for {year} {subject}.")
    q = [q for q in quiz_data if q['year'] == year and q['sub'] == subject][0]
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    q = filtered_qs[st.session_state.q_idx % len(filtered_qs)]

# Question Display
st.subheader(f"📍 {year} - {subject} | {level}")
st.info(f"Question: {q['q']}")
choice = st.radio("Choose Option:", q['opt'], key=f"q_{year}_{subject}_{level}_{st.session_state.get('q_idx', 0)}")

if st.button('Submit Answer'):
    res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
    st.session_state.history.append({"Time": datetime.now().strftime("%H:%M"), "Subject": f"{subject}({level})", "Result": res})
    if choice == q['corr']:
        st.success("Correct! Well done Sai Rakshith!")
        st.balloons()
    else:
        st.error(f"Incorrect. Answer: {q['corr']}")
    st.markdown(f"**Explanation:** {q['exp']}")

st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx = st.session_state.get('q_idx', 0) + 1
    st.rerun()

st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice Log")
if st.session_state.history:
    st.table(pd.DataFrame(st.session_state.history))
