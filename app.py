import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Catalyst PDF Assistant", page_icon="🧠", layout="centered", initial_sidebar_state="collapsed")
st.title("AI Catalyst PDF Assistant 🧠")
st.subheader("Summarize or ask questions from your PDF using LangChain + OpenAI")

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# Choose mode
mode = st.radio("What do you want to do?", ("Summarize", "Ask a question"))

question = ""
if mode == "Ask a question":
    question = st.text_input("Enter your question:", placeholder="e.g. What is the core mission of this document?")

# Submit
if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
    with st.spinner("Processing..."):
        progress = st.progress(0)
        try:
            endpoint = "/summarize" if mode == "Summarize" else "/ask"
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {"question": question} if mode == "Ask a question" else None

            response = requests.post(f"{backend_url}{endpoint}", files=files, data=data)
            progress.progress(100)

            if response.status_code == 200:
                result = response.json()
                st.success("Done!")
                st.markdown("---")
                if mode == "Summarize":
                    st.markdown("### 🌍 Summary")
                    st.write(result.get("summary", "No summary returned."))
                else:
                    st.markdown("### 🧠 Answer")
                    st.write(result.get("answer", "No answer returned."))
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

st.markdown("""
---
🚀 Built with ❤️ by AI Catalyst
""")
