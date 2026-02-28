import pytest
from core.provocation import start_session, calibrate, complete_provocation
from core.mode import Mode


class TestStartSession:
    def test_creates_session_with_friction(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("our deploys keep breaking")
        assert session.friction == "our deploys keep breaking"

    def test_session_starts_in_provocation(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("test friction")
        assert session.phase == "provocation"

    def test_session_has_id(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("test friction")
        assert session.id is not None
        assert len(session.id) == 36

    def test_session_detects_mode(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("test")
        assert session.mode == Mode.STANDALONE


class TestCalibrate:
    @pytest.fixture
    def session(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        return start_session("our deploys keep breaking")

    def test_stores_calibration(self, session):
        calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
        assert session.calibration["what_wrong"] == "CI fails randomly"
        assert session.calibration["how_long"] == "3 months"
        assert session.calibration["what_right"] == "zero-flake pipeline"

    def test_builds_friction_statement(self, session):
        calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
        assert "Friction: our deploys keep breaking" in session.friction_statement
        assert "Specifically: CI fails randomly" in session.friction_statement
        assert "Duration: 3 months" in session.friction_statement
        assert "Target state: zero-flake pipeline" in session.friction_statement

    def test_adds_chain_entry(self, session):
        calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
        assert len(session.chain_entries) == 1
        entry = session.chain_entries[0]
        assert entry["phase"] == "provocation"
        assert entry["action"] == "calibrated"
        assert entry["data"] == session.calibration
        assert entry["output"] == session.friction_statement

    def test_returns_session(self, session):
        result = calibrate(session, "CI fails", "1 month", "stable CI")
        assert result is session


class TestCompleteProvocation:
    @pytest.fixture
    def calibrated_session(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("friction")
        calibrate(session, "wrong", "long", "right")
        return session

    def test_advances_to_expedition(self, calibrated_session):
        complete_provocation(calibrated_session)
        assert calibrated_session.phase == "expedition"

    def test_returns_session(self, calibrated_session):
        result = complete_provocation(calibrated_session)
        assert result is calibrated_session

    def test_fails_without_calibration(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("uncalibrated")
        with pytest.raises(ValueError, match="Must calibrate before completing provocation"):
            complete_provocation(session)

    def test_cannot_complete_twice(self, calibrated_session):
        complete_provocation(calibrated_session)
        with pytest.raises(ValueError, match="Cannot go from expedition"):
            complete_provocation(calibrated_session)
