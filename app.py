import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
