import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime

# =============================
# 1️⃣ Gemini AI Setup
# =============================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY")  # safe method
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# =============================
# 2️⃣ Load old questions
# =============================
QUESTIONS_FILE = 'jee_mains_questions.json'
try:
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            old_questions = json.load(f)
    else:
        old_questions = []
except json.JSONDecodeError:
    old_questions = []

# =============================
# 3️⃣ Generate New Questions
# =============================
def generate_new_questions(subject, count=5):
    prompt = f"""
    Act as a JEE Mains Expert.
    Generate {count} HIGH-QUALITY MCQs strictly for {subject}.
    Each question must have:
    - question
    - options ["A","B","C","D"]
    - answer
    - explanation (step-by-step solution)
    Return ONLY raw JSON list.
    """
    try:
        response = model.generate_text(prompt=
