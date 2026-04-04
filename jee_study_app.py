import streamlit as st
import random

st.set_page_config(page_title="Sai Rakshith JEE Prep", layout="wide")

# 1. సైడ్ బార్ సెటప్ (Exam Center Look)
st.sidebar.title("🏥 JEE EXAM CENTER")
year = st.sidebar.selectbox("Select Year", ["1st Year", "2nd Year"])
subject = st.sidebar.radio("Select Subject", ["Mathematics", "Physics", "Chemistry"])
exam_type = st.sidebar.selectbox("Exam Level", ["JEE Mains", "JEE Advanced"])

st.title(f"🎓 SAI RAKSHITH'S JEE PREP CENTER")
st.markdown(f"### 📍 {year} - {subject} | {exam_type}")

# 2. ప్రశ్నల డేటాబేస్ (1st & 2nd Year అన్ని సబ్జెక్టులు కలిపి)
# రేపు దీన్ని మనం గూగుల్ షీట్ కి కనెక్ట్ చేస్తే వేల ప్రశ్నలు యాడ్ చేయవచ్చు
all_questions = {
    "1st Year": {
        "Mathematics": {"JEE Mains": [{"q": "Value of sin(90)?", "opts": ["0", "1", "-1", "1/2"], "ans": "1", "exp": "sin(90) value is 1 according to trigonometry table."}], "JEE Advanced": [{"q": "Derivative of x^2?", "opts": ["x", "2x", "x^2", "1"], "ans": "2x", "exp": "Using d/dx(x^n) = nx^(n-1), we get 2x."}]},
        "Physics": {"JEE Mains": [{"q": "Unit of Force?", "opts": ["Joule", "Newton", "Watt", "Pascal"], "ans": "Newton", "exp": "Force is measured in Newtons (N)."}], "JEE Advanced": []},
        "Chemistry": {"JEE Mains": [{"q": "Symbol of Gold?", "opts": ["Ag", "Au", "Fe", "Cu"], "ans": "Au", "exp": "Aurum is the Latin name for Gold, so symbol is Au."}], "JEE Advanced": []}
    },
    "2nd Year": {
        "Mathematics": {"JEE Mains": [{"q": "Integration of 1/x dx?", "opts": ["log x", "e^x", "x^2", "1"], "ans": "log x", "exp": "Integration of 1/x is log|x|."}, {"q": "Slope of horizontal line?", "opts": ["0", "1", "Infinite", "-1"], "ans": "0", "exp": "Horizontal lines have zero rise."}], "JEE Advanced": []},
        "Physics": {"JEE Mains": [{"q": "Ideal Ammeter resistance?", "opts": ["Zero", "Low", "High", "Infinite"], "ans": "Zero", "exp": "Ideal ammeter should have no resistance."}], "JEE Advanced": []},
        "Chemistry": {"JEE Mains": [{"q": "PH of pure water?", "opts": ["5", "7", "9", "1"], "ans": "7", "exp": "Pure water is neutral, so PH is 7."}], "JEE Advanced": []}
    }
}

# 3. Session State (మల్టీ-టెస్టర్ లాజిక్)
if 'q_no' not in st.session_state: st.session_state.q_no = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'completed' not in st.session_state: st.session_state.completed = False
if 'current_exam_questions' not in st.session_state: st.session_state.current_exam_questions = []

# సబ్జెక్ట్ లేదా ఇయర్ మారితే కొత్త ఎగ్జామ్ పేపర్ జనరేట్ చేయడం
current_key = f"{year}_{subject}_{exam_type}"
if 'last_key' not in st.session_state or st.session_state.last_key != current_key:
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.completed = False
    st.session_state.last_key = current_key
    # ప్రశ్నలను షఫుల్ (Shuffle) చేసి కొత్త పేపర్ సెట్ చేయడం
    try:
        q_list = all_questions[year][subject][exam_type]
        random.shuffle(q_list)
        st.session_state.current_exam_questions = q_list
    except: st.session_state.current_exam_questions = []

# 4. ఎగ్జామ్ పేపర్ ప్రదర్శన
questions = st.session_state.current_exam_questions

if questions:
    if not st.session_state.completed:
        curr = questions[st.session_state.q_no]
        st.info(f"Question {st.session_state.q_no + 1} of {len(questions)}")
        st.subheader(curr['q'])
        
        user_choice = st.radio("Choose Option:", curr['opts'], key=f"q_{st.session_state.q_no}")

        if st.button("Submit & Next Question ➡️"):
            if user_choice == curr['ans']:
                st.session_state.score += 1
            
            if st.session_state.q_no < len(questions) - 1:
                st.session_state.q_no += 1
                st.rerun()
            else:
                st.session_state.completed = True
                st.rerun()
    else:
        # 5. ఫైనల్ స్కోర్ బోర్డ్
        st.success("🎉 ఎగ్జామ్ పూర్తయింది, సాయి రక్షిత్!")
        st.balloons()
        st.metric("Your Final Score", f"{st.session_state.score} / {len(questions)}")
        
        if st.button("Start New Exam (కొత్త ప్రశ్నలతో మళ్ళీ రాయండి)"):
            st.session_state.q_no = 0
            st.session_state.score = 0
            st.session_state.completed = False
            # మళ్ళీ ప్రశ్నలను మార్చడం
            random.shuffle(questions)
            st.rerun()
else:
    st.warning("ప్రస్తుతం ఈ సెక్షన్ లో ప్రశ్నలు లేవు. త్వరలో యాడ్ చేస్తాము!")

st.divider()
st.caption("Manohar - Variety Motors, Hyderabad")
