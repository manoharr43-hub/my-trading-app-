import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Babu's JEE Master", page_icon="🎓")
st.title("🎓 BABU'S JEE QUIZ & DEEP LEARNING")

# --- History Tracking ---
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
st.sidebar.header("Settings")
year = st.sidebar.radio("Year Selection:", ["1st Year", "2nd Year"])
subject = st.sidebar.selectbox("Subject Selection:", ["Physics", "Chemistry", "Mathematics"])

# --- Detailed Question Bank ---
quiz_data = {
    "1st Year": {
        "Physics": [
            {
                "q": "What is the unit of Force?", 
                "options": ["Joule", "Newton", "Watt", "Pascal"], 
                "correct": "Newton",
                "exp": """
                **లోతైన వివరణ (Deep Explanation):**
                * **ఫార్ములా:** Force (బలం) = mass (ద్రవ్యరాశి) × acceleration (త్వరణం) [$F = m \times a$].
                * **వివరణ:** ఐజాక్ న్యూటన్ గౌరవార్థం ఈ యూనిట్‌కు 'న్యూటన్' అని పేరు పెట్టారు. 
                * **ఇతర ఆప్షన్లు ఎందుకు కావు?:** - Joule అనేది Energy (శక్తి) కి యూనిట్. 
                    - Watt అనేది Power (సామర్థ్యం) కి యూనిట్. 
                    - Pascal అనేది Pressure (పీడనం) కి యూనిట్.
                """
            },
            {
                "q": "What is the unit of Energy?", 
                "options": ["Newton", "Joule", "Watt", "Hertz"], 
                "correct": "Joule",
                "exp": """
                **లోతైన వివరణ (Deep Explanation):**
                * **వివరణ:** పని చేయడానికి అవసరమైన సామర్థ్యాన్ని శక్తి (Energy) అంటారు. దీని SI యూనిట్ 'జౌల్' (Joule).
                * **ముఖ్యమైన విషయం:** Work (పని) మరియు Energy రెండింటికీ ఒకే యూనిట్ ఉంటుంది.
                """
            }
        ],
        "Chemistry": [
            {
                "q": "What is the atomic mass of Carbon?", 
                "options": ["6", "12", "14", "16"], 
                "correct": "12",
                "exp": """
                **లోతైన వివరణ (Deep Explanation):**
                * **వివరణ:** కార్బన్ పరమాణువులో 6 ప్రోటాన్లు మరియు 6 న్యూట్రాన్లు ఉంటాయి. 
                * **లెక్క:** Atomic Mass = Protons + Neutrons ($6 + 6 = 12$).
                * **గమనిక:** 6 అనేది కార్బన్ యొక్క Atomic Number (పరమాణు సంఖ్య).
                """
            }
        ]
    }
}

if 'q_no' not in st.session_state:
    st.session_state.q_no = 0

current_list = quiz_data.get(year, {}).get(subject, [{"q": "No questions!", "options": ["N/A"], "correct": "N/A", "exp": "N/A"}])

# Question Display
st.subheader(f"📍 {year} - {subject}")
q_item = current_list[st.session_state.q_no % len(current_list)]

st.info(f"ప్రశ్న: {q_item['q']}")
user_choice = st.radio("సరైన ఆప్షన్ ఎంచుకోండి:", q_item['options'], key=f"deep_{st.session_state.q_no}")

if st.button('Submit Answer & Save'):
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    is_correct = user_choice == q_item['correct']
    status = "✅ Correct" if is_correct else "❌ Wrong"
    
    # Save to History
    st.session_state.history.append({
        "Date": now,
        "Subject": subject,
        "Result": status,
        "Question": q_item['q'],
        "Your Answer": user_choice,
        "Correct Answer": q_item['correct']
    })
    
    if is_correct:
        st.success("అద్భుతం బాబు! నువ్వు చెప్పింది సరైన సమాధానం. 👏")
        st.balloons()
    else:
        st.error(f"తప్పు బాబు! సరైన సమాధానం: {q_item['correct']}")
    
    # Deep Explanation Box
    st.markdown("---")
    st.markdown(f"### 💡 వివరణ (Explanation):")
    st.write(q_item['exp'])

# --- History Table ---
st.write("---")
st.subheader("📊 బాబు ప్రాక్టీస్ హిస్టరీ (History Log)")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True) # మొబైల్ లో కూడా నీట్ గా కనిపిస్తుంది
else:
    st.write("ఇంకా చదువు మొదలుపెట్టలేదు. ఆల్ ది బెస్ట్!")

# Navigation
col1, col2 = st.columns(2)
with col1:
    if st.button('⬅️ Previous'):
        st.session_state.q_no -= 1
        st.rerun()
with col2:
    if st.button('Next ➡️'):
        st.session_state.q_no += 1
        st.rerun()
