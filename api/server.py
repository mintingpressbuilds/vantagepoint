from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
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
    if not session:
        raise HTTPException(404, "Session not found")
    calibrate(session, req.what_wrong, req.how_long, req.what_right)
    return {"friction_statement": session.friction_statement}


@app.post("/session/{session_id}/provocation/complete")
async def api_complete_provocation(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    complete_provocation(session)
    return {"phase": session.phase}


@app.post("/session/{session_id}/expedition/expand")
async def api_expand(session_id: str, req: ExpandRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    result = expand_territory(session, req.focus)
    return result


@app.post("/session/{session_id}/expedition/node")
async def api_add_node(session_id: str, req: NodeRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return add_node(session, req.label, req.node_type, req.significance)


@app.post("/session/{session_id}/expedition/assumption")
async def api_classify(session_id: str, req: AssumptionRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return classify_assumption(session, req.statement, req.classification, req.evidence)


@app.post("/session/{session_id}/vantage/consolidate")
async def api_consolidate(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return consolidate(session)


@app.post("/session/{session_id}/vantage/goal")
async def api_set_goal(session_id: str, req: GoalRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    set_goal(session, req.goal)
    return {"goal": session.goal}


@app.post("/session/{session_id}/vantage/complete")
async def api_complete_vantage(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    complete_vantage(session)
    return {"phase": session.phase}


@app.post("/session/{session_id}/paths/generate")
async def api_generate_paths(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"paths": generate_paths(session)}


@app.post("/session/{session_id}/paths/commit")
async def api_commit(session_id: str, req: CommitRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    commit_path(session, req.path_id)
    return {"chosen_path": session.chosen_path, "phase": session.phase}


@app.post("/session/{session_id}/receipt")
async def api_receipt(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return generate_receipt(session)


@app.get("/session/{session_id}")
async def api_get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.to_dict()
