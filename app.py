from dotenv import load_dotenv
import os
load_dotenv()
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
