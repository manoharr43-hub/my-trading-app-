import streamlit as st

# =============================
# 1️⃣ 40 JEE Questions Sample (Telugu + English) with step-by-step explanation
# =============================
# For brevity, here only 10 questions shown; you can extend to 40 easily
questions = [
    {
        "question": "Mathematics: Solve for x: 2x + 3 = 7",
        "options": ["1", "2", "3", "4"],
        "answer": "2",
        "explanation": "Step-by-Step:\n1. 2x + 3 = 7\n2. 2x = 4\n3. x = 2"
    },
    {
        "question": "Physics: Time to fall 20 m freely under gravity?",
        "options": ["2 s", "4 s", "3 s", "5 s"],
        "answer": "2 s",
        "explanation": "Step-by-Step:\ns = 0.5*g*t^2\n20 = 0.5*10*t^2\n20 = 5*t^2\nt^2=4 => t=2 s"
    },
    {
        "question": "Chemistry: Molecular formula of water?",
        "options": ["H2O", "H2O2", "HO", "O2H2"],
        "answer": "H2O",
        "explanation": "Step-by-Step:\nWater has 2 H + 1 O → H2O"
    },
    {
        "question": "Mathematics: Value of 3^2 + 4^2?",
        "options": ["25", "12", "7", "10"],
        "answer": "25",
        "explanation": "Step-by-Step:\n3^2 + 4^2 = 9 + 16 = 25"
    },
    {
        "question": "Physics: Speed formula?",
        "options": ["s = d/t", "v = t/d", "v = s*t", "v = d^2/t"],
        "answer": "s = d/t",
        "explanation": "Step-by-Step:\nSpeed = distance / time"
    },
    {
        "question": "Chemistry: Atomic number of Oxygen?",
        "options": ["8", "16", "12", "6"],
        "answer": "8",
        "explanation": "Step-by-Step:\nOxygen has 8 protons → atomic number = 8"
    },
    {
        "question": "Mathematics: Solve x^2 =
