from __future__ import annotations

from text_translator_ai.settings import load_settings


def test_load_settings_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TTA_HOST", raising=False)
    monkeypatch.delenv("TTA_PORT", raising=False)
    monkeypatch.delenv("TTA_DB_PATH", raising=False)
    monkeypatch.delenv("TTA_AI_PROVIDER", raising=False)
    monkeypatch.delenv("TTA_MODEL", raising=False)
    monkeypatch.delenv("TTA_HISTORY_LIMIT", raising=False)

    settings = load_settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8770
    assert settings.model == "openai/gpt-4o"
    assert settings.ai_provider == "github"
    assert settings.github_models == [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "mistral-ai/mistral-small-2503",
        "mistral-ai/mistral-medium-2505",
        "mistral-ai/ministral-3b",
    ]
    assert settings.history_limit == 100


def test_load_settings_env_overrides(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TTA_HOST", "0.0.0.0")
    monkeypatch.setenv("TTA_PORT", "9001")
    monkeypatch.setenv("TTA_MODEL", "gpt-test")
    monkeypatch.setenv("TTA_AI_PROVIDER", "github")
    monkeypatch.setenv("TTA_HISTORY_LIMIT", "12")
    monkeypatch.setenv("TTA_GITHUB_MODELS", "a,b")

    settings = load_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.model == "gpt-test"
    assert settings.ai_provider == "github"
    assert settings.history_limit == 12
    assert settings.github_models == ["a", "b"]
