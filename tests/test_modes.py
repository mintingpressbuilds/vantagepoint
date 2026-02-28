import os
import pytest
from core.mode import Mode, detect_mode, get_mode_description


class TestDetectMode:
    def test_standalone_when_no_env_vars(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert detect_mode() == Mode.STANDALONE

    def test_llm_when_only_anthropic_key(self, monkeypatch):
        monkeypatch.delenv("DOORWAY_API_URL", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        assert detect_mode() == Mode.LLM

    def test_doorway_when_doorway_url_set(self, monkeypatch):
        monkeypatch.setenv("DOORWAY_API_URL", "http://localhost:8000")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert detect_mode() == Mode.DOORWAY

    def test_doorway_takes_priority_over_llm(self, monkeypatch):
        monkeypatch.setenv("DOORWAY_API_URL", "http://localhost:8000")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        assert detect_mode() == Mode.DOORWAY


class TestGetModeDescription:
    def test_standalone_description(self):
        desc = get_mode_description(Mode.STANDALONE)
        assert "Standalone" in desc

    def test_llm_description(self):
        desc = get_mode_description(Mode.LLM)
        assert "LLM" in desc

    def test_doorway_description(self):
        desc = get_mode_description(Mode.DOORWAY)
        assert "Doorway" in desc


class TestModeConstants:
    def test_mode_values(self):
        assert Mode.STANDALONE == "standalone"
        assert Mode.LLM == "llm"
        assert Mode.DOORWAY == "doorway"
