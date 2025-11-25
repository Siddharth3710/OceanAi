import json
import os
import requests
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import PROCESSED_PATH, OPENROUTER_API_KEY
from core.prompts import load_prompts
from core.ingest import load_mock_inbox


# -----------------------------------------------------------
# OpenRouter Setup
# -----------------------------------------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Good balance of speed and accuracy
MODEL = "meta-llama/llama-3.2-3b-instruct"

# Balanced settings for speed + accuracy
MAX_WORKERS = 5  # Process 5 emails at once
REQUEST_TIMEOUT = 20
RATE_LIMIT_DELAY = 0.2

if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY in .env")


def call_openrouter(prompt: str) -> str:
    """Fast API call with one retry."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300,
    }

    for attempt in range(2):  # Try twice
        try:
            resp = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
            )

            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 429:
                time.sleep(2)
                continue
            else:
                raise RuntimeError(f"API Error {resp.status_code}")

        except requests.exceptions.Timeout:
            if attempt == 0:
                time.sleep(1)
                continue
            raise RuntimeError("Timeout")

    raise RuntimeError("Failed after retries")


# -----------------------------------------------------------
# Categorization - Accurate
# -----------------------------------------------------------


def categorize_email(email: Dict[str, Any], categorization_prompt: str) -> str:
    """Categorize with clear, focused prompt."""

    full_prompt = f"""{categorization_prompt}

Email:
Sender: {email.get('sender')}
Subject: {email.get('subject')}
Body:
{email.get('body')}

Respond with ONLY the category name (like: "Work", "Personal", "Urgent", etc.)."""

    out = call_openrouter(full_prompt)
    return out.splitlines()[0].strip()


# -----------------------------------------------------------
# Action Extraction - Accurate
# -----------------------------------------------------------


def extract_actions(email: Dict[str, Any], action_prompt: str) -> Any:
    """Extract actions with clear prompt."""

    full_prompt = f"""{action_prompt}

Email:
Sender: {email.get('sender')}
Subject: {email.get('subject')}
Body:
{email.get('body')}

Respond ONLY with valid JSON.
Do NOT use backticks or markdown."""

    raw = call_openrouter(full_prompt).strip()

    # Clean JSON
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return raw


# -----------------------------------------------------------
# Process Single Email in Parallel
# -----------------------------------------------------------


def process_single_email(email: Dict, prompts: Dict) -> Dict:
    """
    Process one email with both categorization and action extraction.
    Designed for parallel execution.
    """
    try:
        # Small delay to respect rate limits
        time.sleep(RATE_LIMIT_DELAY)

        # Process both tasks
        category = categorize_email(email, prompts["categorization_prompt"])
        actions = extract_actions(email, prompts["action_item_prompt"])

        return {
            "id": email.get("id"),
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "timestamp": email.get("timestamp"),
            "body": email.get("body"),
            "category": category,
            "actions": actions,
            "status": "success",
        }

    except Exception as e:
        return {
            "id": email.get("id"),
            "sender": email.get("sender"),
            "subject": email.get("subject"),
            "timestamp": email.get("timestamp"),
            "body": email.get("body"),
            "category": "Error",
            "actions": f"Processing failed: {str(e)}",
            "status": "error",
        }


# -----------------------------------------------------------
# Save / Load
# -----------------------------------------------------------


def save_processed(processed: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)


def load_processed():
    if not os.path.exists(PROCESSED_PATH):
        return []

    try:
        with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []


# -----------------------------------------------------------
# Main Pipeline - Parallel with Accuracy
# -----------------------------------------------------------


def run_ingestion_pipeline() -> List[Dict[str, Any]]:
    """
    Process emails in parallel while maintaining accuracy.
    Expected: 12-18 seconds for 24 emails with good accuracy.
    """
    emails = load_mock_inbox()
    if not emails:
        raise RuntimeError("No emails found. Put data/mock_inbox.json first.")

    prompts = load_prompts()
    cat_prompt = prompts["categorization_prompt"]
    act_prompt = prompts["action_item_prompt"]

    processed: List[Dict[str, Any]] = []

    print(f"⚡ Processing {len(emails)} emails with {MAX_WORKERS} parallel workers...")
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_email = {
                executor.submit(process_single_email, email, prompts): email
                for email in emails
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_email):
                result = future.result()
                processed.append(result)
                completed += 1

                # Progress indicator
                if result["status"] == "success":
                    print(
                        f"✅ [{completed}/{len(emails)}] {result['subject'][:40]} → {result['category']}"
                    )
                else:
                    print(
                        f"⚠️  [{completed}/{len(emails)}] Failed: {result['subject'][:40]}"
                    )

    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n⚠️  Error during processing: {e}")

    # Sort by ID to maintain order
    processed.sort(key=lambda x: x["id"])

    # Summary
    success_count = sum(1 for p in processed if p.get("status") == "success")
    error_count = len(processed) - success_count
    elapsed = time.time() - start_time

    print(
        f"\n✨ Complete in {elapsed:.1f}s! Success: {success_count}, Errors: {error_count}"
    )

    save_processed(processed)
    return processed
