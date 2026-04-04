import streamlit as st
from datetime import datetime
import pandas as pd

# App Title with Sai Rakshith's Name
st.set_page_config(page_title="Sai Rakshith's JEE Master", page_icon="🎓", layout="wide")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.write("Target: Board Exams | JEE Mains | JEE Advanced")

# History logic
if 'history' not in st.session_state:
    st.session_state.history = []

# --- Sidebar Configuration ---
st.sidebar.header("📝 Exam Settings")
year = st.sidebar.radio("Select Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])
level = st.sidebar.selectbox("Select Exam Level:", ["Board Level", "JEE Mains", "JEE Advanced"])

# --- Comprehensive Question Bank ---
quiz_data = [
    # 1st Year - Physics
    {"year": "1st Year", "sub": "Physics", "lvl": "Board Level", "q": "What is the SI unit of Work?", "opt": ["Newton", "Joule", "Watt", "Pascal"], "corr": "Joule", "exp": "Work = Force x Displacement. Its SI unit is Joule (J)."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "The dimension of Universal Gravitational Constant (G) is?", "opt": ["[M⁻¹L³T⁻²]", "[ML²T⁻²]", "[M⁻¹L²T⁻¹]", "[MLT⁻²]"], "corr": "[M⁻¹L³T⁻²]", "exp": "Using $F = G m_1 m_2 / r^2$, we find $G = Fr^2 / m_1 m_2$. Substituting dimensions gives $[M^{-1}L^3T^{-2}]$."},
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "A projectile is fired at 45°. What is the ratio of Max Height to Horizontal Range?", "opt": ["1:1", "1:2", "1:4", "2:1"], "corr": "1:4", "exp": "$H = u^2 \sin^2 \theta / 2g$ and $R = u^2 \sin 2\theta / g$. At $45^\circ$, $H/R = \tan(45)/4 = 1/4$."},

    # 1st Year - Chemistry
    {"year": "1st Year", "sub": "Chemistry", "lvl": "Board Level", "q": "Which is the most electronegative element?", "opt": ["Oxygen", "Chlorine", "Fluorine", "Nitrogen"], "corr": "Fluorine", "exp": "Fluorine has the highest electronegativity value (4.0) on the Pauling scale."},
    {"year": "1st Year", "sub": "Chemistry", "lvl": "JEE Mains", "q": "The number of radial nodes in a 3p orbital is?", "opt": ["1", "2", "3", "0"], "corr": "1", "exp": "Radial nodes = $n - l - 1$. For 3p: $n=3, l=1$. So, $3 - 1 - 1 = 1$."},

    # 1st Year - Mathematics
    {"year": "1st Year", "sub": "Mathematics", "lvl": "Board Level", "q": "Value of $\cos(60^\circ)$ is?", "opt": ["1", "1/2", "$\sqrt{3}/2$", "0"], "corr": "1/2", "exp": "Standard trigonometric ratio: $\cos(60) = 0.5$."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Advanced", "q": "If A is a set with 'n' elements, then number of proper subsets is?", "opt": ["2^n", "2^n - 1", "2^n - 2", "n^2"], "corr": "2^n - 1", "exp": "Total subsets = $2^n$. Proper subsets exclude the set itself, so $2^n - 1$."},

    # 2nd Year - Physics
    {"year": "2nd Year", "sub": "Physics", "lvl": "Board Level", "q": "Ohm's Law is valid only for?", "opt": ["Semiconductors", "Insulators", "Metallic Conductors", "Diodes"], "corr": "Metallic Conductors", "exp": "$V = IR$ applies to ohmic conductors, primarily metals at constant temperature."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Advanced", "q": "The core of a transformer is laminated to reduce?", "opt": ["Copper loss", "Hysteresis loss", "Eddy current loss", "Magnetic leakage"], "corr": "Eddy current loss", "exp": "Lamination breaks the path of circulating eddy currents, reducing heat loss."},

    # 2nd Year - Mathematics
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Derivative of $\log(\sin x)$ is?", "opt": ["$\tan x$", "$\cot x$", "$\sec x$", "$\sin x$"], "corr": "$\cot x$", "exp": "Using chain rule: $d/dx(\log u) = (1/u) du/dx$. So $(1/\sin x) \cdot \cos x = \cot x$."}
]

# Filtering Logic
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"⚠️ No questions available for {year} {subject} at {level} level. Please try another combination!")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    idx = st.session_state.q_idx % len(current_qs)
    q = current_qs[idx]
    
    st.subheader(f"📍 {year} - {subject} | {level}")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Select your option:", q['opt'], key=f"q_{year}_{subject}_{level}_{idx}")
    
    if st.button('Submit Answer & Record Progress'):
        now = datetime.now().strftime("%d-%m %H:%M")
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        
        st.session_state.history.append({
            "Time": now,
            "Subject": f"{subject}({level})",
            "Result": res,
            "Target": q['corr']
        })
        
        if choice == q['corr']:
            st.success("Correct! Excellent Work, Sai Rakshith! 🎯")
            st.balloons()
        else:
            st.error(f"Incorrect. The correct answer is: {q['corr']}")
        
        st.markdown(f"### 💡 Deep Explanation:")
        st.write(q['exp'])

# --- Navigation & History Table ---
st.write("---")
if st.button('Next Question ➡️'):
    st.session_state.q_idx += 1
    st.rerun()

st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice Log")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.table(df)
else:
    st.write("No practice history yet. Start your journey!")
