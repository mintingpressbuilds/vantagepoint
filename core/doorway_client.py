import os
import httpx

DOORWAY_API_URL = os.getenv("DOORWAY_API_URL")


def call_doorway(input_text, session_name="vantagepoint"):
    """Call Doorway API. Returns full result dict."""
    if not DOORWAY_API_URL:
        raise RuntimeError("DOORWAY_API_URL not set")
    response = httpx.post(
        f"{DOORWAY_API_URL}/run",
        json={"input": input_text, "session_name": session_name},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()
