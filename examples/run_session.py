"""
Example: Full VantagePoint session in standalone mode.

Run from the project root:
  python -m examples.run_session
Or:
  cd vantagepoint && python examples/run_session.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    run_interactive, calibrate, complete_provocation,
    add_node, add_edge, flag_significant, classify_assumption,
    consolidate, verify_discovery, set_goal, complete_vantage,
    generate_paths, commit_path, generate_receipt,
)

# Phase 1: Provocation
session = run_interactive("Our customer onboarding takes too long")

calibrate(
    session,
    what_wrong="New users take 3 weeks to reach first value",
    how_long="Since launch — 18 months",
    what_right="First value in under 3 days",
)
complete_provocation(session)
print(f"Friction statement: {session.friction_statement}\n")

# Phase 2: Expedition
n1 = add_node(session, "Onboarding requires 12 steps", "ground", 0.9)
n2 = add_node(session, "Users must complete training first", "convention", 0.5)
n3 = add_node(session, "API integration is the bottleneck", "unknown", 0.7)
n4 = add_node(session, "Competitors onboard in 2 days", "ground", 0.8)

add_edge(session, n2["id"], n3["id"], "blocks")
flag_significant(session, n3["id"])

classify_assumption(session, "Training must come before access", "convention")
classify_assumption(session, "12 steps are all necessary", "convention", "never audited")
classify_assumption(session, "API is required for value", "ground", "confirmed with users")

print(f"Territory: {len(session.territory['nodes'])} nodes, threshold: {session.threshold}")

# Phase 3: Vantage
session.advance_phase("vantage")
summary = consolidate(session)
verify_discovery(session, 0)
print(f"\nVantage summary: {summary['recommendation']}")

set_goal(session, "Deliver first value within 72 hours of signup")
complete_vantage(session)

# Phase 4: Paths
paths = generate_paths(session)
for p in paths:
    print(f"\nPath {p['path_id']}: {p['label']} (risk: {p['risk']})")
    print(f"  {p['description'][:100]}...")

commit_path(session, "B")
print(f"\nCommitted to: {session.chosen_path['label']}")

# Phase 5: Receipt
receipt = generate_receipt(session)
print(f"\n--- Receipt ---")
print(f"Session: {receipt['session_id']}")
print(f"Mode: {receipt['mode']}")
print(f"Goal: {receipt['goal']}")
print(f"Chosen path: {receipt['chosen_path']}")
print(f"Chain verified: {receipt['chain']['chain_verified']}")
print(f"Chain length: {receipt['chain']['chain_length']}")
