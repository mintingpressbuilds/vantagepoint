# CLAUDE.md — VantagePoint

## What This Repo Is

A structured thinking methodology as an installable Python package. Five phases: provocation, expedition, vantage, paths, receipt. The methodology that externalizes how humans think before committing to execution. No frontend — this is infrastructure.

Powered by Doorway. Built on xycore. Receipted by pruv. Works completely standalone.

## Before Writing Any Code

Read `BLUEPRINT.md` completely. It is the build specification. Every phase, every verification gate, every interface contract is defined there. Follow it exactly. Build in the exact sequence specified. Do not skip phases. Do not combine phases.

## Build Order

Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7. Each phase confirmed before the next begins.

## Three Operating Modes

VantagePoint auto-detects its mode from environment variables. Priority chain:

1. DOORWAY_API_URL present → **Doorway mode** (full geometric reasoning, ignores ANTHROPIC_API_KEY)
1. ANTHROPIC_API_KEY only → **LLM mode** (AI-assisted, no geometric layer)
1. Neither → **Standalone mode** (pure methodology, user drives all analysis)

Every function in the package must work in all three modes. The mode determines what powers the analysis, not what analysis is available. All five phases run in every mode.

## Critical Rules

- VantagePoint is a package, not a frontend. No React. No HTML. No UI components. The dashboard lives in doorway-platform.
- The methodology is the product. Doorway is an optional layer underneath.
- Every session step is chained via xy_wrap. The receipt is not a log — it is the complete reasoning trail, cryptographically verifiable.
- xy_wrap api_key must be conditional — same pattern as doorway. Local dev runs with zero network dependency.
- Doorway API calls use the interface contract from the doorway BLUEPRINT: POST /run returns { status, content, structure, bridge, conflict, chain, receipt }.
- Nothing executes without explicit user commitment at each phase transition. The methodology guides — the human decides.
- Export the pruv class as CloudClient, not PruvClient.

## Stack

- Python 3.11+
- anthropic (LLM mode only)
- xycore (chain primitive — imported via pruv)
- pruv (xy_wrap, receipts, cloud sync)
- fastapi + uvicorn (API server)
- httpx (doorway API client)
- pytest (testing)

## Definition of Done

All checks in BLUEPRINT.md must pass. The package must work in all three modes. The API server must respond correctly. README must document all three modes, CLI, and API.
