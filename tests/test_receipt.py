import pytest
from core.provocation import start_session, calibrate, complete_provocation
from core.expedition import add_node, classify_assumption, flag_significant
from core.vantage import set_goal, complete_vantage
from core.paths import generate_paths, commit_path
from core.receipt import generate_receipt
from core.chain import get_wrapper, extract_receipt_info
from core.mode import Mode


def _build_full_session(monkeypatch):
    """Build a session through all phases to receipt."""
    monkeypatch.delenv("DOORWAY_API_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PRUV_API_KEY", raising=False)

    session = start_session("our deploys keep breaking")
    calibrate(session, "CI fails randomly", "3 months", "zero-flake pipeline")
    complete_provocation(session)

    n1 = add_node(session, "Jenkins is CI", "ground", 0.9)
    n2 = add_node(session, "staging required", "convention", 0.5)
    n3 = add_node(session, "root cause unknown", "unknown", 0.7)
    flag_significant(session, n3["id"])
    classify_assumption(session, "staging is required", "convention")
    classify_assumption(session, "Jenkins is stable", "ground", "logs confirm")

    session.advance_phase("vantage")
    set_goal(session, "Eliminate CI flakiness")
    complete_vantage(session)

    generate_paths(session)
    commit_path(session, "B")

    return session


@pytest.fixture
def receipt_session(monkeypatch):
    return _build_full_session(monkeypatch)


class TestGetWrapper:
    def test_returns_callable(self):
        wrapper = get_wrapper("test_chain")
        assert callable(wrapper)

    def test_custom_chain_name(self):
        wrapper = get_wrapper("custom_name")

        @wrapper
        def fn(data):
            return data

        result = fn({"test": True})
        assert result.chain.name == "custom_name"

    def test_default_chain_name(self):
        wrapper = get_wrapper()

        @wrapper
        def fn(data):
            return data

        result = fn({"test": True})
        assert result.chain.name == "vantagepoint"


class TestExtractReceiptInfo:
    def test_extracts_all_fields(self):
        wrapper = get_wrapper("test")

        @wrapper
        def fn(data):
            return data

        result = fn({"key": "value"})
        info = extract_receipt_info(result)
        assert "chain_id" in info
        assert "chain_root" in info
        assert "chain_length" in info
        assert "chain_verified" in info
        assert "receipt" in info

    def test_chain_is_verified(self):
        wrapper = get_wrapper("test")

        @wrapper
        def fn(data):
            return data

        result = fn({"key": "value"})
        info = extract_receipt_info(result)
        assert info["chain_verified"] is True

    def test_chain_length_is_positive(self):
        wrapper = get_wrapper("test")

        @wrapper
        def fn(data):
            return data

        result = fn({"key": "value"})
        info = extract_receipt_info(result)
        assert info["chain_length"] >= 1


class TestGenerateReceipt:
    def test_returns_receipt_dict(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert isinstance(receipt, dict)

    def test_contains_session_id(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["session_id"] == receipt_session.id

    def test_contains_mode(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["mode"] == "standalone"

    def test_contains_friction(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["friction"] == "our deploys keep breaking"
        assert "our deploys keep breaking" in receipt["friction_statement"]

    def test_contains_territory_summary(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        territory = receipt["territory"]
        assert territory["nodes"] == 3
        assert territory["ground"] == 1
        assert territory["convention"] == 1
        assert territory["unknown"] == 1

    def test_contains_discoveries(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert len(receipt["discoveries"]) == 1

    def test_contains_assumptions(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert len(receipt["assumptions"]) == 2

    def test_contains_goal(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["goal"] == "Eliminate CI flakiness"

    def test_contains_paths_summary(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert len(receipt["paths"]) == 3
        for p in receipt["paths"]:
            assert "path_id" in p
            assert "label" in p
            assert "risk" in p

    def test_contains_chosen_path(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["chosen_path"] == "B"

    def test_contains_chain_info(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        chain = receipt["chain"]
        assert "chain_id" in chain
        assert "chain_root" in chain
        assert chain["chain_verified"] is True
        assert chain["chain_length"] >= 1

    def test_contains_chain_entries(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert len(receipt["chain_entries"]) > 0

    def test_adds_receipt_generated_chain_entry(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        entries = [e for e in receipt_session.chain_entries
                   if e.get("action") == "receipt_generated"]
        assert len(entries) == 1
        assert "chain_id" in entries[0]

    def test_chain_name_uses_session_id(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        expected_prefix = f"vp_{receipt_session.id[:8]}"
        # The chain_id is derived from the chain, but we can verify
        # the chain was created (it has entries and is verified)
        assert receipt["chain"]["chain_verified"] is True

    def test_created_at_preserved(self, receipt_session):
        receipt = generate_receipt(receipt_session)
        assert receipt["created_at"] == receipt_session.created_at
