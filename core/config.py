import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# ------------ API KEYS ------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY in .env")


# ------------ PATHS ------------
# Base directory: root of your project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Auto-create folders
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Data files
MOCK_INBOX_PATH = os.path.join(DATA_DIR, "mock_inbox.json")
PROCESSED_PATH = os.path.join(DATA_DIR, "processed.json")
DRAFTS_PATH = os.path.join(DATA_DIR, "drafts.json")
PROMPTS_PATH = os.path.join(DATA_DIR, "prompts.json")
