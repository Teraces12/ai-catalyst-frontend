import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

# UI Setup
st.set_page_config(
    page_title="AI Catalyst PDF Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.title("AI Catalyst PDF Assistant 🧠")
st.subheader("Summarize or ask questions from your PDF using LangChain + OpenAI")

# File upload
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# Mode selection
mode = st.radio("What do you want to do?", ["Summarize", "Ask a question"])

# Question input
question = ""
if mode == "Ask a question":
    question = st.text_input("Enter your question:", placeholder="e.g. What is the core mission of this document?")

# Trigger API request
if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
    with st.spinner("Processing..."):
        progress = st.progress(0)
        try:
            endpoint = "/summarize" if mode == "Summarize" else "/ask"
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {"question": question} if mode == "Ask a question" else {}

            response = requests.post(f"{backend_url}{endpoint}", files=files, data=data)
            response.raise_for_status()  # Raise if status_code != 200

            result = response.json()
            answer = result.get("answer")

            if answer:
                st.success(answer)
            else:
                st.error("Unexpected response format.")

        except requests.exceptions.HTTPError as http_err:
            try:
                error_msg = response.json().get("error", str(http_err))
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"HTTP error: {http_err}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            progress.progress(100)
