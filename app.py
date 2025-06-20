import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Catalyst PDF Assistant", page_icon="🧠", layout="centered", initial_sidebar_state="collapsed")
st.title("AI Catalyst PDF Assistant 🧠")
st.subheader("Summarize or ask questions from your PDF using LangChain + OpenAI")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
mode = st.radio("What do you want to do?", ("Summarize", "Ask a question"))

question = ""
if mode == "Ask a question":
    question = st.text_input("Enter your question:", placeholder="e.g. What is the core mission of this document?")

if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
    with st.spinner("Processing..."):
        progress = st.progress(0)
        try:
            endpoint = "/summarize" if mode == "Summarize" else "/ask"
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {"question": question} if mode == "Ask a question" else None

            response = requests.post(f"{backend_url}{endpoint}", files=files, data=data)
            result = response.json()

            if "summary" in result:
                st.success(result["summary"])
            elif "answer" in result:
                st.success(result["answer"])
            else:
                st.error("Unexpected response format.")
        except Exception as e:
            st.error(f"Error: {e}")
        progress.progress(100)
