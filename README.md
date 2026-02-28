# VantagePoint

**Structured thinking methodology as infrastructure. The process that externalizes how humans think before committing to execution.**

[![PyPI](https://img.shields.io/pypi/v/vantagepoint-doorway)](https://pypi.org/project/vantagepoint-doorway/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

-----

## The Problem

You have a hard problem. You open a chat with an AI. You type a question. You get an answer. Maybe it's good. Maybe it's not. You ask another question. Another answer. Twenty minutes later you have a pile of responses and no structured understanding of the territory you just explored.

No map of what you covered. No record of what you assumed versus what you confirmed. No separation between convention and physics. No honest accounting of where the gaps are. No verifiable receipt of the thinking process that led to your decision.

The problem isn't the AI's answers. The problem is there's no methodology around the AI. No structured process for how to think through a hard problem before committing to action. Every thinking tool gives you a blank page or a chatbox. Neither one guides the process of thinking itself.

## What VantagePoint Does

VantagePoint is a five-phase methodology implemented as callable Python functions. It externalizes the process of thinking — from initial friction through territory mapping through goal setting through path generation through a verifiable receipt of everything that happened.

It's not a chatbot. It's not a project management tool. It's the methodology that structures how you think before you commit to execution.

### Five Phases

|Phase          |What Happens                                                                                                                                                                                                                                              |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Provocation**|Start with friction — something wrong, not a goal. Three calibration questions establish the baseline. A verified friction statement emerges.                                                                                                             |
|**Expedition** |Territory expansion. Map what's known (ground), what's assumed (convention), and what's genuinely unknown. Significance detection flags what matters. Threshold sensor tells you when you've covered enough ground.                                       |
|**Vantage**    |Consolidation. Stand on what you've mapped and see what's visible. Discoveries verified. Assumptions classified. A goal emerges from the territory — not imposed on it.                                                                                   |
|**Paths**      |Three paths generated from your verified goal. Path A: maximum divergence — break every convention. Path B: informed hybrid — break conventions selectively. Path C: confirmed ground — maximum safety. Each with named assumptions, confidence, and risk.|
|**Receipt**    |Complete session receipt. Every phase, every discovery, every assumption, every path — chained and cryptographically verifiable. Proof of the thinking process, not just the conclusion.                                                                  |

### Three Operating Modes

VantagePoint works standalone, with any LLM, or with the full Doorway reasoning engine. Auto-detected from environment variables.

```bash
# Mode 1: Standalone — no env vars needed
# Pure methodology. You drive the analysis. Framework guides the process.

# Mode 2: Doorway — full geometric reasoning
DOORWAY_API_URL=http://localhost:8000

# Mode 3: LLM — AI-assisted, no geometric layer
ANTHROPIC_API_KEY=sk-ant-xxx
```

|Mode          |What Powers Analysis                                                                       |Best For                                                                                     |
|--------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
|**Standalone**|Your thinking. No AI.                                                                      |Researchers wanting the methodology without AI dependency. Teams who want structured process.|
|**Doorway**   |Full geometric reasoning at every step. Gap detection. Bridge building. Conflict detection.|Maximum depth. Every expedition step gets epistemic classification.                          |
|**LLM**       |Claude or other model assists territory expansion and analysis. No geometric layer.        |AI-assisted thinking without running a Doorway instance.                                     |

Priority chain: if `DOORWAY_API_URL` is set, Doorway mode activates and ignores `ANTHROPIC_API_KEY`. If only `ANTHROPIC_API_KEY` is set, LLM mode. Neither set, standalone.

## Install

```bash
pip install vantagepoint-doorway
```

## Quick Start

### CLI

```bash
# Start an interactive session
vantagepoint run "Our product development cycle takes too long"

# Start the API server
vantagepoint serve --port 8001
```

### Python

```python
from vantagepoint import (
    start_session, calibrate, complete_provocation,
    expand_territory, add_node, classify_assumption,
    consolidate, set_goal, complete_vantage,
    generate_paths, commit_path, generate_receipt,
)

# Phase 1: Provocation
session = start_session("Our product development cycle takes too long")
calibrate(session,
    what_wrong="Features take 3x longer than estimated consistently",
    how_long="Last 18 months since the team doubled",
    what_right="Predictable 2-week cycles with honest estimation"
)
complete_provocation(session)

# Phase 2: Expedition
expand_territory(session, focus="estimation process")
add_node(session, "Story points are fictional", "convention", significance=0.8)
add_node(session, "Scope grows after estimation", "ground", significance=0.9)
classify_assumption(session,
    statement="More engineers means faster delivery",
    classification="convention",
    evidence="Brooks's Law demonstrates the opposite"
)

# Phase 3: Vantage
summary = consolidate(session)
set_goal(session, "Achieve predictable 2-week cycles by addressing scope growth at source")
complete_vantage(session)

# Phase 4: Paths
paths = generate_paths(session)
# Path A: Break all conventions — no estimation, continuous flow
# Path B: Keep estimation, add scope-lock at kickoff
# Path C: Current process with smaller batches
commit_path(session, "B")

# Phase 5: Receipt
receipt = generate_receipt(session)
print(receipt["chain"]["chain_verified"])  # True
```

### API

```bash
# Start session
curl -X POST http://localhost:8001/session/start \
  -H "Content-Type: application/json" \
  -d '{"friction": "Our product development cycle takes too long"}'

# Returns: { "session_id": "abc-123", "mode": "standalone", "phase": "provocation" }

# Calibrate
curl -X POST http://localhost:8001/session/abc-123/calibrate \
  -H "Content-Type: application/json" \
  -d '{"what_wrong": "...", "how_long": "...", "what_right": "..."}'

# Continue through phases...
# POST /session/{id}/provocation/complete
# POST /session/{id}/expedition/expand
# POST /session/{id}/vantage/consolidate
# POST /session/{id}/vantage/goal
# POST /session/{id}/vantage/complete
# POST /session/{id}/paths/generate
# POST /session/{id}/paths/commit
# POST /session/{id}/receipt
```

## Why Start With Friction

Not a goal. Not a task. Friction.

Goals are premature. If you knew what to do, you wouldn't need a thinking methodology. Starting with a goal skips the territory mapping that reveals whether the goal is even the right one.

Friction is honest. Something is wrong. Something doesn't work. Something should be different. That observation is the seed. The methodology maps the territory around the friction, classifies what's assumed versus what's confirmed, and *then* a goal emerges from the territory. The goal is discovered, not declared.

This is why Phase 3 (Vantage) exists between expedition and paths. You don't go from mapping to acting. You stop, consolidate, verify what you found, and then set a goal informed by the territory. Most thinking tools skip this step. That's why most decisions are made on incomplete maps.

## The Territory Map

During expedition, VantagePoint builds a node-edge graph of the problem space. Every finding is classified:

|Node Type     |Meaning                                                                                                             |
|--------------|--------------------------------------------------------------------------------------------------------------------|
|**Ground**    |Confirmed. Verified by evidence. Safe to build on.                                                                  |
|**Convention**|Assumed. Everyone treats it as true, but the evidence is habit, not physics. These are where the opportunities hide.|
|**Unknown**   |Genuinely unexplored. The map has edges — this is where they are.                                                   |

The threshold sensor tracks ground coverage: how much of the territory has been mapped as confirmed ground versus convention and unknown. When the threshold recommends consolidation (>70% ground), it's time for the vantage phase. You can also consolidate earlier or continue exploring — the methodology guides, the human decides.

## Verifiable Thinking

Every VantagePoint session produces a cryptographic receipt via [xycore](https://pypi.org/project/xycore/) and [pruv](https://pypi.org/project/pruv/). The receipt is not a summary. It's the complete reasoning trail — every phase transition, every node added, every assumption classified, every path generated, every commitment made. Chained. Tamper-evident. Independently verifiable.

The receipt answers: what did we think, in what order, based on what evidence, with what assumptions, and what did we decide? Not reconstructed. Recorded as it happened.

## Configuration

```bash
# Doorway mode — full geometric reasoning (takes priority)
DOORWAY_API_URL=http://localhost:8000

# LLM mode — AI-assisted (used only if DOORWAY_API_URL not set)
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional — cloud chain sync and receipts
PRUV_API_KEY=pv_live_xxx
```

## Part of Doorway

VantagePoint is Product Two on the [Doorway](https://doorwayagi.com) platform.

|Package                                                             |What It Is                                              |
|--------------------------------------------------------------------|--------------------------------------------------------|
|[doorway-agi](https://pypi.org/project/doorway-agi/)                |AGI reasoning engine. Gap detection. Geometric bridging.|
|[vantagepoint-doorway](https://pypi.org/project/vantagepoint-doorway/)|This package. Structured thinking methodology.          |
|[xycore](https://pypi.org/project/xycore/)                          |Cryptographic chain primitive.                          |
|[pruv](https://pypi.org/project/pruv/)                              |Digital verification infrastructure.                    |

## License

Apache License 2.0 — see <LICENSE> for details.

(c) 2026 Doorway · [doorwayagi.com](https://doorwayagi.com)

Created by Luke H
