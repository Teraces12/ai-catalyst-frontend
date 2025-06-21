import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from langdetect import detect
from deep_translator import GoogleTranslator
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()
ACCESS_CODE = os.getenv("STREAMLIT_APP_PASSWORD")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Session config
SESSION_TIMEOUT = 15 * 60  # 15 minutes

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.login_time = None

# Auto logout after session timeout
if st.session_state.authenticated:
    time_elapsed = time.time() - st.session_state.login_time
    if time_elapsed > SESSION_TIMEOUT:
        st.session_state.authenticated = False
        st.warning("⏳ Session expired after 15 minutes. Please log in again.")
        st.experimental_rerun()

# Login Gate
if not st.session_state.authenticated:
    st.set_page_config(page_title="Secure Access", layout="centered")
    st.title("🔐 Secure Access Required")
    user_code = st.text_input("Enter access code:", type="password")
    if st.button("Submit"):
        if user_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.session_state.login_time = time.time()
            st.success("✅ Access granted")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid access code")
    st.stop()

# --- MAIN UI ---
st.set_page_config(page_title="AI Catalyst PDF Assistant", page_icon="🧠", layout="centered")
st.sidebar.success("✅ You are logged in")

# Logout Button
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.login_time = None
    st.experimental_rerun()

# --- App Tabs ---
tabs = st.tabs(["📄 PDF Assistant", "🌐 Translate PDF"])

# --- TAB 1: PDF Assistant ---
with tabs[0]:
    st.title("🧠 AI Catalyst PDF Assistant")
    st.subheader("Summarize or ask questions from your PDF using LangChain + OpenAI")

    uploaded_file = st.file_uploader("📄 Upload a PDF", type=["pdf"])
    mode = st.radio("🔍 Choose an action:", ["Summarize", "Ask a question"])

    model_name = st.selectbox("🤖 Select model:", ["gpt-3.5-turbo-16k", "gpt-4"])
    temperature = st.slider("🎨 Creativity level:", 0.0, 1.0, 0.0, step=0.1)
    allow_non_english = st.checkbox("🌐 Allow non-English PDFs", value=False)

    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input("Start Page", min_value=1, value=1)
    with col2:
        end_page = st.number_input("End Page", min_value=start_page, value=start_page + 4)

    question = ""
    if mode == "Ask a question":
        question = st.text_input("❓ Your question:", placeholder="e.g. What is the core mission of this document?")

    if uploaded_file and (mode == "Summarize" or (mode == "Ask a question" and question)):
        with st.spinner("⚙️ Processing..."):
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

                response = requests.post(f"{BACKEND_URL}{endpoint}", files=files, data=data)
                response.raise_for_status()
                result = response.json()

                answer = result.get("answer")
                language = result.get("language", "unknown")
                citations = result.get("citations", [])

                if answer:
                    st.success(answer)
                    st.info(f"🌍 Detected Language: {language}")
                    if citations:
                        st.caption(f"📚 Citations: {', '.join(citations)}")
                else:
                    st.error("⚠️ Unexpected response format.")

            except requests.exceptions.RequestException as e:
                st.error(f"🚫 Request failed: {e}")
            except Exception as e:
                st.error(f"🔥 Internal error: {e}")

# --- TAB 2: Translate PDF ---
with tabs[1]:
    st.title("🌐 PDF Translator")
    uploaded_file = st.file_uploader("📄 Upload a PDF for Translation", type=["pdf"], key="translator")

    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input("Start Page", min_value=1, value=1, key="trans_start")
    with col2:
        end_page = st.number_input("End Page", min_value=start_page, value=start_page + 2, key="trans_end")

    target_lang = st.selectbox("🌍 Translate to:", ["en", "fr", "es", "de", "pt", "zh", "ar", "sw", "hi"], index=0)

    if uploaded_file:
        with st.spinner("🔄 Translating PDF text..."):
            def extract_pdf_text(uploaded_file, start_page, end_page):
                text = ""
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                for page_num in range(start_page - 1, end_page):
                    if page_num < len(doc):
                        text += doc[page_num].get_text()
                return text

            original_text = extract_pdf_text(uploaded_file, start_page, end_page)
            translated_text = GoogleTranslator(source="auto", target=target_lang).translate(original_text)

        st.markdown("### 📝 Side-by-Side Translation")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original Text**")
            st.text_area("", original_text, height=400)
        with col2:
            st.markdown(f"**Translated Text ({target_lang.upper()})**")
            st.text_area("", translated_text, height=400)
