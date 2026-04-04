import streamlit as st
from datetime import datetime
import pandas as pd

# App Title with Babu's Name
st.set_page_config(page_title="Sai Rakshith's JEE Academy", page_icon="🎓")
st.title("🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.write("Welcome back, Sai Rakshith! Let's master JEE Mains & Advanced.")

# History initialization
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.header("Study Settings")
year = st.sidebar.radio("Year:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject:", ["Physics", "Chemistry", "Mathematics"])
# Level ni simple ga ఉంచాను confusion లేకుండా
level = st.sidebar.selectbox("Exam Level:", ["JEE Mains", "JEE Advanced", "Board Level"])

# --- Combined Question Bank ---
quiz_data = [
    {"year": "1st Year", "sub": "Physics", "lvl": "JEE Mains", "q": "What is the SI unit of Force?", "opt": ["Joule", "Newton", "Watt", "Pascal"], "corr": "Newton", "exp": "Force $F = ma$. The SI unit is Newton (N)."},
    {"year": "1st Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Value of sin(30°)?", "opt": ["0", "1/2", "1", "√3/2"], "corr": "1/2", "exp": "Standard trigonometric value: sin(30) = 0.5."},
    {"year": "2nd Year", "sub": "Physics", "lvl": "JEE Mains", "q": "Unit of Electric Current?", "opt": ["Volt", "Ohm", "Ampere", "Tesla"], "corr": "Ampere", "exp": "Current is the flow of charge, measured in Amperes (A)."},
    {"year": "2nd Year", "sub": "Chemistry", "lvl": "JEE Advanced", "q": "Formula of Benzene?", "opt": ["C6H12", "C6H6", "C2H2", "CH4"], "corr": "C6H6", "exp": "Benzene is a stable aromatic ring with formula C6H6."},
    {"year": "2nd Year", "sub": "Mathematics", "lvl": "JEE Mains", "q": "Derivative of x²?", "opt": ["x", "2x", "x³", "1"], "corr": "2x", "exp": "Using power rule: d/dx(x^n) = nx^(n-1). So d/dx(x^2) = 2x."}
]

# Filtering
current_qs = [q for q in quiz_data if q['year'] == year and q['sub'] == subject and q['lvl'] == level]

if not current_qs:
    st.warning(f"Note: No {level} questions found for {subject} yet. Please try another Level or Subject.")
else:
    if 'q_idx' not in st.session_state: st.session_state.q_idx = 0
    q = current_qs[st.session_state.q_idx % len(current_qs)]
    
    st.subheader(f"📍 {year} - {subject} ({level})")
    st.info(f"Question: {q['q']}")
    
    choice = st.radio("Choose Answer:", q['opt'], key=f"{year}_{subject}_{level}")
    
    if st.button('Submit & Save History'):
        now = datetime.now().strftime("%d-%m %H:%M")
        res = "✅ Correct" if choice == q['corr'] else "❌ Wrong"
        
        # Save to history list
        st.session_state.history.append({
            "Time": now,
            "Subject": f"{subject} ({level})",
            "Result": res,
            "Correct Ans": q['corr']
        })
        
        if choice == q['corr']:
            st.success("Excellent, Sai Rakshith! 🎯")
            st.balloons()
        else:
            st.error(f"Try again! Correct answer: {q['corr']}")
        
        st.markdown(f"**Detailed Explanation:** {q['exp']}")

# --- History Section (Visible Always) ---
st.markdown("---")
st.subheader("📊 Sai Rakshith's Practice History")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.table(df) # Table format lo history clear ga కనిపిస్తుంది
else:
    st.write("No history available yet. Start practicing!")

# Navigation
st.write("---")
if st.button('Next Question ➡️'):
    if 'q_idx' in st.session_state: st.session_state.q_idx += 1
    st.rerun()
