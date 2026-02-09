import os
import json
from django.conf import settings
from google import genai

def _client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env and restart server.")
    return genai.Client(api_key=key)

def generate_text(prompt: str) -> str:
    client = _client()
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")

    try:
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return (resp.text or "").strip()
    except Exception as e:
        # Common: 429 RESOURCE_EXHAUSTED
        # We return "" so views can fallback instead of crashing.
        return ""

def generate_json(prompt: str) -> dict:
    text = generate_text(prompt)
    try:
        return json.loads(text)
    except Exception:
        return {}
