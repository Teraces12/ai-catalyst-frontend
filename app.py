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

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
mode = st.radio("What do you want to do?", ["Summarize", "Ask a question"])

model_name = st.selectbox("Select model:", ["gpt-3.5-turbo-16k", "gpt-4"])
temperature = st.slider("Temperature (creativity):", 0.0, 1.0, 0.0, step=0.1)
allow_non_english = st.checkbox("Allow non-English PDFs", value=False)

# Page range
start_page = st.number_input("Start Page", min_value=1, value=1)
end_page = st.number_input("End Page", min_value=start_page, value=start_page + 4)

# Question field
question = ""
if mode == "Ask a question":
    question = st.text_input("Enter your question:", placeholder="e.g. What is the core mission of this document?")

if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
    with st.spinner("Processing..."):
        progress = st.progress(0)
        try:
            endpoint = "/summarize" if mode == "Summarize" else "/ask"
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {
                "model_name": model_name,
                "temperature": temperature,
                "allow_non_english": str(allow_non_english).lower(),
                "start_page": start_page,
                "end_page": end_page
            }
            if mode == "Ask a question":
                data["question"] = question

            response = requests.post(f"{backend_url}{endpoint}", files=files, data=data)
            response.raise_for_status()

            result = response.json()
            answer = result.get("answer")
            citations = result.get("citations", [])
            lang = result.get("language", "unknown")

            if answer:
                st.success(answer)
                st.info(f"Detected Language: {lang}")
                if citations:
                    st.caption("📚 Citations from: " + ", ".join(citations))
            else:
                st.error("Unexpected response format.")

        except requests.exceptions.HTTPError as http_err:
            try:
                st.error(f"Error: {response.json().get('error', str(http_err))}")
            except:
                st.error(f"HTTP error: {http_err}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            progress.progress(100)
