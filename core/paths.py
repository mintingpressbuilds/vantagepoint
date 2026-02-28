from core.mode import Mode
from core.doorway_client import call_doorway
from core.llm_client import call_llm


def generate_paths(session):
    """
    Generate three paths from the verified goal.
    PATH A: Maximum divergence — break every convention that can be broken
    PATH B: Informed hybrid — break conventions flagged as habit not physics
    PATH C: Confirmed ground — maximum confidence, closest to known territory
    """
    if not session.goal:
        raise ValueError("No goal set. Complete vantage phase first.")

    if session.mode == Mode.DOORWAY:
        paths = _generate_doorway_paths(session)
    elif session.mode == Mode.LLM:
        paths = _generate_llm_paths(session)
    else:
        paths = _generate_standalone_paths(session)

    session.paths = paths
    session.chain_entries.append({
        "phase": "paths", "action": "paths_generated",
        "count": len(paths),
    })
    return paths


def commit_path(session, path_id):
    """User commits to a path. Nothing runs until commit."""
    matching = [p for p in session.paths if p["path_id"] == path_id]
    if not matching:
        raise ValueError(f"Path {path_id} not found")
    session.chosen_path = matching[0]
    session.chain_entries.append({
        "phase": "paths", "action": "path_committed",
        "path_id": path_id, "label": matching[0]["label"],
    })
    session.advance_phase("receipt")
    return session


def _generate_doorway_paths(session):
    """Use Doorway for geometric path generation."""
    paths = []
    conventions = [a["statement"] for a in session.assumptions if a["classification"] == "convention"]

    # PATH A — Maximum divergence
    prompt_a = (
        f"Goal: {session.goal}. "
        f"Break every conventional assumption: {conventions}. "
        f"What is the most divergent viable approach?"
    )
    result_a = call_doorway(prompt_a)
    paths.append({
        "path_id": "A", "label": "Maximum divergence",
        "description": result_a.get("content", {}).get("answer", ""),
        "gap_score": result_a.get("structure", {}).get("gap_score", 0),
        "status": result_a.get("status", "PROVISIONAL"),
        "assumptions": result_a.get("bridge", {}).get("assumptions", []) if result_a.get("bridge") else [],
        "confidence": result_a.get("bridge", {}).get("confidence", 0) if result_a.get("bridge") else result_a.get("content", {}).get("confidence", 0),
        "risk": "high",
        "doorway_result": result_a,
    })

    # PATH B — Informed hybrid
    prompt_b = (
        f"Goal: {session.goal}. "
        f"These are conventions (not physics): {conventions}. "
        f"Break only the ones that are clearly habit. Keep confirmed constraints. "
        f"What is the balanced approach?"
    )
    result_b = call_doorway(prompt_b)
    paths.append({
        "path_id": "B", "label": "Informed hybrid",
        "description": result_b.get("content", {}).get("answer", ""),
        "gap_score": result_b.get("structure", {}).get("gap_score", 0),
        "status": result_b.get("status", "PROVISIONAL"),
        "assumptions": result_b.get("bridge", {}).get("assumptions", []) if result_b.get("bridge") else [],
        "confidence": result_b.get("bridge", {}).get("confidence", 0) if result_b.get("bridge") else result_b.get("content", {}).get("confidence", 0),
        "risk": "moderate",
        "doorway_result": result_b,
    })

    # PATH C — Confirmed ground
    prompt_c = (
        f"Goal: {session.goal}. "
        f"Use only confirmed ground. No conventions broken. Maximum confidence path. "
        f"What is the safest viable approach?"
    )
    result_c = call_doorway(prompt_c)
    paths.append({
        "path_id": "C", "label": "Confirmed ground",
        "description": result_c.get("content", {}).get("answer", ""),
        "gap_score": result_c.get("structure", {}).get("gap_score", 0),
        "status": result_c.get("status", "PROVISIONAL"),
        "assumptions": [],
        "confidence": result_c.get("content", {}).get("confidence", 0),
        "risk": "low",
        "doorway_result": result_c,
    })

    return paths


def _generate_llm_paths(session):
    """Use LLM for path generation (no geometric layer)."""
    conventions = [a["statement"] for a in session.assumptions if a["classification"] == "convention"]
    prompt = (
        f"Goal: {session.goal}.\n"
        f"Known conventions (assumptions, not physics): {conventions}\n\n"
        f"Generate three approaches:\n"
        f"A) Maximum divergence — break every convention. Highest risk, highest potential.\n"
        f"B) Informed hybrid — break conventions selectively. Balanced.\n"
        f"C) Confirmed ground — safest path. No conventions broken.\n\n"
        f"For each: describe the approach, list assumptions, rate confidence (0-1), rate risk (low/moderate/high)."
    )
    result = call_llm(prompt)
    # Parse into three paths — best effort
    answer = result.get("answer", "")
    return [
        {"path_id": "A", "label": "Maximum divergence", "description": answer, "gap_score": 0, "status": "LLM", "assumptions": conventions, "confidence": 0.5, "risk": "high"},
        {"path_id": "B", "label": "Informed hybrid", "description": "See full analysis above", "gap_score": 0, "status": "LLM", "assumptions": [], "confidence": 0.6, "risk": "moderate"},
        {"path_id": "C", "label": "Confirmed ground", "description": "See full analysis above", "gap_score": 0, "status": "LLM", "assumptions": [], "confidence": 0.7, "risk": "low"},
    ]


def _generate_standalone_paths(session):
    """Standalone: provide framework for user to fill in."""
    conventions = [a["statement"] for a in session.assumptions if a["classification"] == "convention"]
    return [
        {"path_id": "A", "label": "Maximum divergence",
         "description": f"Break all conventions: {conventions}. Describe your most divergent viable approach.",
         "gap_score": 0, "status": "STANDALONE", "assumptions": conventions, "confidence": 0, "risk": "high"},
        {"path_id": "B", "label": "Informed hybrid",
         "description": "Break conventions selectively. Keep confirmed constraints. Describe your balanced approach.",
         "gap_score": 0, "status": "STANDALONE", "assumptions": [], "confidence": 0, "risk": "moderate"},
        {"path_id": "C", "label": "Confirmed ground",
         "description": "Use only confirmed ground. Maximum safety. Describe your safest approach.",
         "gap_score": 0, "status": "STANDALONE", "assumptions": [], "confidence": 0, "risk": "low"},
    ]
