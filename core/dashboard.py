from typing import List, Dict, Any, Tuple
from collections import Counter
import pandas as pd

from core.processing import load_processed

# Very simple stopword list so keyword chart looks cleaner
STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "this", "that",
    "are", "our", "has", "have", "will", "from", "all", "but",
    "can", "was", "were", "they", "their", "them", "about",
    "please", "kindly", "hello", "hi", "thanks", "thank",
    "team", "dear", "regards", "best", "here", "link", "click",
    "http", "https", "com", "subject", "body"
}


def _count_actions(actions: Any) -> int:
    """Count number of tasks in the extracted actions structure."""
    if actions is None:
        return 0

    # If LLM followed the expected JSON format:
    # { "tasks": [ { "task": "...", "deadline": "..." }, ... ] }
    if isinstance(actions, dict) and isinstance(actions.get("tasks"), list):
        return len(actions["tasks"])

    # If it's a bare list of tasks
    if isinstance(actions, list):
        return len(actions)

    # Otherwise treat as unstructured
    return 0


def _compute_priority_row(row: pd.Series) -> Tuple[int, str]:
    """
    Simple rule-based priority scoring:
    - Category Important / To-Do
    - Urgent / deadline / meeting keywords
    - Number of actions
    """
    score = 0
    category = str(row.get("category") or "").lower()
    text = f"{row.get('subject', '')} {row.get('body', '')}".lower()

    # Category-based
    if "important" in category:
        score += 3
    if "to-do" in category or "todo" in category:
        score += 3
    if "spam" in category or "newsletter" in category:
        score -= 1  # slightly lower

    urgent_keywords = ["urgent", "asap", "immediately", "critical", "high priority"]
    deadline_keywords = ["deadline", "by ", "before ", "due ", "last date", "submit"]
    meeting_keywords = ["meeting", "call", "discussion", "review", "planning"]

    if any(k in text for k in urgent_keywords):
        score += 3
    if any(k in text for k in deadline_keywords):
        score += 2
    if any(k in text for k in meeting_keywords):
        score += 1

    num_actions = row.get("num_actions", 0)
    if isinstance(num_actions, (int, float)) and num_actions > 0:
        score += min(3, int(num_actions))

    if score >= 7:
        label = "HIGH"
    elif score >= 4:
        label = "MEDIUM"
    else:
        label = "LOW"

    return score, label


def prepare_email_dataframe(processed: List[Dict[str, Any]] | None = None) -> pd.DataFrame:
    """
    Turn processed.json into a DataFrame with:
    - parsed timestamps
    - num_actions
    - priority_score + priority_label
    """
    if processed is None:
        processed = load_processed()

    if not processed:
        return pd.DataFrame()

    df = pd.DataFrame(processed)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Number of action items
    df["num_actions"] = df["actions"].apply(_count_actions)

    # Priority scoring
    scores_labels = df.apply(_compute_priority_row, axis=1)
    df["priority_score"] = [sl[0] for sl in scores_labels]
    df["priority_label"] = [sl[1] for sl in scores_labels]

    return df


def get_keyword_counts(df: pd.DataFrame, top_n: int = 20) -> list[tuple[str, int]]:
    """
    Build a simple keyword frequency list from subject + body.
    Returns list of (keyword, count).
    """
    if df.empty:
        return []

    text = (df["subject"].fillna("") + " " + df["body"].fillna("")).str.lower().str.cat(sep=" ")

    tokens = [
        t.strip(".,!?:;()[]\"'") for t in text.split()
    ]
    tokens = [
        t for t in tokens if t and t not in STOPWORDS and len(t) > 2
    ]

    counter = Counter(tokens)
    return counter.most_common(top_n)
