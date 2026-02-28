import os


class Mode:
    STANDALONE = "standalone"
    LLM = "llm"
    DOORWAY = "doorway"


def detect_mode():
    """Strict priority: Doorway > LLM > Standalone."""
    if os.getenv("DOORWAY_API_URL"):
        return Mode.DOORWAY
    elif os.getenv("ANTHROPIC_API_KEY"):
        return Mode.LLM
    else:
        return Mode.STANDALONE


def get_mode_description(mode):
    return {
        Mode.STANDALONE: "Standalone — user drives all analysis",
        Mode.LLM: "LLM — AI-assisted analysis, no geometric layer",
        Mode.DOORWAY: "Doorway — full geometric reasoning at every step",
    }[mode]
