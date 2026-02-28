from core.mode import Mode
from core.doorway_client import call_doorway
from core.llm_client import call_llm


def consolidate(session):
    """
    Consolidate territory into discoveries, assumptions, and goal.
    Returns summary of what was found.
    """
    summary = _build_vantage_summary(session)

    session.vantage_summary = summary
    session.chain_entries.append({
        "phase": "vantage", "action": "consolidated",
        "discoveries": len(session.discoveries),
        "assumptions": len(session.assumptions),
        "threshold": session.threshold,
    })
    return summary


def verify_discovery(session, discovery_index):
    """Mark a discovery as verified after user review."""
    if discovery_index >= len(session.discoveries):
        raise IndexError(f"Discovery {discovery_index} not found")
    session.discoveries[discovery_index]["verified"] = True
    return session.discoveries[discovery_index]


def set_goal(session, goal_statement):
    """Set the verified goal. User must explicitly commit."""
    session.goal = goal_statement
    session.chain_entries.append({
        "phase": "vantage", "action": "goal_set",
        "goal": goal_statement,
    })
    return session


def complete_vantage(session):
    """Advance to paths. Requires goal to be set."""
    if not session.goal:
        raise ValueError("Must set goal before advancing to paths")
    session.advance_phase("paths")
    return session


def return_to_expedition(session):
    """Go back for another territory pass."""
    session.phase = "expedition"
    session.chain_entries.append({
        "phase": "vantage", "action": "returned_to_expedition",
    })
    return session


def _build_vantage_summary(session):
    ground_nodes = [n for n in session.territory["nodes"] if n["type"] == "ground"]
    convention_nodes = [n for n in session.territory["nodes"] if n["type"] == "convention"]
    unknown_nodes = [n for n in session.territory["nodes"] if n["type"] == "unknown"]
    verified_discoveries = [d for d in session.discoveries if d["verified"]]
    return {
        "territory_covered": len(session.territory["nodes"]),
        "ground": len(ground_nodes),
        "convention": len(convention_nodes),
        "unknown": len(unknown_nodes),
        "discoveries": session.discoveries,
        "verified_discoveries": len(verified_discoveries),
        "assumptions": session.assumptions,
        "threshold": session.threshold,
        "recommendation": (
            "Territory well mapped. Set your goal and proceed to paths."
            if session.threshold > 0.6
            else "Consider another expedition pass — significant unknown territory remains."
        ),
    }
