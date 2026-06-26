"""
Grounded AI tutor for the Databricks DE Associate study hub.

Calls GitHub Models (free, OpenAI-compatible). The token is read from
Streamlit secrets / env on the SERVER side only -- it is never sent to the
browser, which also avoids any browser CORS issues.

The tutor is grounded in the study hub's own section notes (content.json),
which follow the official July 25, 2025 exam outline. It is instructed to say
when it is unsure rather than invent facts.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

CONTENT_PATH = Path(__file__).parent / "content.json"

# GitHub Models defaults (override via secrets if the endpoint/model changes)
DEFAULT_ENDPOINT = "https://models.github.ai/inference"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def load_content() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


def notes_context(content: dict) -> str:
    """Compact plain-text grounding built from the section notes."""
    parts = []
    for s in content["sections"]:
        parts.append(f"## {s['title']}\nObjectives: " + "; ".join(s["objectives"]))
        parts.append(_strip_html(s["notes"]))
    return "\n\n".join(parts)


def system_prompt(content: dict) -> str:
    return (
        "You are a friendly, accurate study tutor for the "
        "Databricks Certified Data Engineer Associate exam "
        f"({content['meta']['outlineVersion']} outline).\n"
        "Ground every answer in the STUDY NOTES below and your knowledge of "
        "these specific Databricks exam topics. Be concise and clear; use short "
        "examples or a tiny code snippet when it helps.\n"
        "IMPORTANT: If a question is outside these exam topics, or you are not "
        "confident the answer is correct, say so plainly (e.g. \"I'm not sure\") "
        "and point the student to the official exam guide rather than guessing. "
        "Never invent Databricks features, syntax, or numbers.\n\n"
        "=== STUDY NOTES ===\n" + notes_context(content)
    )


def question_lookup(content: dict, section_title: str, qnum: int) -> str | None:
    for s in content["sections"]:
        if s["title"] == section_title:
            qs = s["quiz"]
            if 1 <= qnum <= len(qs):
                q = qs[qnum - 1]
                opts = "\n".join(
                    f"{chr(65+i)}. {o}" for i, o in enumerate(q["opts"])
                )
                return (
                    f"Explain this question and WHY the correct answer is right "
                    f"(and why the others are wrong):\n\n{q['q']}\n{opts}\n"
                    f"Correct answer: {chr(65+q['a'])}. Topic: {q['obj']}"
                )
    return None


def get_config(secrets: dict | None = None) -> dict:
    """Pull token/endpoint/model from Streamlit secrets, then env vars."""
    secrets = secrets or {}
    token = (
        secrets.get("GITHUB_TOKEN")
        or secrets.get("github_token")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GITHUB_MODELS_TOKEN")
    )
    return {
        "token": token,
        "endpoint": secrets.get("GITHUB_MODELS_ENDPOINT")
        or os.environ.get("GITHUB_MODELS_ENDPOINT")
        or DEFAULT_ENDPOINT,
        "model": secrets.get("GITHUB_MODELS_MODEL")
        or os.environ.get("GITHUB_MODELS_MODEL")
        or DEFAULT_MODEL,
    }


def ask(messages: list[dict], config: dict, timeout: int = 45) -> str:
    """messages = [{role, content}, ...] (system prompt is prepended by caller).
    Returns the assistant text, or a friendly error string."""
    if not config.get("token"):
        return ("⚠️ AI is not configured. Add a GITHUB_TOKEN secret to enable "
                "the tutor (see the README).")
    url = config["endpoint"].rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": config["model"],
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 700,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {config['token']}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        if e.code in (401, 403):
            return ("⚠️ The GitHub Models token was rejected (401/403). "
                    "Check that the token is valid and has 'models' access.")
        if e.code == 429:
            return ("⏳ Rate limit reached on the free tier (about 50 requests/"
                    "day on top models). Try again later.")
        return f"⚠️ AI request failed ({e.code}). {detail}"
    except Exception as e:  # noqa: BLE001
        return f"⚠️ Could not reach the AI service: {e}"
