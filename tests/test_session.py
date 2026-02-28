import pytest
from core.session import VPSession
from core.mode import Mode


class TestVPSessionInit:
    def test_creates_with_id(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.id is not None
        assert len(session.id) == 36  # UUID format

    def test_starts_in_provocation_phase(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.phase == "provocation"

    def test_stores_friction(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession(friction="nothing works")
        assert session.friction == "nothing works"

    def test_detects_standalone_mode(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.mode == Mode.STANDALONE

    def test_detects_llm_mode(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        session = VPSession()
        assert session.mode == Mode.LLM

    def test_detects_doorway_mode(self, monkeypatch):
        monkeypatch.setenv("DOORWAY_API_URL", "http://localhost:8000")
        session = VPSession()
        assert session.mode == Mode.DOORWAY

    def test_initializes_empty_territory(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.territory == {"nodes": [], "edges": [], "clusters": []}

    def test_initializes_empty_collections(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.discoveries == []
        assert session.assumptions == []
        assert session.paths == []
        assert session.chain_entries == []
        assert session.doorway_results == []

    def test_initializes_threshold_zero(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.threshold == 0.0

    def test_has_created_at_timestamp(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession()
        assert session.created_at is not None
        assert "T" in session.created_at  # ISO format


class TestPhaseTransitions:
    @pytest.fixture
    def session(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        return VPSession()

    def test_provocation_to_expedition(self, session):
        session.advance_phase("expedition")
        assert session.phase == "expedition"

    def test_expedition_to_vantage(self, session):
        session.advance_phase("expedition")
        session.advance_phase("vantage")
        assert session.phase == "vantage"

    def test_vantage_to_paths(self, session):
        session.advance_phase("expedition")
        session.advance_phase("vantage")
        session.advance_phase("paths")
        assert session.phase == "paths"

    def test_paths_to_receipt(self, session):
        session.advance_phase("expedition")
        session.advance_phase("vantage")
        session.advance_phase("paths")
        session.advance_phase("receipt")
        assert session.phase == "receipt"

    def test_cannot_skip_phases(self, session):
        with pytest.raises(ValueError, match="Cannot go from provocation to vantage"):
            session.advance_phase("vantage")

    def test_cannot_go_backwards(self, session):
        session.advance_phase("expedition")
        with pytest.raises(ValueError, match="Cannot go from expedition to provocation"):
            session.advance_phase("provocation")

    def test_cannot_advance_to_invalid_phase(self, session):
        with pytest.raises(ValueError):
            session.advance_phase("nonexistent")


class TestToDict:
    def test_contains_all_fields(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = VPSession(friction="test friction")
        d = session.to_dict()
        assert d["id"] == session.id
        assert d["mode"] == "standalone"
        assert d["phase"] == "provocation"
        assert d["friction"] == "test friction"
        assert d["friction_statement"] is None
        assert d["calibration"] == {}
        assert d["territory"] == {"nodes": [], "edges": [], "clusters": []}
        assert d["discoveries"] == []
        assert d["assumptions"] == []
        assert d["threshold"] == 0.0
        assert d["goal"] is None
        assert d["vantage_summary"] is None
        assert d["paths"] == []
        assert d["chosen_path"] is None
        assert d["chain_entries"] == []
