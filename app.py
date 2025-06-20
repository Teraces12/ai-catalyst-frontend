import streamlit as st
import requests
import os
from dotenv import load_dotenv
from streamlit_lottie import st_lottie
from PIL import Image
import json
import time
import logging
from datetime import datetime

# Load environment variables
load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
api_key = os.getenv("API_KEY", "your-secret")  # API Key

# Configure analytics logging
logging.basicConfig(filename="analytics.log", level=logging.INFO)

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
        .tooltip {
            font-size: 12px;
            color: #ccc;
        }
    </style>
""", unsafe_allow_html=True)

# --- Lottie animation loader ---
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

animation = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_p8bfn5to.json")

# --- Logo and Header ---
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.image("Terasystemsai_logo.png", width=180)
st.markdown("""
    <h1 style="color:#FFFFFF;">AI Catalyst PDF Assistant 🧠</h1>
    <h4 style="color:#F8F8F8;">Summarize or ask questions from your PDF using <b>LangChain + OpenAI</b></h4>
</div>
""", unsafe_allow_html=True)

st_lottie(animation, height=150, key="intro")

# --- Upload section ---
uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])

mode = st.radio("🔍 What do you want to do?", ["Summarize", "Ask a question"], horizontal=True)
model_name = st.selectbox("🤖 Select model:", ["gpt-3.5-turbo-16k", "gpt-4"])
temperature = st.slider("🎨 Temperature (creativity):", 0.0, 1.0, 0.0, step=0.1, help="Higher values mean more creative output")
allow_non_english = st.checkbox("🌐 Allow non-English PDFs", help="Enable to analyze PDFs in any language")

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
            start_time = time.time()  # Analytics logging
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

            headers = {"x-api-key": api_key}  # API Key header
            response = requests.post(f"{backend_url}{endpoint}", headers=headers, files=files, data=data)
            response.raise_for_status()
            result = response.json()

            st.success(result.get("answer"))
            st.info(f"🌍 Detected Language: {result.get('language', 'unknown')}")

            if "citations" in result:
                sources = ", ".join(result["citations"])
                st.markdown(f"<p style='font-size: 14px;'>📚 Citations from: {sources}</p>", unsafe_allow_html=True)

            duration = round(time.time() - start_time, 2)
            logging.info(f"{datetime.utcnow()} | Mode: {mode.lower()} | Time: {duration}s")
            st.markdown(f"<p class='tooltip'>📈 Processed in {duration}s</p>", unsafe_allow_html=True)

        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# --- Footer Branding ---
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
st.image("Terasystemsai_logo.png", width=100)
st.markdown("""
    <p style="font-size:14px; color:#eeeeee;">
        <strong>TerasystemsAI</strong> — Empowering Decisions Through Data & AI<br>
        📍 Philadelphia, PA, USA — Serving Globally 🌎<br>
        ✉️ <a style="color:#fff;" href="mailto:admin@terasystems.ai">admin@terasystems.ai</a> | <a style="color:#fff;" href="mailto:lebede@terasystems.ai">lebede@terasystems.ai</a><br>
        🌐 <a style="color:#fff;" href="https://www.terasystems.ai">www.terasystems.ai</a>
    </p>
</div>
""", unsafe_allow_html=True)
