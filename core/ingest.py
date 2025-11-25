import json
import os
from core.config import MOCK_INBOX_PATH

def load_mock_inbox():
    """Load emails from data/mock_inbox.json"""
    if not os.path.exists(MOCK_INBOX_PATH):
        return []
    try:
        with open(MOCK_INBOX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
