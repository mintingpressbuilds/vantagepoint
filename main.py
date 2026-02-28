from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import expand_territory, add_node, add_edge, flag_significant, classify_assumption
from core.vantage import consolidate, verify_discovery, set_goal, complete_vantage, return_to_expedition
from core.paths import generate_paths, commit_path
from core.receipt import generate_receipt
from core.mode import detect_mode, get_mode_description


def run_interactive(friction):
    """Run a full VantagePoint session interactively."""
    mode = detect_mode()
    print(f"\nVantagePoint — {get_mode_description(mode)}")
    print(f"Friction: {friction}\n")

    session = start_session(friction)
    return session


# Re-export all functions for clean API
__all__ = [
    "start_session", "calibrate", "complete_provocation",
    "expand_territory", "add_node", "add_edge", "flag_significant",
    "classify_assumption", "consolidate", "verify_discovery",
    "set_goal", "complete_vantage", "return_to_expedition",
    "generate_paths", "commit_path", "generate_receipt",
    "detect_mode", "run_interactive",
]
