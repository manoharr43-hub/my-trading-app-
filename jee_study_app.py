import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="Sai Rakshith JEE Prep", layout="wide")

# --- 1. సబ్జెక్ట్ & ఎగ్జామ్ డేటా (నమూనా) ---
all_questions = {
    "1st Year": {
        "Mathematics": {
            "JEE Mains": [{"q": "Derivative of x^2?", "opts": ["x", "2x", "x^2", "1"], "ans": "2x", "exp": "d/dx(x^n) = nx^(n-1). So, 2x^(2-1) = 2x."}],
            "JEE Advanced": [{"q": "Area under y=x from 0 to 1?", "opts": ["1", "0.5", "2", "1.5"], "ans": "0.5", "exp": "Integral of x is x^2/2. [1^2/2 - 0] = 0.5."}]
        },
        "Physics": {"JEE Mains": [{"q": "Unit of Power?", "opts": ["Watt", "Joule", "Newton", "Volt"], "ans": "Watt", "exp": "Power is Rate of doing work. P = W/t. Unit is Watt."}], "JEE Advanced": []},
        "Chemistry": {"JEE Mains": [{"q": "Atomic number of Carbon?", "opts": ["4", "6", "8", "12"], "ans": "6", "exp": "Carbon is the 6th element in the periodic table."}], "JEE Advanced": []}
    },
    "2nd Year": {
        "Mathematics": {"JEE Mains": [{"q": "Integration of 1/x?", "opts": ["log x", "e^x", "x^2", "1"], "ans": "log x", "exp": "Integral of 1/x dx is log|x| + C."}], "JEE Advanced": []},
        "Physics": {"JEE Mains": [{"q": "Ideal Ammeter resistance?", "opts": ["Zero", "Low", "High", "Infinite"], "ans": "Zero", "exp": "To avoid voltage drop, ideal ammeter must have 0 resistance."}], "JEE Advanced": []},
        "Chemistry": {"JEE Mains": [{"q": "PH of pure water?", "opts": ["5", "7", "9", "1"], "ans": "7", "exp": "Pure water is neutral, so PH is 7."}], "JEE Advanced": []}
    }
}

# --- 2. సెషన్ స్టేట్ (డేటా సేవ్ చేయడానికి) ---
if 'history' not in st.session_state: st.session_state.history = []
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'completed' not in st.session_state: st.session_state.completed = False
if 'show_exp' not in st.session_state: st.session_state.show_exp = False

# --- 3. సైడ్ బార్ (ఫోల్డర్ సిస్టమ్) ---
st.sidebar.title("🏥 JEE EXAM CENTER")
folder = st.sidebar.radio("Go to Folder:", ["📝 Take Exam", "📜 Exam History"])

if folder == "📝 Take Exam":
    year = st.sidebar.selectbox("Year", ["1st Year", "2nd Year"])
    subject = st.sidebar.selectbox("Subject", ["Mathematics", "Physics", "Chemistry"])
    level = st.sidebar.radio("Level", ["JEE Mains", "JEE Advanced"])

    # సబ్జెక్ట్ మారితే రీసెట్
    current_key = f"{year}_{subject}_{level}"
    if 'last_key' not in st.session_state or st.session_state.last_key != current_key:
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.completed = False
        st.session_state.show_exp = False
        st.session_state.last_key = current_key

    st.title(f"✍️ {level} Practice")
    st.write(f"**Target:** {year} - {subject}")

    try:
        questions = all_questions[year][subject][level]
        if not st.session_state.completed:
            curr = questions[st.session_state.q_no]
            st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
            st.subheader(curr['q'])
            
            user_choice = st.radio("Select Answer:", curr['opts'], key=f"q_{st.session_state.q_no}")
            
            if st.button("Submit Answer"):
                st.session_state.show_exp = True
            
            if st.session_state.show_exp:
                if user_choice == curr['ans']:
                    st.success(f"✅ Correct! \n\n **Explanation:** {curr['exp']}")
                else:
                    st.error(f"❌ Wrong! Correct: {curr['ans']} \n\n **Explanation:** {curr['exp']}")
                
                if st.button("Next Question ➡️"):
                    if user_choice == curr['ans']: st.session_state.score += 1
                    if st.session_state.q_no < len(questions) - 1:
                        st.session_state.q_no += 1
                        st.session_state.show_exp = False
                        st.rerun()
                    else:
                        st.session_state.completed = True
                        # హిస్టరీలో సేవ్ చేయడం
                        st.session_state.history.append({
                            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Exam": f"{year}-{subject}-{level}",
                            "Score": f"{st.session_state.score}/{len(questions)}"
                        })
                        st.rerun()
        else:
            st.balloons()
            st.success(f"🎉 Exam Completed! Your Score: {st.session_state.score} / {len(questions)}")
            if st.button("Restart with New Questions"):
                random.shuffle(questions)
                st.session_state.q_no = 0
                st.session_state.score = 0
                st.session_state.completed = False
                st.rerun()
    except:
        st.warning("No questions available here yet.")

# --- 4. ఎగ్జామ్ హిస్టరీ ఫోల్డర్ ---
elif folder == "📜 Exam History":
    st.title("📊 Sai Rakshith's Progress Report")
    if st.session_state.history:
        st.table(st.session_state.history)
    else:
        st.info("ఇంకా ఎటువంటి ఎగ్జామ్స్ రాయలేదు. ఆల్ ది బెస్ట్!")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
