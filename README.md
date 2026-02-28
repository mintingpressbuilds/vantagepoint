# VantagePoint

Created by Luke H · [doorwayagi.com](https://doorwayagi.com)

Structured thinking methodology as an installable Python package. Five phases: provocation, expedition, vantage, paths, receipt.

Part of [Doorway](https://doorwayagi.com). Works completely standalone.

## Install

```bash
pip install vantagepoint
```

Or from source:

```bash
pip install -r requirements.txt
```

## Three Operating Modes

VantagePoint auto-detects its mode from environment variables:

| Priority | Env Var | Mode | What Powers Analysis |
|----------|---------|------|---------------------|
| 1 | `DOORWAY_API_URL` | Doorway | Full geometric reasoning at every step |
| 2 | `ANTHROPIC_API_KEY` | LLM | AI-assisted analysis, no geometric layer |
| 3 | Neither | Standalone | User drives all analysis manually |

```bash
# Standalone — no env vars needed

# Doorway mode (takes priority if both set)
export DOORWAY_API_URL=http://localhost:8000

# LLM mode (used only if DOORWAY_API_URL not set)
export ANTHROPIC_API_KEY=sk-ant-xxx

# Optional: cloud chain sync
export PRUV_API_KEY=pv_live_xxx
```

All five phases run in every mode. The mode determines what powers the analysis, not what analysis is available.

## CLI

```bash
# Start the API server (port 8001)
python cli.py serve
python cli.py serve --port 9000

# Start an interactive session
python cli.py run "Our deploys keep breaking"
```

## API Endpoints

VantagePoint runs on port 8001. All session endpoints follow the methodology phases.

### Health

```
GET /health
→ {"status": "ok", "engine": "vantagepoint", "mode": "standalone"}
```

### Provocation

```
POST /session/start
  {"friction": "Our deploys keep breaking"}
→ {"session_id": "...", "mode": "standalone", "phase": "provocation"}

POST /session/{id}/calibrate
  {"what_wrong": "CI fails randomly", "how_long": "3 months", "what_right": "zero-flake pipeline"}
→ {"friction_statement": "Friction: ..."}

POST /session/{id}/provocation/complete
→ {"phase": "expedition"}
```

### Expedition

```
POST /session/{id}/expedition/expand
  {"focus": "CI infrastructure"}  (focus is optional)
→ {"prompt": "...", "instruction": "..."} (standalone)
→ {"nodes_added": [...], "threshold": 0.5, "recommendation": "continue"} (llm/doorway)

POST /session/{id}/expedition/node
  {"label": "Jenkins is CI", "node_type": "ground", "significance": 0.9}
→ {"id": "...", "label": "...", "type": "ground", "significance": 0.9}

POST /session/{id}/expedition/assumption
  {"statement": "staging required", "classification": "convention", "evidence": ""}
→ {"statement": "...", "classification": "convention", "evidence": ""}
```

### Vantage

```
POST /session/{id}/vantage/consolidate
→ {"territory_covered": 5, "ground": 2, "convention": 2, "unknown": 1, ...}

POST /session/{id}/vantage/goal
  {"goal": "Eliminate CI flakiness"}
→ {"goal": "Eliminate CI flakiness"}

POST /session/{id}/vantage/complete
→ {"phase": "paths"}
```

### Paths

```
POST /session/{id}/paths/generate
→ {"paths": [{"path_id": "A", "label": "Maximum divergence", ...}, ...]}

POST /session/{id}/paths/commit
  {"path_id": "B"}
→ {"chosen_path": {...}, "phase": "receipt"}
```

### Receipt

```
POST /session/{id}/receipt
→ {"session_id": "...", "chain": {"chain_verified": true, ...}, ...}
```

### Session State

```
GET /session/{id}
→ Full session state as JSON
```

## Python API

```python
from main import (
    start_session, calibrate, complete_provocation,
    add_node, classify_assumption,
    consolidate, set_goal, complete_vantage,
    generate_paths, commit_path,
    generate_receipt,
)

session = start_session("Our deploys keep breaking")
calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
complete_provocation(session)

add_node(session, "Jenkins is CI", "ground", 0.9)
classify_assumption(session, "staging required", "convention")
session.advance_phase("vantage")

consolidate(session)
set_goal(session, "Eliminate CI flakiness")
complete_vantage(session)

paths = generate_paths(session)
commit_path(session, "B")

receipt = generate_receipt(session)
print(receipt["chain"]["chain_verified"])  # True
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

Apache License 2.0 · © 2026 Doorway
