import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv
from langdetect import detect
from deep_translator import GoogleTranslator
import fitz  # PyMuPDF
from io import BytesIO
from fpdf import FPDF
from pdf2docx import Converter
import pypandoc
import openai

# Load environment variables
load_dotenv()
ACCESS_CODE = os.getenv("STREAMLIT_APP_PASSWORD")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

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
tabs = st.tabs(["📄 PDF Assistant", "🌐 Translate PDF", "🔁 Convert Files", "👨‍💻 AI Code & Paper Assistant"])

# --- TAB 1: PDF Assistant ---
with tabs[0]:
    st.title("🧠 AI Catalyst PDF Assistant")
    st.subheader("Summarize or ask questions from your PDF using LangChain + OpenAI")

    uploaded_files = st.file_uploader("📄 Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)
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

    if uploaded_files and (mode == "Summarize" or (mode == "Ask a question" and question)):
        for uploaded_file in uploaded_files:
            st.markdown(f"### 📘 {uploaded_file.name}")
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
    uploaded_files = st.file_uploader("📄 Upload one or more PDFs for Translation", type=["pdf"], accept_multiple_files=True, key="translator")

    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input("Start Page", min_value=1, value=1, key="trans_start")
    with col2:
        end_page = st.number_input("End Page", min_value=start_page, value=start_page + 2, key="trans_end")

    target_lang = st.selectbox("🌍 Translate to:", ["en", "fr", "es", "de", "pt", "zh", "ar", "sw", "hi"], index=0)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.markdown(f"### 📘 {uploaded_file.name}")
            with st.spinner("🔄 Translating PDF text..."):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                original_text = ""
                for page_num in range(start_page - 1, end_page):
                    if page_num < len(doc):
                        original_text += doc[page_num].get_text()
                translated_text = GoogleTranslator(source="auto", target=target_lang).translate(original_text)

            st.markdown("### 📝 Side-by-Side Translation")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original Text**")
                st.text_area("", original_text, height=400)
            with col2:
                st.markdown(f"**Translated Text ({target_lang.upper()})**")
                st.text_area("", translated_text, height=400)

            # Download translated text
            download_txt = BytesIO(translated_text.encode("utf-8"))
            st.download_button("📄 Download Translated Text (.txt)", data=download_txt, file_name="translated_output.txt", mime="text/plain")

            # Download side-by-side PDF
            class PDF(FPDF):
                def header(self):
                    self.set_font("Arial", "B", 12)
                    self.cell(0, 10, "Translated PDF Output", ln=True, align="C")
                def chapter_body(self, original, translated):
                    self.set_font("Arial", "", 10)
                    self.multi_cell(0, 5, f"🔸 Original:\n{original}\n\n🌍 Translated:\n{translated}\n\n")

            pdf = PDF()
            pdf.add_page()
            pdf.chapter_body(original_text, translated_text)

            pdf_buffer = BytesIO()
            pdf.output(pdf_buffer)
            pdf_buffer.seek(0)

            st.download_button("🧾 Download Side-by-Side PDF", data=pdf_buffer, file_name="translated_side_by_side.pdf", mime="application/pdf")

# --- TAB 3: Convert Files ---
with tabs[2]:
    st.title("🔁 PDF ↔ Word Converter")
    conversion_mode = st.radio("📤 File Conversion", ["None", "PDF ➡️ Word", "Word ➡️ PDF"])
    conversion_file = st.file_uploader("📄 Upload file to convert", type=["pdf", "docx"], key="convert")

    if conversion_file and conversion_mode != "None":
        output_path = "converted_output"
        if conversion_mode == "PDF ➡️ Word":
            output_path += ".docx"
            with open("temp_input.pdf", "wb") as f:
                f.write(conversion_file.read())
            cv = Converter("temp_input.pdf")
            cv.convert(output_path, start=0, end=None)
            cv.close()
        else:
            output_path += ".pdf"
            with open("temp_input.docx", "wb") as f:
                f.write(conversion_file.read())
            pypandoc.convert_file("temp_input.docx", 'pdf', outputfile=output_path)

        with open(output_path, "rb") as f:
            st.download_button("📥 Download Converted File", f, file_name=output_path)

# --- TAB 4: AI Code & Paper Assistant ---
with tabs[3]:
    st.title("👨‍💻 AI Code & Paper Assistant")
    task_type = st.selectbox("Select Task:", ["Generate Python Script", "Write Research Paper Section", "Start New Paper"])
    user_prompt = st.text_area("🧠 Describe what you want to generate:", height=200)

    if st.button("🚀 Generate") and user_prompt:
        with st.spinner("Generating with GPT..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"You are an expert {task_type.lower()}. Output clean, complete content."},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                generated_output = response.choices[0].message.content
                st.success("✅ Generation complete")
                st.code(generated_output if task_type == "Generate Python Script" else "\n" + generated_output)

                download_data = BytesIO(generated_output.encode("utf-8"))
                file_ext = ".py" if task_type == "Generate Python Script" else ".txt"
                st.download_button("📥 Download Output", data=download_data, file_name=f"generated{file_ext}", mime="text/plain")

            except Exception as e:
                st.error(f"❌ Failed to generate: {e}")
