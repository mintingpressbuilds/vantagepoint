import pytest
from unittest.mock import patch, MagicMock
from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import (
    expand_territory, add_node, add_edge, flag_significant,
    classify_assumption, _calculate_threshold, _build_expansion_prompt,
    _extract_territory_from_doorway, _extract_territory_from_llm,
)
from core.mode import Mode


@pytest.fixture
def standalone_session(monkeypatch):
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)
    return session


@pytest.fixture
def llm_session(monkeypatch):
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)
    return session


@pytest.fixture
def doorway_session(monkeypatch):
    monkeypatch.setenv("DOORWAY_API_URL", "http://localhost:8000")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)
    return session


class TestExpandTerritoryStandalone:
    def test_returns_prompt_and_instruction(self, standalone_session):
        result = expand_territory(standalone_session)
        assert "prompt" in result
        assert "instruction" in result
        assert "add_nodes()" in result["instruction"]

    def test_prompt_includes_friction_statement(self, standalone_session):
        result = expand_territory(standalone_session)
        assert "our deploys keep breaking" in result["prompt"]

    def test_prompt_includes_focus_when_given(self, standalone_session):
        result = expand_territory(standalone_session, focus="CI infrastructure")
        assert "CI infrastructure" in result["prompt"]

    def test_does_not_modify_territory(self, standalone_session):
        expand_territory(standalone_session)
        assert len(standalone_session.territory["nodes"]) == 0


class TestExpandTerritoryLLM:
    @patch("core.expedition.call_llm")
    def test_calls_llm_and_adds_node(self, mock_llm, llm_session):
        mock_llm.return_value = {"answer": "The CI system uses shared runners", "success": True}
        result = expand_territory(llm_session)
        assert len(result["nodes_added"]) == 1
        assert result["nodes_added"][0]["type"] == "convention"
        assert len(llm_session.territory["nodes"]) == 1

    @patch("core.expedition.call_llm")
    def test_updates_threshold(self, mock_llm, llm_session):
        mock_llm.return_value = {"answer": "Analysis result", "success": True}
        result = expand_territory(llm_session)
        assert "threshold" in result
        assert result["threshold"] == 0.0  # convention node, no ground

    @patch("core.expedition.call_llm")
    def test_adds_chain_entry(self, mock_llm, llm_session):
        mock_llm.return_value = {"answer": "Analysis", "success": True}
        expand_territory(llm_session)
        expedition_entries = [e for e in llm_session.chain_entries if e["phase"] == "expedition"]
        assert len(expedition_entries) == 1
        assert expedition_entries[0]["action"] == "territory_expanded"


class TestExpandTerritoryDoorway:
    @patch("core.expedition.call_doorway")
    def test_calls_doorway_and_parses_result(self, mock_doorway, doorway_session):
        mock_doorway.return_value = {
            "status": "GROUND",
            "content": {"answer": "CI runners are shared across teams"},
            "structure": {"closest_shape": "triangle", "gap_score": 0.2},
            "bridge": None,
            "conflict": {},
        }
        result = expand_territory(doorway_session)
        assert len(result["nodes_added"]) == 1
        assert result["nodes_added"][0]["type"] == "ground"
        assert result["nodes_added"][0]["gap_score"] == 0.2

    @patch("core.expedition.call_doorway")
    def test_stores_doorway_result(self, mock_doorway, doorway_session):
        mock_doorway.return_value = {
            "status": "GROUND",
            "content": {"answer": "test"},
            "structure": {"closest_shape": "triangle", "gap_score": 0.3},
            "bridge": None, "conflict": {},
        }
        expand_territory(doorway_session)
        assert len(doorway_session.doorway_results) == 1

    @patch("core.expedition.call_doorway")
    def test_parses_bridge_assumptions(self, mock_doorway, doorway_session):
        mock_doorway.return_value = {
            "status": "BRIDGE",
            "content": {"answer": "Shared runners assumed stable"},
            "structure": {"closest_shape": "bridge", "gap_score": 0.5},
            "bridge": {"assumptions": ["runners are stable", "no contention"], "confidence": 0.6},
            "conflict": {},
        }
        result = expand_territory(doorway_session)
        # 1 main node + 2 assumption nodes
        assert len(result["nodes_added"]) == 3
        assert result["nodes_added"][0]["type"] == "convention"  # BRIDGE -> convention
        assert result["nodes_added"][1]["type"] == "convention"
        assert result["nodes_added"][2]["type"] == "convention"
        # 2 edges from main to assumptions
        assert len(result["edges_added"]) == 2
        assert result["edges_added"][0]["label"] == "assumes"

    @patch("core.expedition.call_doorway")
    def test_parses_conflict(self, mock_doorway, doorway_session):
        mock_doorway.return_value = {
            "status": "CONFLICT",
            "content": {"answer": "Contradictory evidence"},
            "structure": {"closest_shape": "unknown", "gap_score": 0.8},
            "bridge": None,
            "conflict": {"conflict": True, "message": "Physics vs convention clash"},
        }
        result = expand_territory(doorway_session)
        # 1 main node + 1 conflict node
        assert len(result["nodes_added"]) == 2
        assert result["nodes_added"][1]["type"] == "unknown"
        assert result["nodes_added"][1]["significance"] == 0.9
        assert len(result["edges_added"]) == 1
        assert result["edges_added"][0]["label"] == "conflicts"

    @patch("core.expedition.call_doorway")
    def test_recommendation_consolidate(self, mock_doorway, doorway_session):
        mock_doorway.return_value = {
            "status": "GROUND",
            "content": {"answer": "confirmed fact"},
            "structure": {"closest_shape": "triangle", "gap_score": 0.1},
            "bridge": None, "conflict": {},
        }
        result = expand_territory(doorway_session)
        # 1 ground node out of 1 = threshold 1.0 > 0.7
        assert result["recommendation"] == "consolidate"


class TestAddNode:
    def test_adds_node_to_territory(self, standalone_session):
        node = add_node(standalone_session, "CI uses Jenkins", "ground", 0.9)
        assert node["label"] == "CI uses Jenkins"
        assert node["type"] == "ground"
        assert node["significance"] == 0.9
        assert len(node["id"]) == 8
        assert len(standalone_session.territory["nodes"]) == 1

    def test_default_significance(self, standalone_session):
        node = add_node(standalone_session, "test", "convention")
        assert node["significance"] == 0.5

    def test_updates_threshold(self, standalone_session):
        add_node(standalone_session, "fact1", "ground")
        assert standalone_session.threshold == 1.0
        add_node(standalone_session, "assumption1", "convention")
        assert standalone_session.threshold == 0.5


class TestAddEdge:
    def test_adds_edge(self, standalone_session):
        n1 = add_node(standalone_session, "A", "ground")
        n2 = add_node(standalone_session, "B", "convention")
        edge = add_edge(standalone_session, n1["id"], n2["id"], "causes")
        assert edge["source"] == n1["id"]
        assert edge["target"] == n2["id"]
        assert edge["label"] == "causes"
        assert len(standalone_session.territory["edges"]) == 1

    def test_default_label(self, standalone_session):
        n1 = add_node(standalone_session, "A", "ground")
        n2 = add_node(standalone_session, "B", "ground")
        edge = add_edge(standalone_session, n1["id"], n2["id"])
        assert edge["label"] == "related"


class TestFlagSignificant:
    def test_flags_node(self, standalone_session):
        node = add_node(standalone_session, "important thing", "convention", 0.3)
        result = flag_significant(standalone_session, node["id"])
        assert result["significance"] == 1.0

    def test_adds_discovery(self, standalone_session):
        node = add_node(standalone_session, "important thing", "convention")
        flag_significant(standalone_session, node["id"])
        assert len(standalone_session.discoveries) == 1
        assert standalone_session.discoveries[0]["finding"] == "important thing"
        assert standalone_session.discoveries[0]["verified"] is False
        assert standalone_session.discoveries[0]["node_id"] == node["id"]

    def test_raises_for_unknown_node(self, standalone_session):
        with pytest.raises(ValueError, match="not found"):
            flag_significant(standalone_session, "nonexistent")


class TestClassifyAssumption:
    def test_classifies_as_ground(self, standalone_session):
        result = classify_assumption(
            standalone_session, "Jenkins is the CI tool", "ground", "confirmed in docs"
        )
        assert result["statement"] == "Jenkins is the CI tool"
        assert result["classification"] == "ground"
        assert result["evidence"] == "confirmed in docs"
        assert len(standalone_session.assumptions) == 1

    def test_classifies_as_convention(self, standalone_session):
        result = classify_assumption(
            standalone_session, "deploys must go through staging", "convention"
        )
        assert result["classification"] == "convention"
        assert result["evidence"] == ""

    def test_adds_chain_entry(self, standalone_session):
        classify_assumption(standalone_session, "test", "ground")
        entries = [e for e in standalone_session.chain_entries if e["action"] == "assumption_classified"]
        assert len(entries) == 1
        assert entries[0]["phase"] == "expedition"


class TestCalculateThreshold:
    def test_empty_returns_zero(self, standalone_session):
        assert _calculate_threshold(standalone_session) == 0.0

    def test_all_ground(self, standalone_session):
        add_node(standalone_session, "a", "ground")
        add_node(standalone_session, "b", "ground")
        assert _calculate_threshold(standalone_session) == 1.0

    def test_mixed(self, standalone_session):
        add_node(standalone_session, "a", "ground")
        add_node(standalone_session, "b", "convention")
        add_node(standalone_session, "c", "unknown")
        assert _calculate_threshold(standalone_session) == pytest.approx(0.333, abs=0.001)

    def test_no_ground(self, standalone_session):
        add_node(standalone_session, "a", "convention")
        add_node(standalone_session, "b", "unknown")
        assert _calculate_threshold(standalone_session) == 0.0


class TestBuildExpansionPrompt:
    def test_includes_friction(self, standalone_session):
        prompt = _build_expansion_prompt(standalone_session, None)
        assert "our deploys keep breaking" in prompt

    def test_includes_focus(self, standalone_session):
        prompt = _build_expansion_prompt(standalone_session, "networking")
        assert "networking" in prompt

    def test_includes_existing_territory(self, standalone_session):
        add_node(standalone_session, "known fact", "ground")
        add_node(standalone_session, "assumed thing", "convention")
        prompt = _build_expansion_prompt(standalone_session, None)
        assert "known fact" in prompt
        assert "assumed thing" in prompt
        assert "Already mapped" in prompt


class TestExtractTerritoryFromDoorway:
    def test_ground_status(self, standalone_session):
        result = {
            "status": "GROUND",
            "content": {"answer": "Verified fact"},
            "structure": {"closest_shape": "triangle", "gap_score": 0.1},
            "bridge": None, "conflict": {},
        }
        nodes, edges = _extract_territory_from_doorway(result, standalone_session)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "ground"
        assert nodes[0]["significance"] == pytest.approx(0.9)

    def test_provisional_status(self, standalone_session):
        result = {
            "status": "PROVISIONAL",
            "content": {"answer": "Not yet verified"},
            "structure": {"closest_shape": "unknown", "gap_score": 0.7},
            "bridge": None, "conflict": {},
        }
        nodes, edges = _extract_territory_from_doorway(result, standalone_session)
        assert nodes[0]["type"] == "unknown"


class TestExtractTerritoryFromLLM:
    def test_creates_convention_node(self, standalone_session):
        result = {"answer": "Some LLM analysis text"}
        nodes, edges = _extract_territory_from_llm(result, standalone_session)
        assert len(nodes) == 1
        assert nodes[0]["type"] == "convention"
        assert nodes[0]["significance"] == 0.5
        assert edges == []

    def test_truncates_long_text(self, standalone_session):
        result = {"answer": "x" * 200}
        nodes, _ = _extract_territory_from_llm(result, standalone_session)
        assert len(nodes[0]["label"]) == 120
