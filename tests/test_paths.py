import pytest
from unittest.mock import patch
from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import add_node, classify_assumption
from core.vantage import set_goal, complete_vantage
from core.paths import generate_paths, commit_path
from core.mode import Mode


def _build_session_to_paths(monkeypatch, mode="standalone"):
    """Helper to build a session through to the paths phase."""
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    if mode == "llm":
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    elif mode == "doorway":
        monkeypatch.setenv("DOORWAY_API_URL", "http://localhost:8000")

    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)
    add_node(session, "Jenkins is CI", "ground")
    add_node(session, "staging required", "convention")
    classify_assumption(session, "staging is required", "convention", "no evidence")
    classify_assumption(session, "Jenkins is stable", "ground", "logs confirm")
    session.advance_phase("vantage")
    set_goal(session, "Eliminate CI flakiness")
    complete_vantage(session)
    return session


@pytest.fixture
def standalone_paths_session(monkeypatch):
    return _build_session_to_paths(monkeypatch, "standalone")


@pytest.fixture
def llm_paths_session(monkeypatch):
    return _build_session_to_paths(monkeypatch, "llm")


@pytest.fixture
def doorway_paths_session(monkeypatch):
    return _build_session_to_paths(monkeypatch, "doorway")


class TestGeneratePathsStandalone:
    def test_generates_three_paths(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        assert len(paths) == 3

    def test_path_ids(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        assert paths[0]["path_id"] == "A"
        assert paths[1]["path_id"] == "B"
        assert paths[2]["path_id"] == "C"

    def test_path_labels(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        assert paths[0]["label"] == "Maximum divergence"
        assert paths[1]["label"] == "Informed hybrid"
        assert paths[2]["label"] == "Confirmed ground"

    def test_path_risk_levels(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        assert paths[0]["risk"] == "high"
        assert paths[1]["risk"] == "moderate"
        assert paths[2]["risk"] == "low"

    def test_standalone_status(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        for p in paths:
            assert p["status"] == "STANDALONE"

    def test_path_a_includes_conventions(self, standalone_paths_session):
        paths = generate_paths(standalone_paths_session)
        assert "staging is required" in paths[0]["assumptions"]

    def test_stores_paths_on_session(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        assert len(standalone_paths_session.paths) == 3

    def test_adds_chain_entry(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        entries = [e for e in standalone_paths_session.chain_entries
                   if e.get("action") == "paths_generated"]
        assert len(entries) == 1
        assert entries[0]["count"] == 3

    def test_fails_without_goal(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("test")
        calibrate(session, "w", "h", "r")
        complete_provocation(session)
        session.advance_phase("vantage")
        session.advance_phase("paths")
        with pytest.raises(ValueError, match="No goal set"):
            generate_paths(session)


class TestGeneratePathsLLM:
    @patch("core.paths.call_llm")
    def test_calls_llm(self, mock_llm, llm_paths_session):
        mock_llm.return_value = {"answer": "Three approaches analyzed", "success": True}
        paths = generate_paths(llm_paths_session)
        mock_llm.assert_called_once()
        assert len(paths) == 3

    @patch("core.paths.call_llm")
    def test_llm_status(self, mock_llm, llm_paths_session):
        mock_llm.return_value = {"answer": "Analysis", "success": True}
        paths = generate_paths(llm_paths_session)
        for p in paths:
            assert p["status"] == "LLM"

    @patch("core.paths.call_llm")
    def test_llm_confidence_ordering(self, mock_llm, llm_paths_session):
        mock_llm.return_value = {"answer": "Analysis", "success": True}
        paths = generate_paths(llm_paths_session)
        assert paths[0]["confidence"] < paths[1]["confidence"] < paths[2]["confidence"]

    @patch("core.paths.call_llm")
    def test_path_a_has_conventions(self, mock_llm, llm_paths_session):
        mock_llm.return_value = {"answer": "Analysis", "success": True}
        paths = generate_paths(llm_paths_session)
        assert "staging is required" in paths[0]["assumptions"]


class TestGeneratePathsDoorway:
    def _mock_doorway_result(self, answer="test", gap_score=0.3, status="GROUND"):
        return {
            "status": status,
            "content": {"answer": answer, "confidence": 0.8},
            "structure": {"closest_shape": "triangle", "gap_score": gap_score},
            "bridge": None,
            "conflict": {},
        }

    @patch("core.paths.call_doorway")
    def test_calls_doorway_three_times(self, mock_doorway, doorway_paths_session):
        mock_doorway.return_value = self._mock_doorway_result()
        paths = generate_paths(doorway_paths_session)
        assert mock_doorway.call_count == 3
        assert len(paths) == 3

    @patch("core.paths.call_doorway")
    def test_path_a_high_risk(self, mock_doorway, doorway_paths_session):
        mock_doorway.return_value = self._mock_doorway_result()
        paths = generate_paths(doorway_paths_session)
        assert paths[0]["risk"] == "high"
        assert paths[0]["label"] == "Maximum divergence"

    @patch("core.paths.call_doorway")
    def test_path_c_low_risk(self, mock_doorway, doorway_paths_session):
        mock_doorway.return_value = self._mock_doorway_result()
        paths = generate_paths(doorway_paths_session)
        assert paths[2]["risk"] == "low"
        assert paths[2]["label"] == "Confirmed ground"

    @patch("core.paths.call_doorway")
    def test_doorway_result_stored(self, mock_doorway, doorway_paths_session):
        mock_doorway.return_value = self._mock_doorway_result()
        paths = generate_paths(doorway_paths_session)
        for p in paths:
            assert "doorway_result" in p

    @patch("core.paths.call_doorway")
    def test_bridge_assumptions_extracted(self, mock_doorway, doorway_paths_session):
        result_with_bridge = {
            "status": "BRIDGE",
            "content": {"answer": "hybrid approach", "confidence": 0.6},
            "structure": {"closest_shape": "bridge", "gap_score": 0.4},
            "bridge": {"assumptions": ["runners stable"], "confidence": 0.7},
            "conflict": {},
        }
        mock_doorway.return_value = result_with_bridge
        paths = generate_paths(doorway_paths_session)
        # Path A and B should extract bridge assumptions
        assert paths[0]["assumptions"] == ["runners stable"]
        assert paths[0]["confidence"] == 0.7


class TestCommitPath:
    def test_commits_path(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        commit_path(standalone_paths_session, "B")
        assert standalone_paths_session.chosen_path["path_id"] == "B"
        assert standalone_paths_session.chosen_path["label"] == "Informed hybrid"

    def test_advances_to_receipt(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        commit_path(standalone_paths_session, "A")
        assert standalone_paths_session.phase == "receipt"

    def test_adds_chain_entry(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        commit_path(standalone_paths_session, "C")
        entries = [e for e in standalone_paths_session.chain_entries
                   if e.get("action") == "path_committed"]
        assert len(entries) == 1
        assert entries[0]["path_id"] == "C"
        assert entries[0]["label"] == "Confirmed ground"

    def test_returns_session(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        result = commit_path(standalone_paths_session, "A")
        assert result is standalone_paths_session

    def test_fails_for_invalid_path(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        with pytest.raises(ValueError, match="Path X not found"):
            commit_path(standalone_paths_session, "X")

    def test_cannot_commit_without_generating(self, standalone_paths_session):
        with pytest.raises(ValueError, match="not found"):
            commit_path(standalone_paths_session, "A")

    def test_cannot_commit_twice(self, standalone_paths_session):
        generate_paths(standalone_paths_session)
        commit_path(standalone_paths_session, "A")
        # Session is now in receipt phase, advance_phase will fail
        with pytest.raises(ValueError):
            commit_path(standalone_paths_session, "B")
