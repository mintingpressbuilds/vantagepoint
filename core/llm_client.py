import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("DOORWAY_MODEL", "claude-sonnet-4-20250514")


def call_llm(prompt):
    """Call Anthropic API directly. Returns dict with answer."""
    if not API_KEY:
        return {"answer": "[No API key]", "success": False}
    payload = json.dumps({
        "model": MODEL, "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
            return {"answer": data["content"][0]["text"], "success": True}
    except Exception as e:
        return {"answer": f"[LLM error: {str(e)[:120]}]", "success": False}
