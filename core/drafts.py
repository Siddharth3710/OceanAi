import json
import os
from typing import List, Dict, Any
from core.config import DATA_DIR

DRAFTS_PATH = os.path.join(DATA_DIR, "drafts.json")


def load_drafts() -> List[Dict[str, Any]]:
    if not os.path.exists(DRAFTS_PATH):
        return []
    try:
        with open(DRAFTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_drafts(drafts: List[Dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)
