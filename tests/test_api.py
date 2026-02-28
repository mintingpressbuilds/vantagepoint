import pytest
from fastapi.testclient import TestClient
from api.server import app, sessions


@pytest.fixture(autouse=True)
def clear_sessions(monkeypatch):
    """Clear session store and ensure standalone mode for each test."""
    sessions.clear()
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PRUV_API_KEY", raising=False)


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["engine"] == "vantagepoint"
        assert data["mode"] == "standalone"


class TestSessionStart:
    def test_start_session(self, client):
        resp = client.post("/session/start", json={"friction": "deploys break"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["mode"] == "standalone"
        assert data["phase"] == "provocation"

    def test_session_stored(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        assert sid in sessions


class TestCalibrate:
    def test_calibrate(self, client):
        resp = client.post("/session/start", json={"friction": "deploys break"})
        sid = resp.json()["session_id"]
        resp = client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "CI flaky", "how_long": "3 months", "what_right": "stable CI"
        })
        assert resp.status_code == 200
        assert "friction_statement" in resp.json()
        assert "deploys break" in resp.json()["friction_statement"]

    def test_calibrate_missing_session(self, client):
        resp = client.post("/session/nonexistent/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        assert resp.status_code == 404


class TestProvocationComplete:
    def test_complete_provocation(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        resp = client.post(f"/session/{sid}/provocation/complete")
        assert resp.status_code == 200
        assert resp.json()["phase"] == "expedition"


class TestExpedition:
    @pytest.fixture
    def expedition_session(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        client.post(f"/session/{sid}/provocation/complete")
        return sid

    def test_expand_standalone(self, client, expedition_session):
        resp = client.post(f"/session/{expedition_session}/expedition/expand",
                          json={"focus": None})
        assert resp.status_code == 200
        data = resp.json()
        assert "prompt" in data
        assert "instruction" in data

    def test_add_node(self, client, expedition_session):
        resp = client.post(f"/session/{expedition_session}/expedition/node",
                          json={"label": "fact", "node_type": "ground", "significance": 0.9})
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] == "fact"
        assert data["type"] == "ground"

    def test_classify_assumption(self, client, expedition_session):
        resp = client.post(f"/session/{expedition_session}/expedition/assumption",
                          json={"statement": "assumed true", "classification": "convention"})
        assert resp.status_code == 200
        assert resp.json()["classification"] == "convention"


class TestVantage:
    @pytest.fixture
    def vantage_session(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        client.post(f"/session/{sid}/provocation/complete")
        client.post(f"/session/{sid}/expedition/node",
                   json={"label": "fact", "node_type": "ground"})
        sessions[sid].advance_phase("vantage")
        return sid

    def test_consolidate(self, client, vantage_session):
        resp = client.post(f"/session/{vantage_session}/vantage/consolidate")
        assert resp.status_code == 200
        assert "territory_covered" in resp.json()

    def test_set_goal(self, client, vantage_session):
        resp = client.post(f"/session/{vantage_session}/vantage/goal",
                          json={"goal": "Fix everything"})
        assert resp.status_code == 200
        assert resp.json()["goal"] == "Fix everything"

    def test_complete_vantage(self, client, vantage_session):
        client.post(f"/session/{vantage_session}/vantage/goal",
                   json={"goal": "Fix it"})
        resp = client.post(f"/session/{vantage_session}/vantage/complete")
        assert resp.status_code == 200
        assert resp.json()["phase"] == "paths"


class TestPaths:
    @pytest.fixture
    def paths_session(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        client.post(f"/session/{sid}/provocation/complete")
        client.post(f"/session/{sid}/expedition/node",
                   json={"label": "fact", "node_type": "ground"})
        sessions[sid].advance_phase("vantage")
        client.post(f"/session/{sid}/vantage/goal", json={"goal": "Fix it"})
        client.post(f"/session/{sid}/vantage/complete")
        return sid

    def test_generate_paths(self, client, paths_session):
        resp = client.post(f"/session/{paths_session}/paths/generate")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        assert len(paths) == 3
        assert paths[0]["path_id"] == "A"

    def test_commit_path(self, client, paths_session):
        client.post(f"/session/{paths_session}/paths/generate")
        resp = client.post(f"/session/{paths_session}/paths/commit",
                          json={"path_id": "B"})
        assert resp.status_code == 200
        assert resp.json()["phase"] == "receipt"


class TestReceipt:
    @pytest.fixture
    def receipt_session(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "x", "how_long": "y", "what_right": "z"
        })
        client.post(f"/session/{sid}/provocation/complete")
        client.post(f"/session/{sid}/expedition/node",
                   json={"label": "fact", "node_type": "ground"})
        sessions[sid].advance_phase("vantage")
        client.post(f"/session/{sid}/vantage/goal", json={"goal": "Fix it"})
        client.post(f"/session/{sid}/vantage/complete")
        client.post(f"/session/{sid}/paths/generate")
        client.post(f"/session/{sid}/paths/commit", json={"path_id": "A"})
        return sid

    def test_generate_receipt(self, client, receipt_session):
        resp = client.post(f"/session/{receipt_session}/receipt")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == receipt_session
        assert data["goal"] == "Fix it"
        assert data["chosen_path"] == "A"
        assert data["chain"]["chain_verified"] is True


class TestGetSession:
    def test_get_session(self, client):
        resp = client.post("/session/start", json={"friction": "test"})
        sid = resp.json()["session_id"]
        resp = client.get(f"/session/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sid
        assert data["friction"] == "test"

    def test_get_missing_session(self, client):
        resp = client.get("/session/nonexistent")
        assert resp.status_code == 404


class TestFullSessionFlow:
    """End-to-end: provocation → expedition → vantage → paths → receipt via API."""

    def test_full_flow(self, client):
        # Start
        resp = client.post("/session/start", json={"friction": "deploys break"})
        sid = resp.json()["session_id"]
        assert resp.json()["phase"] == "provocation"

        # Calibrate
        resp = client.post(f"/session/{sid}/calibrate", json={
            "what_wrong": "CI flaky", "how_long": "3 months", "what_right": "stable"
        })
        assert "friction_statement" in resp.json()

        # Complete provocation
        resp = client.post(f"/session/{sid}/provocation/complete")
        assert resp.json()["phase"] == "expedition"

        # Add nodes
        client.post(f"/session/{sid}/expedition/node",
                   json={"label": "Jenkins", "node_type": "ground", "significance": 0.9})
        client.post(f"/session/{sid}/expedition/node",
                   json={"label": "staging", "node_type": "convention"})
        client.post(f"/session/{sid}/expedition/assumption",
                   json={"statement": "staging needed", "classification": "convention"})

        # Advance to vantage
        sessions[sid].advance_phase("vantage")

        # Consolidate + goal
        resp = client.post(f"/session/{sid}/vantage/consolidate")
        assert resp.json()["territory_covered"] == 2

        resp = client.post(f"/session/{sid}/vantage/goal",
                          json={"goal": "Fix CI"})
        assert resp.json()["goal"] == "Fix CI"

        resp = client.post(f"/session/{sid}/vantage/complete")
        assert resp.json()["phase"] == "paths"

        # Generate + commit
        resp = client.post(f"/session/{sid}/paths/generate")
        assert len(resp.json()["paths"]) == 3

        resp = client.post(f"/session/{sid}/paths/commit",
                          json={"path_id": "C"})
        assert resp.json()["phase"] == "receipt"

        # Receipt
        resp = client.post(f"/session/{sid}/receipt")
        receipt = resp.json()
        assert receipt["session_id"] == sid
        assert receipt["mode"] == "standalone"
        assert receipt["goal"] == "Fix CI"
        assert receipt["chosen_path"] == "C"
        assert receipt["chain"]["chain_verified"] is True
        assert len(receipt["chain_entries"]) > 0
