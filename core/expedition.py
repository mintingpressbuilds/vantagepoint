import uuid
from core.mode import Mode, detect_mode
from core.doorway_client import call_doorway
from core.llm_client import call_llm


def expand_territory(session, focus=None):
    """
    Expand territory around friction or a specific focus area.
    Uses the active mode to power analysis.
    """
    prompt = _build_expansion_prompt(session, focus)

    if session.mode == Mode.DOORWAY:
        result = call_doorway(prompt)
        nodes, edges = _extract_territory_from_doorway(result, session)
        session.doorway_results.append(result)
    elif session.mode == Mode.LLM:
        result = call_llm(prompt)
        nodes, edges = _extract_territory_from_llm(result, session)
    else:
        # Standalone: return the prompt for the user to analyze
        return {
            "prompt": prompt,
            "instruction": "Analyze this and identify: known facts (ground), "
                "assumptions treated as fact (convention), and genuinely unknown areas. "
                "Then call add_nodes() with your findings.",
        }

    # Add to territory
    for node in nodes:
        session.territory["nodes"].append(node)
    for edge in edges:
        session.territory["edges"].append(edge)

    # Update threshold
    session.threshold = _calculate_threshold(session)

    session.chain_entries.append({
        "phase": "expedition", "action": "territory_expanded",
        "focus": focus, "nodes_added": len(nodes),
        "threshold": session.threshold,
    })

    return {
        "nodes_added": nodes, "edges_added": edges,
        "threshold": session.threshold,
        "recommendation": "consolidate" if session.threshold > 0.7 else "continue",
    }


def add_node(session, label, node_type, significance=0.5):
    """Manually add a node (used in all modes, required in standalone)."""
    node = {
        "id": str(uuid.uuid4())[:8],
        "label": label,
        "type": node_type,       # ground | convention | unknown
        "significance": significance,
    }
    session.territory["nodes"].append(node)
    session.threshold = _calculate_threshold(session)
    return node


def add_edge(session, source_id, target_id, label="related"):
    """Add relationship between nodes."""
    edge = {"source": source_id, "target": target_id, "label": label}
    session.territory["edges"].append(edge)
    return edge


def flag_significant(session, node_id):
    """Manually flag a node as significant."""
    for node in session.territory["nodes"]:
        if node["id"] == node_id:
            node["significance"] = 1.0
            session.discoveries.append({
                "finding": node["label"],
                "significance": 1.0,
                "verified": False,
                "node_id": node_id,
            })
            return node
    raise ValueError(f"Node {node_id} not found")


def classify_assumption(session, statement, classification, evidence=""):
    """Classify an assumption as ground or convention."""
    assumption = {
        "statement": statement,
        "classification": classification,  # ground | convention
        "evidence": evidence,
    }
    session.assumptions.append(assumption)
    session.chain_entries.append({
        "phase": "expedition", "action": "assumption_classified",
        "data": assumption,
    })
    return assumption


def _build_expansion_prompt(session, focus):
    base = f"Problem space: {session.friction_statement}"
    if focus:
        base += f"\n\nFocus area: {focus}"
    if session.territory["nodes"]:
        known = [n["label"] for n in session.territory["nodes"] if n["type"] == "ground"]
        conventional = [n["label"] for n in session.territory["nodes"] if n["type"] == "convention"]
        unknown = [n["label"] for n in session.territory["nodes"] if n["type"] == "unknown"]
        base += f"\n\nAlready mapped — Ground: {known}. Convention: {conventional}. Unknown: {unknown}."
    base += (
        "\n\nExpand the territory. Identify what is genuinely known (ground), "
        "what is assumed without evidence (convention), and what is genuinely unknown. "
        "For each finding, state whether it is ground, convention, or unknown."
    )
    return base


def _extract_territory_from_doorway(result, session):
    """Extract territory nodes from a Doorway API response."""
    nodes = []
    edges = []
    status = result.get("status", "PROVISIONAL")
    shape = result.get("structure", {}).get("closest_shape", "unknown")
    gap_score = result.get("structure", {}).get("gap_score", 1.0)
    content = result.get("content", {}).get("answer", "")

    # The Doorway result itself becomes a node
    node_type = {
        "GROUND": "ground", "BRIDGE": "convention",
        "CONFLICT": "unknown", "PROVISIONAL": "unknown"
    }.get(status, "unknown")

    node = {
        "id": str(uuid.uuid4())[:8], "label": content[:120],
        "type": node_type, "significance": 1.0 - gap_score,
        "doorway_status": status, "shape": shape, "gap_score": gap_score,
    }
    nodes.append(node)

    # If bridge exists, add assumptions as convention nodes
    bridge = result.get("bridge")
    if bridge and bridge.get("assumptions"):
        for assumption in bridge["assumptions"]:
            a_node = {
                "id": str(uuid.uuid4())[:8], "label": assumption,
                "type": "convention", "significance": 0.6,
            }
            nodes.append(a_node)
            edges.append({"source": node["id"], "target": a_node["id"], "label": "assumes"})

    # If conflict, add as high-significance unknown
    conflict = result.get("conflict", {})
    if conflict.get("conflict"):
        c_node = {
            "id": str(uuid.uuid4())[:8], "label": conflict.get("message", "Conflict detected"),
            "type": "unknown", "significance": 0.9,
        }
        nodes.append(c_node)
        edges.append({"source": node["id"], "target": c_node["id"], "label": "conflicts"})

    return nodes, edges


def _extract_territory_from_llm(result, session):
    """Extract territory nodes from an LLM response."""
    nodes = []
    # LLM returns text — parse for ground/convention/unknown markers
    # This is a best-effort extraction. The methodology still works
    # if the user manually adds nodes instead.
    text = result.get("answer", "")
    node = {
        "id": str(uuid.uuid4())[:8], "label": text[:120],
        "type": "convention", "significance": 0.5,
    }
    nodes.append(node)
    return nodes, []


def _calculate_threshold(session):
    """Ground made vs ground remaining. Returns 0.0 to 1.0."""
    nodes = session.territory["nodes"]
    if not nodes:
        return 0.0
    ground = sum(1 for n in nodes if n["type"] == "ground")
    total = len(nodes)
    return round(ground / total, 3) if total > 0 else 0.0
