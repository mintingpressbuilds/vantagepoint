# VANTAGEPOINT — Build Specification

**Structured thinking methodology as infrastructure. pip install vantagepoint.**

Instructions for Claude Code: Read every section before writing a single line of code. Build in the exact sequence specified. Do not skip phases. Do not combine phases.

February 2026 · Part of Doorway · doorwayagi.com · All Rights Reserved

-----

## What This Document Is

Build specification for VantagePoint — a Python package that implements a structured thinking methodology. Five phases: provocation, expedition, vantage, paths, receipt. Works standalone, with an LLM, or with the Doorway AGI engine. No frontend. No UI. Pure infrastructure.

Researchers install it with `pip install vantagepoint`. doorway-platform renders the dashboard views on top of it. This repo builds the engine underneath.

> This is not a chatbot. Not an AI wrapper. Not a project management tool. This is the methodology that externalizes how humans think before committing to execution — made callable, chainable, and cryptographically verifiable.

-----

## Relation to Doorway

VantagePoint is Product Two on the Doorway platform. It is a separate installable package that works completely standalone. When Doorway is available, VantagePoint calls the Doorway API at each methodology step for geometric reasoning. When it’s not, the methodology still runs — the analysis is powered by an LLM or by the user directly.

```
doorway-platform
  └── Product One — AGI chat (calls doorway)
  └── Product Two — VantagePoint (calls vantagepoint + optionally doorway)

vantagepoint (this repo)
  optionally calls → doorway /run  (when DOORWAY_API_URL set)
  optionally calls → Anthropic API (when ANTHROPIC_API_KEY set, no doorway)
  uses → pruv (xy_wrap, receipts)
  uses → xycore (chain primitive via pruv)
```

-----

## Three Operating Modes

VantagePoint auto-detects its mode from environment variables. Strict priority chain:

```
DOORWAY_API_URL present   →  Mode 2: Doorway (ignores ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY only    →  Mode 3: LLM only
Neither                   →  Mode 1: Standalone
```

|Mode      |What Powers Analysis           |What’s Available                                                                                                                                                  |
|----------|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Standalone|User input only. No AI.        |Full five-phase methodology. User drives territory expansion, significance detection, path generation manually. Framework guides the process.                     |
|LLM       |Claude (or other model) via API|AI-assisted territory expansion, significance detection, assumption classification. No geometric layer. No gap scores. No bridge/conflict detection.              |
|Doorway   |Full Doorway engine via API    |Geometric reasoning at every step. Gap detector maps territory. Conflict detector finds convention vs physics. Bridge builder generates paths. Full status output.|

All five phases run in every mode. The mode determines what powers the analysis, not what analysis is available.

```
# .env configuration
# Mode 1: Standalone — no env vars needed
# Mode 2: Doorway — set this (takes priority if both set)
DOORWAY_API_URL=http://localhost:8000
# Mode 3: LLM only — set this (used only if DOORWAY_API_URL not set)
ANTHROPIC_API_KEY=sk-ant-xxx
# Optional: cloud chain sync
PRUV_API_KEY=pv_live_xxx
```

-----

## Repository Structure

```
vantagepoint/
├── core/
│   ├── __init__.py
│   ├── mode.py                ← Mode detection (standalone/llm/doorway)
│   ├── provocation.py         ← Phase 1: Friction → verified problem statement
│   ├── expedition.py          ← Phase 2: Territory expansion + significance detection
│   ├── vantage.py             ← Phase 3: Consolidation + goal statement
│   ├── paths.py               ← Phase 4: Three-path generation
│   ├── receipt.py             ← Phase 5: Session receipt generation
│   ├── session.py             ← Session state management across phases
│   ├── doorway_client.py      ← Doorway API client (Mode 2)
│   ├── llm_client.py          ← LLM client (Mode 3)
│   └── chain.py               ← xy_wrap integration
├── api/
│   ├── __init__.py
│   └── server.py              ← FastAPI server
├── tests/
│   ├── __init__.py
│   ├── test_provocation.py
│   ├── test_expedition.py
│   ├── test_vantage.py
│   ├── test_paths.py
│   ├── test_receipt.py
│   ├── test_session.py
│   └── test_modes.py
├── examples/
│   └── run_session.py         ← Example full session
├── main.py                    ← Entry point
├── cli.py                     ← CLI: vantagepoint run / vantagepoint serve
├── requirements.txt
└── README.md
```

-----

## Phase 0 — Environment Setup

```bash
pip install anthropic httpx xycore pruv pytest python-dotenv fastapi uvicorn
```

`.env` file (all optional):

```
DOORWAY_API_URL=http://localhost:8000
ANTHROPIC_API_KEY=sk-ant-xxx
PRUV_API_KEY=pv_live_xxx
DOORWAY_MODEL=claude-sonnet-4-20250514
```

Confirm dependencies:

```python
from pruv import xy_wrap, CloudClient, XYChain
print("pruv confirmed")

import httpx
print("httpx confirmed")

import fastapi
print("fastapi confirmed")
```

> Do not proceed to Phase 1 until environment is confirmed.

-----

## Phase 1 — Mode Detection + Session State

Build the mode detection and session management before any methodology logic.

### Mode Detection

```python
# core/mode.py
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
```

### Session State

```python
# core/session.py
import uuid
from datetime import datetime
from core.mode import detect_mode

class VPSession:
  def __init__(self, friction=None):
    self.id = str(uuid.uuid4())
    self.mode = detect_mode()
    self.created_at = datetime.utcnow().isoformat()
    self.phase = "provocation"
    self.friction = friction

    # Provocation output
    self.friction_statement = None
    self.calibration = {}           # what_wrong, how_long, what_right

    # Expedition output
    self.territory = {
      "nodes": [],                  # { id, label, type: ground|convention|unknown, significance: float }
      "edges": [],                  # { source, target, label }
      "clusters": [],               # { id, label, node_ids }
    }
    self.discoveries = []           # { finding, significance, verified: bool }
    self.assumptions = []           # { statement, classification: ground|convention, evidence }
    self.threshold = 0.0            # 0.0 to 1.0 — ground made vs ground remaining

    # Vantage output
    self.goal = None                # Verified goal statement
    self.vantage_summary = None     # What can be seen from here

    # Paths output
    self.paths = []                 # [ { path_id, label, description, gap_score, assumptions, confidence, risk } ]
    self.chosen_path = None

    # Doorway results (Mode 2 only)
    self.doorway_results = []       # Raw results from doorway /run calls

    # Chain
    self.chain_entries = []         # Every state transition logged

  def advance_phase(self, next_phase):
    valid_transitions = {
      "provocation": "expedition",
      "expedition": "vantage",
      "vantage": "paths",
      "paths": "receipt",
    }
    expected = valid_transitions.get(self.phase)
    if expected != next_phase:
      raise ValueError(f"Cannot go from {self.phase} to {next_phase}. Expected: {expected}")
    self.phase = next_phase

  def to_dict(self):
    return {
      "id": self.id, "mode": self.mode, "phase": self.phase,
      "created_at": self.created_at, "friction": self.friction,
      "friction_statement": self.friction_statement,
      "calibration": self.calibration, "territory": self.territory,
      "discoveries": self.discoveries, "assumptions": self.assumptions,
      "threshold": self.threshold, "goal": self.goal,
      "vantage_summary": self.vantage_summary, "paths": self.paths,
      "chosen_path": self.chosen_path, "chain_entries": self.chain_entries,
    }
```

Verify Phase 1: Mode detection returns correct mode for each env var combination. Session state initializes correctly. Phase transitions enforce order.

> Do not proceed to Phase 2 until verified.

-----

## Phase 2 — Provocation (Phase 1 of Methodology)

Entry point. The user enters friction — not a goal, not a task. Something wrong.

Three calibration questions before proceeding:

1. What specifically is wrong?
1. How long has it been this way?
1. What would right look like?

These calibrate the significance detector and establish the baseline state for the chain.

```python
# core/provocation.py
from core.session import VPSession
from core.mode import Mode

def start_session(friction):
  """Create session from initial friction statement."""
  session = VPSession(friction=friction)
  return session

def calibrate(session, what_wrong, how_long, what_right):
  """Run calibration questions. Returns verified friction statement."""
  session.calibration = {
    "what_wrong": what_wrong,
    "how_long": how_long,
    "what_right": what_right,
  }
  # Build verified friction statement
  session.friction_statement = (
    f"Friction: {session.friction}. "
    f"Specifically: {what_wrong}. "
    f"Duration: {how_long}. "
    f"Target state: {what_right}."
  )
  session.chain_entries.append({
    "phase": "provocation",
    "action": "calibrated",
    "data": session.calibration,
    "output": session.friction_statement,
  })
  return session

def complete_provocation(session):
  """Verify friction statement and advance to expedition."""
  if not session.friction_statement:
    raise ValueError("Must calibrate before completing provocation")
  session.advance_phase("expedition")
  return session
```

-----

## Phase 3 — Expedition (Phase 2 of Methodology)

Territory expansion. The core analytical engine. This is where the three modes diverge most.

### Territory Expansion

```python
# core/expedition.py
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
  if not nodes: return 0.0
  ground = sum(1 for n in nodes if n["type"] == "ground")
  total = len(nodes)
  return round(ground / total, 3) if total > 0 else 0.0
```

### Doorway Client

```python
# core/doorway_client.py
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
```

### LLM Client

```python
# core/llm_client.py
import os, json, urllib.request
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
    headers={"Content-Type": "application/json",
             "x-api-key": API_KEY, "anthropic-version": "2023-06-01"})
  try:
    with urllib.request.urlopen(req, timeout=30) as response:
      data = json.loads(response.read())
      return {"answer": data["content"][0]["text"], "success": True}
  except Exception as e:
    return {"answer": f"[LLM error: {str(e)[:120]}]", "success": False}
```

Verify Phase 3:

- Territory expansion works in all three modes
- Nodes and edges add correctly
- Threshold calculates correctly
- Doorway results parse into territory nodes
- Manual add_node and flag_significant work

> Do not proceed to Phase 4 until verified.

-----

## Phase 4 — Vantage (Phase 3 of Methodology)

Consolidation. Fires when threshold sensor recommends it (threshold > 0.7) or when user decides.

```python
# core/vantage.py
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
```

-----

## Phase 5 — Paths (Phase 4 of Methodology)

Three paths generated from the verified goal. Ordered by divergence from convention.

```python
# core/paths.py
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
```

-----

## Phase 6 — Receipt + Chain (Phase 5 of Methodology)

Every session produces a receipt. The complete reasoning trail, cryptographically verifiable.

```python
# core/chain.py
import os
from pruv import xy_wrap, CloudClient, XYChain

PRUV_API_KEY = os.getenv("PRUV_API_KEY")  # None in local dev — fine

def get_wrapper(chain_name="vantagepoint"):
  return xy_wrap(
    chain_name=chain_name, auto_redact=True,
    **({"api_key": PRUV_API_KEY} if PRUV_API_KEY else {})
  )

def extract_receipt_info(wrapped_result):
  return {
    "chain_id": wrapped_result.chain.id, "chain_root": wrapped_result.chain.root,
    "chain_length": wrapped_result.chain.length, "chain_verified": wrapped_result.verified,
    "receipt": wrapped_result.receipt,
  }
```

```python
# core/receipt.py
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
```

-----

## Phase 7 — API Server + CLI + Main Pipeline

### Main Pipeline

```python
# main.py
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
```

### API Server

```python
# api/server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from core.session import VPSession
from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import expand_territory, add_node, classify_assumption, flag_significant
from core.vantage import consolidate, verify_discovery, set_goal, complete_vantage
from core.paths import generate_paths, commit_path
from core.receipt import generate_receipt
from core.mode import detect_mode, get_mode_description

app = FastAPI(title="VantagePoint", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
  allow_methods=["*"], allow_headers=["*"])

# In-memory session store (production: use database)
sessions = {}

class StartRequest(BaseModel):
  friction: str

class CalibrateRequest(BaseModel):
  what_wrong: str
  how_long: str
  what_right: str

class ExpandRequest(BaseModel):
  focus: Optional[str] = None

class NodeRequest(BaseModel):
  label: str
  node_type: str
  significance: float = 0.5

class AssumptionRequest(BaseModel):
  statement: str
  classification: str
  evidence: str = ""

class GoalRequest(BaseModel):
  goal: str

class CommitRequest(BaseModel):
  path_id: str

@app.get("/health")
async def health():
  mode = detect_mode()
  return {"status": "ok", "engine": "vantagepoint", "mode": mode}

@app.post("/session/start")
async def api_start(req: StartRequest):
  session = start_session(req.friction)
  sessions[session.id] = session
  return {"session_id": session.id, "mode": session.mode, "phase": session.phase}

@app.post("/session/{session_id}/calibrate")
async def api_calibrate(session_id: str, req: CalibrateRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  calibrate(session, req.what_wrong, req.how_long, req.what_right)
  return {"friction_statement": session.friction_statement}

@app.post("/session/{session_id}/provocation/complete")
async def api_complete_provocation(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  complete_provocation(session)
  return {"phase": session.phase}

@app.post("/session/{session_id}/expedition/expand")
async def api_expand(session_id: str, req: ExpandRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  result = expand_territory(session, req.focus)
  return result

@app.post("/session/{session_id}/expedition/node")
async def api_add_node(session_id: str, req: NodeRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return add_node(session, req.label, req.node_type, req.significance)

@app.post("/session/{session_id}/expedition/assumption")
async def api_classify(session_id: str, req: AssumptionRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return classify_assumption(session, req.statement, req.classification, req.evidence)

@app.post("/session/{session_id}/vantage/consolidate")
async def api_consolidate(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return consolidate(session)

@app.post("/session/{session_id}/vantage/goal")
async def api_set_goal(session_id: str, req: GoalRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  set_goal(session, req.goal)
  return {"goal": session.goal}

@app.post("/session/{session_id}/vantage/complete")
async def api_complete_vantage(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  complete_vantage(session)
  return {"phase": session.phase}

@app.post("/session/{session_id}/paths/generate")
async def api_generate_paths(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return {"paths": generate_paths(session)}

@app.post("/session/{session_id}/paths/commit")
async def api_commit(session_id: str, req: CommitRequest):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  commit_path(session, req.path_id)
  return {"chosen_path": session.chosen_path, "phase": session.phase}

@app.post("/session/{session_id}/receipt")
async def api_receipt(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return generate_receipt(session)

@app.get("/session/{session_id}")
async def api_get_session(session_id: str):
  session = sessions.get(session_id)
  if not session: raise HTTPException(404, "Session not found")
  return session.to_dict()
```

### CLI

```python
# cli.py
import argparse, uvicorn

def main():
  parser = argparse.ArgumentParser(description="VantagePoint")
  sub = parser.add_subparsers(dest="command")
  serve = sub.add_parser("serve", help="Start API server")
  serve.add_argument("--host", default="0.0.0.0")
  serve.add_argument("--port", type=int, default=8001)
  rp = sub.add_parser("run", help="Start interactive session")
  rp.add_argument("friction", type=str, help="What's wrong?")
  args = parser.parse_args()
  if args.command == "serve":
    uvicorn.run("api.server:app", host=args.host, port=args.port)
  elif args.command == "run":
    from main import run_interactive
    session = run_interactive(args.friction)
    print(f"Session started: {session.id}")
    print(f"Mode: {session.mode}")
    print("Use the API to continue: POST /session/{id}/calibrate")

if __name__ == "__main__": main()
```

> VantagePoint API runs on port 8001 by default. Doorway runs on 8000.

-----

## Definition of Done

- [ ] Mode detection works correctly for all three modes
- [ ] Session state tracks all five phases with enforced transitions
- [ ] Provocation creates verified friction statement from calibration
- [ ] Expedition expands territory in all three modes
- [ ] Territory nodes classified correctly (ground/convention/unknown)
- [ ] Threshold sensor calculates and recommends consolidation
- [ ] Vantage consolidation produces summary with discoveries and assumptions
- [ ] Paths generates three paths (A: divergent, B: hybrid, C: ground) in all modes
- [ ] Commit flow requires explicit user commitment
- [ ] Receipt generates with full chain via xy_wrap
- [ ] API server responds correctly on all endpoints
- [ ] CLI starts server and interactive session
- [ ] Full session runs provocation → expedition → vantage → paths → receipt
- [ ] README documents all three modes, API endpoints, and CLI

> When all are checked — VantagePoint is done. The methodology is infrastructure.

-----

## What This Package Is Not

VantagePoint does not contain UI components. No React. No HTML. No dashboard views. The five-view dashboard (provocation form, territory map, expedition feed, vantage view, paths view) lives in doorway-platform. This package is the engine underneath.

VantagePoint does not contain Doorway’s reasoning logic. It calls the Doorway API when available. It does not reimplement gap detection, bridge building, or conflict detection.

VantagePoint does not require Doorway. It works standalone. Doorway is an optional layer that deepens each step.

-----

VantagePoint — Build Specification · February 2026 · Part of Doorway · doorwayagi.com · All Rights Reserved
