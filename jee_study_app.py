import streamlit as st
import random

st.set_page_config(page_title="Sai Rakshith JEE Prep", layout="wide")

# 1. సైడ్ బార్ సెటప్
st.sidebar.title("🎓 JEE LEARNING HUB")
year = st.sidebar.selectbox("Select Year", ["1st Year", "2nd Year"])
subject = st.sidebar.radio("Select Subject", ["Mathematics", "Physics", "Chemistry"])
exam_type = st.sidebar.selectbox("Exam Level", ["JEE Mains", "JEE Advanced"])

st.title(f"🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown(f"### 📍 {year} - {subject} | {exam_type}")

# 2. భారీ ప్రశ్నల డేటాబేస్ (నమూనా కోసం కొన్ని)
# మనం రేపు గూగుల్ షీట్ కనెక్ట్ చేస్తే ఇవి ఆటోమేటిక్ గా వస్తాయి
all_questions = {
    "2nd Year": {
        "Mathematics": {
            "JEE Mains": [
                {"q": "Integration of 1/x dx?", "opts": ["log x", "e^x", "x^2", "1"], "ans": "log x", "exp": "Integration of 1/x is always log|x| + C."},
                {"q": "Slope of a horizontal line?", "opts": ["0", "1", "Infinite", "-1"], "ans": "0", "exp": "Horizontal lines have no rise, so slope is 0."}
            ],
            "JEE Advanced": [
                {"q": "Value of i^2?", "opts": ["1", "-1", "i", "0"], "ans": "-1", "exp": "By definition of complex numbers, i = sqrt(-1), so i^2 = -1."}
            ]
        },
        "Physics": {
            "JEE Mains": [
                {"q": "Ideal Ammeter resistance?", "opts": ["Zero", "Low", "High", "Infinite"], "ans": "Zero", "exp": "To measure current without drop, resistance must be zero."}
            ]
        }
    }
}

# 3. Session State సెటప్
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'completed' not in st.session_state: st.session_state.completed = False
if 'show_exp' not in st.session_state: st.session_state.show_exp = False

# సబ్జెక్ట్ మారితే రీసెట్
current_key = f"{year}_{subject}_{exam_type}"
if 'last_key' not in st.session_state or st.session_state.last_key != current_key:
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.show_exp = False
    st.session_state.last_key = current_key

# 4. ఎగ్జామ్ ఇంజిన్
try:
    questions = all_questions[year][subject][exam_type]
    
    if not st.session_state.completed:
        curr = questions[st.session_state.q_no]
        st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
        st.subheader(curr['q'])
        
        user_choice = st.radio("Choose Option:", curr['opts'], key=f"opt_{st.session_state.q_no}")

        if st.button("Check Answer & Explanation"):
            st.session_state.show_exp = True
        
        if st.session_state.show_exp:
            if user_choice == curr['ans']:
                st.success(f"✅ Correct! Explanation: {curr['exp']}")
            else:
                st.error(f"❌ Wrong! Correct Answer: {curr['ans']}. Explanation: {curr['exp']}")

            if st.button("Next Question ➡️"):
                if user_choice == curr['ans']:
                    st.session_state.score += 1
                
                if st.session_state.q_no < len(questions) - 1:
                    st.session_state.q_no += 1
                    st.session_state.show_exp = False
                    st.rerun()
                else:
                    st.session_state.completed = True
                    st.rerun()
    else:
        # 5. ఫైనల్ రిజల్ట్ బోర్డు
        st.success("🎉 ఎగ్జామ్ పూర్తయింది!")
        st.balloons()
        st.metric("Total Marks", f"{st.session_state.score} / {len(questions)}")
        
        if st.button("కొత్త ప్రశ్నలతో మళ్ళీ రాయండి (New Exam)"):
            # ఇక్కడ మనం ప్రశ్నలను షఫుల్ (Shuffle) చేయవచ్చు
            random.shuffle(questions) 
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.completed = False
            st.rerun()

except KeyError:
    st.warning("ఈ సెక్షన్ లో ఇంకా ప్రశ్నలు యాడ్ చేయలేదు. త్వరలో వస్తాయి!")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
