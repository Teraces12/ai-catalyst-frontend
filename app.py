from dotenv import load_dotenv
import os
load_dotenv()
backend_url = os.getenv("BACKEND_URL", "https://ai-catalyst.onrender.com")
