import requests
import os
from core.config import OPENROUTER_API_KEY
from core.prompts import load_prompts  # ✅ Import to load prompts

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# ---------- OpenRouter Model (FAST + FREE) ----------
DEFAULT_MODEL = "meta-llama/llama-3.2-3b-instruct"
MODEL = DEFAULT_MODEL


def call_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    r = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter Error {r.status_code}: {r.text}")

    return r.json()["choices"][0]["message"]["content"].strip()


def ask_grok(user_query: str, email: dict) -> str:
    prompt = f"""
You are an email assistant.

Email:
Sender: {email.get('sender')}
Subject: {email.get('subject')}
Body:
{email.get('body')}

User question:
{user_query}

Give a short, clear answer.
"""
    return call_openrouter(prompt)


def generate_reply_draft(email: dict) -> str:
    """Generate reply draft using the saved auto_reply_prompt."""

    # ✅ Load the current prompts from file
    prompts = load_prompts()
    auto_reply_prompt = prompts.get(
        "auto_reply_prompt", "Write a polite reply to this email."
    )

    # ✅ Use the user's custom prompt
    prompt = f"""{auto_reply_prompt}

Original Email:
Sender: {email.get('sender')}
Subject: {email.get('subject')}
Body:
{email.get('body')}

Generate the reply now:
"""

    return call_openrouter(prompt)


# -----------------------------------------------------------
