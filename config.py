import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# API Authentication
API_KEY = os.getenv("API_KEY", "mk_default_key_for_testing")

# File upload configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.webp'}

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
