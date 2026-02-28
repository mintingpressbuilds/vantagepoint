import pytest
from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import add_node, flag_significant, classify_assumption
from core.vantage import (
    consolidate, verify_discovery, set_goal,
    complete_vantage, return_to_expedition,
)
from core.mode import Mode


@pytest.fixture
def expedition_session(monkeypatch):
    """Session in expedition phase with some territory mapped."""
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)
    # Add territory
    n1 = add_node(session, "Jenkins is the CI tool", "ground", 0.9)
    n2 = add_node(session, "deploys must go through staging", "convention", 0.5)
    n3 = add_node(session, "root cause of flakiness", "unknown", 0.7)
    flag_significant(session, n3["id"])
    classify_assumption(session, "staging is required", "convention", "no evidence")
    classify_assumption(session, "Jenkins is stable", "ground", "confirmed in logs")
    # Advance to vantage
    session.advance_phase("vantage")
    return session


class TestConsolidate:
    def test_returns_summary(self, expedition_session):
        summary = consolidate(expedition_session)
        assert summary["territory_covered"] == 3
        assert summary["ground"] == 1
        assert summary["convention"] == 1
        assert summary["unknown"] == 1

    def test_includes_discoveries(self, expedition_session):
        summary = consolidate(expedition_session)
        assert len(summary["discoveries"]) == 1
        assert summary["discoveries"][0]["finding"] == "root cause of flakiness"

    def test_includes_assumptions(self, expedition_session):
        summary = consolidate(expedition_session)
        assert len(summary["assumptions"]) == 2

    def test_includes_threshold(self, expedition_session):
        summary = consolidate(expedition_session)
        assert summary["threshold"] == pytest.approx(0.333, abs=0.001)

    def test_stores_summary_on_session(self, expedition_session):
        consolidate(expedition_session)
        assert expedition_session.vantage_summary is not None
        assert expedition_session.vantage_summary["territory_covered"] == 3

    def test_adds_chain_entry(self, expedition_session):
        consolidate(expedition_session)
        entries = [e for e in expedition_session.chain_entries if e["phase"] == "vantage"]
        assert len(entries) == 1
        assert entries[0]["action"] == "consolidated"
        assert entries[0]["discoveries"] == 1
        assert entries[0]["assumptions"] == 2

    def test_recommendation_low_threshold(self, expedition_session):
        summary = consolidate(expedition_session)
        # threshold ~0.333 < 0.6
        assert "another expedition pass" in summary["recommendation"]

    def test_recommendation_high_threshold(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        session = start_session("test")
        calibrate(session, "w", "h", "r")
        complete_provocation(session)
        add_node(session, "fact1", "ground")
        add_node(session, "fact2", "ground")
        add_node(session, "fact3", "ground")
        session.advance_phase("vantage")
        summary = consolidate(session)
        # threshold 1.0 > 0.6
        assert "Set your goal" in summary["recommendation"]

    def test_verified_discoveries_count(self, expedition_session):
        summary = consolidate(expedition_session)
        assert summary["verified_discoveries"] == 0


class TestVerifyDiscovery:
    def test_marks_as_verified(self, expedition_session):
        result = verify_discovery(expedition_session, 0)
        assert result["verified"] is True
        assert expedition_session.discoveries[0]["verified"] is True

    def test_raises_for_invalid_index(self, expedition_session):
        with pytest.raises(IndexError, match="not found"):
            verify_discovery(expedition_session, 99)

    def test_verified_count_after_verify(self, expedition_session):
        verify_discovery(expedition_session, 0)
        summary = consolidate(expedition_session)
        assert summary["verified_discoveries"] == 1


class TestSetGoal:
    def test_sets_goal(self, expedition_session):
        set_goal(expedition_session, "Eliminate CI flakiness completely")
        assert expedition_session.goal == "Eliminate CI flakiness completely"

    def test_adds_chain_entry(self, expedition_session):
        set_goal(expedition_session, "Fix CI")
        entries = [e for e in expedition_session.chain_entries
                   if e.get("action") == "goal_set"]
        assert len(entries) == 1
        assert entries[0]["goal"] == "Fix CI"

    def test_returns_session(self, expedition_session):
        result = set_goal(expedition_session, "Fix CI")
        assert result is expedition_session


class TestCompleteVantage:
    def test_advances_to_paths(self, expedition_session):
        set_goal(expedition_session, "Fix CI")
        complete_vantage(expedition_session)
        assert expedition_session.phase == "paths"

    def test_returns_session(self, expedition_session):
        set_goal(expedition_session, "Fix CI")
        result = complete_vantage(expedition_session)
        assert result is expedition_session

    def test_fails_without_goal(self, expedition_session):
        with pytest.raises(ValueError, match="Must set goal"):
            complete_vantage(expedition_session)

    def test_cannot_complete_twice(self, expedition_session):
        set_goal(expedition_session, "Fix CI")
        complete_vantage(expedition_session)
        with pytest.raises(ValueError, match="Cannot go from paths"):
            complete_vantage(expedition_session)


class TestReturnToExpedition:
    def test_returns_to_expedition(self, expedition_session):
        return_to_expedition(expedition_session)
        assert expedition_session.phase == "expedition"

    def test_adds_chain_entry(self, expedition_session):
        return_to_expedition(expedition_session)
        entries = [e for e in expedition_session.chain_entries
                   if e.get("action") == "returned_to_expedition"]
        assert len(entries) == 1

    def test_returns_session(self, expedition_session):
        result = return_to_expedition(expedition_session)
        assert result is expedition_session

    def test_can_advance_to_vantage_again(self, expedition_session):
        return_to_expedition(expedition_session)
        assert expedition_session.phase == "expedition"
        expedition_session.advance_phase("vantage")
        assert expedition_session.phase == "vantage"
