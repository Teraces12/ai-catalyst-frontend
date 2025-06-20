import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config with Adobe Red theme and gradient background
st.set_page_config(
    page_title="AI Catalyst PDF Assistant",
    page_icon="🧠",
    layout="centered"
)

# Adobe red-themed background style
st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, #FF0000, #D00000);
            color: white;
        }
        .stApp {
            background: transparent !important;
        }
        .css-1v3fvcr, .css-ffhzg2 {
            background-color: transparent !important;
        }
        .stTextInput>div>input, .stSelectbox>div>div>div, .stButton>button {
            color: black !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Logo and Header ---
st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://raw.githubusercontent.com/Teraces12/ai-catalyst-frontend/main/assets/terasystem_logo.png" width="180">
        <h1 style="color:#FFFFFF;">AI Catalyst PDF Assistant 🧠</h1>
        <h4 style="color:#F8F8F8;">Summarize or ask questions from your PDF using <b>LangChain + OpenAI</b></h4>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Upload section ---
uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])

mode = st.radio("🔍 What do you want to do?", ["Summarize", "Ask a question"], horizontal=True)
model_name = st.selectbox("🤖 Select model:", ["gpt-3.5-turbo-16k", "gpt-4"])
temperature = st.slider("🎨 Temperature (creativity):", 0.0, 1.0, 0.0, step=0.1)
allow_non_english = st.checkbox("🌐 Allow non-English PDFs")

col1, col2 = st.columns(2)
with col1:
    start_page = st.number_input("Start Page", min_value=1, value=1)
with col2:
    end_page = st.number_input("End Page", min_value=start_page, value=start_page + 4)

question = ""
if mode == "Ask a question":
    question = st.text_input("❓ Enter your question", placeholder="e.g. What is the core mission of this document?")

# --- Request trigger ---
if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
    with st.spinner("🚀 Processing..."):
        try:
            endpoint = "/summarize" if mode == "Summarize" else "/ask"
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {
                "model_name": model_name,
                "temperature": temperature,
                "allow_non_english": str(allow_non_english).lower(),
                "start_page": int(start_page),
                "end_page": int(end_page)
            }
            if mode == "Ask a question":
                data["question"] = question

            response = requests.post(f"{backend_url}{endpoint}", files=files, data=data)
            response.raise_for_status()
            result = response.json()

            st.success(result.get("answer"))
            st.info(f"🌍 Detected Language: {result.get('language', 'unknown')}")

            if "citations" in result:
                sources = ", ".join(result["citations"])
                st.markdown(f"<p style='font-size: 14px;'>📚 Citations from: {sources}</p>", unsafe_allow_html=True)

        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- Footer Branding ---
st.markdown(
    """
    <hr>
    <div style="text-align:center;">
        <img src="https://raw.githubusercontent.com/Teraces12/ai-catalyst-frontend/main/assets/terasystem_logo.png" width="100">
        <p style="font-size:14px; color:#eeeeee;">
            <strong>TerasystemsAI</strong> — Empowering Decisions Through Data & AI<br>
            📍 Philadelphia, PA, USA — Serving Globally 🌎<br>
            ✉️ <a style="color:#fff;" href="mailto:admin@terasystems.ai">admin@terasystems.ai</a> | <a style="color:#fff;" href="mailto:lebede@terasystems.ai">lebede@terasystems.ai</a><br>
            🌐 <a style="color:#fff;" href="https://www.terasystems.ai">www.terasystems.ai</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
