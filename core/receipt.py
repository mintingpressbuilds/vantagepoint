from core.chain import get_wrapper, extract_receipt_info


def generate_receipt(session):
    """Generate full session receipt with chain."""
    wrapper = get_wrapper(chain_name=f"vp_{session.id[:8]}")

    @wrapper
    def _build_receipt(session_data):
        return session_data

    wrapped = _build_receipt(session.to_dict())
    receipt_info = extract_receipt_info(wrapped)

    receipt = {
        "session_id": session.id,
        "mode": session.mode,
        "created_at": session.created_at,
        "friction": session.friction,
        "friction_statement": session.friction_statement,
        "territory": {
            "nodes": len(session.territory["nodes"]),
            "ground": len([n for n in session.territory["nodes"] if n["type"] == "ground"]),
            "convention": len([n for n in session.territory["nodes"] if n["type"] == "convention"]),
            "unknown": len([n for n in session.territory["nodes"] if n["type"] == "unknown"]),
        },
        "discoveries": session.discoveries,
        "assumptions": session.assumptions,
        "goal": session.goal,
        "paths": [{"path_id": p["path_id"], "label": p["label"], "risk": p["risk"]} for p in session.paths],
        "chosen_path": session.chosen_path["path_id"] if session.chosen_path else None,
        "chain": receipt_info,
        "chain_entries": session.chain_entries,
    }

    session.chain_entries.append({
        "phase": "receipt", "action": "receipt_generated",
        "chain_id": receipt_info["chain_id"],
    })

    return receipt
