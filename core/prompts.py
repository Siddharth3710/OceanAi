import json
import os

DEFAULT_PROMPTS = {
    "categorization_prompt": (
        "You are an email categorization assistant. "
        "Categorize this email into one of these categories: Important, Newsletter, Spam, To-Do. "
        "To-Do emails must include a direct request requiring user action. "
        "Reply ONLY with the category name."
    ),
    "action_item_prompt": (
        "Extract all action items and deadlines from this email. Respond in JSON as a list under 'tasks': "
        "[{\"task\": \"...\", \"deadline\": \"...\"}]. If there is no explicit deadline, set \"deadline\": null."
    ),
    "auto_reply_prompt": (
        "You write polite, concise professional replies. Draft a reply to this email based on the user's tone: "
        "friendly but professional. If it is a meeting request, ask for an agenda and confirm time. "
        "Respond with Subject and Body in a clearly marked format."
    )
}

PROMPTS_PATH = "data/prompts.json"


def load_prompts():
    if os.path.exists(PROMPTS_PATH):
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_PROMPTS.copy()


def save_prompts(prompts: dict):
    os.makedirs(os.path.dirname(PROMPTS_PATH), exist_ok=True)
    with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
