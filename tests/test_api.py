from __future__ import annotations

from fastapi.testclient import TestClient

import text_translator_ai.app as app_module
from text_translator_ai.ai_client import AIClientError, TranslationAIResult
from text_translator_ai.app import create_app


class FakeOpenAIClient:
    instances: list["FakeOpenAIClient"] = []

    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key
        self.calls: list[dict[str, str]] = []
        self.fail = False
        FakeOpenAIClient.instances.append(self)

    def list_models(self) -> list[str]:
        return ["gpt-4o", "gpt-test"]

    def translate(
        self,
        *,
        model: str,
        source_text: str,
        source_language: str,
        target_language: str,
        translation_context: str = "",
    ) -> TranslationAIResult:
        self.calls.append(
            {
                "model": model,
                "source_text": source_text,
                "source_language": source_language,
                "target_language": target_language,
                "translation_context": translation_context,
            }
        )
        if self.fail:
            raise AIClientError("provider unavailable")
        return TranslationAIResult(translated_text=f"{target_language}: {source_text}")


class FakeGitHubModelsClient(FakeOpenAIClient):
    instances: list["FakeGitHubModelsClient"] = []

    def __init__(self, token: str | None) -> None:
        self.api_key = token
        self.calls: list[dict[str, str]] = []
        self.fail = False
        FakeGitHubModelsClient.instances.append(self)

    def list_models(self) -> list[str]:
        return ["openai/gpt-4o", "openai/gpt-test"]


def build_client(monkeypatch, test_settings) -> TestClient:
    FakeOpenAIClient.instances.clear()
    FakeGitHubModelsClient.instances.clear()
    monkeypatch.setattr(app_module, "OpenAIClient", FakeOpenAIClient)
    monkeypatch.setattr(app_module, "GitHubModelsClient", FakeGitHubModelsClient)
    return TestClient(create_app(test_settings))


def test_health_endpoint(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_pages_render(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    home_html = client.get("/").text
    settings_html = client.get("/settings").text
    assert "Text Translator AI" in home_html
    assert 'id="historyList" hidden' in home_html
    assert "Show History" in home_html
    assert '<option value="Serbian" selected>Serbian</option>' in home_html
    assert '<option value="Russian" selected>Russian</option>' in home_html
    assert "text-translator-ai:draft" in home_html
    assert "restoreDraft();" in home_html
    assert "sourceText.focus();" in home_html
    assert 'id="contextTopic"' in home_html
    assert '<option value="Medicine">Medicine</option>' in home_html
    assert 'id="customContext"' in home_html
    assert 'id="contextStatus"' in home_html
    assert "Active context:" in home_html
    assert "updateContextStatus();" in home_html
    assert "Context changed, retranslating..." in home_html
    assert "Enter a custom topic to retranslate" in home_html
    assert "queueContextRetranslate();" in home_html
    assert "translation_context: activeTranslationContext()" in home_html
    assert "--source-bg" in home_html
    assert "#translatedText" in home_html
    assert "Provider diagnostics" not in settings_html
    assert "diagnosticsBox" not in settings_html
    assert "Appearance" in settings_html
    assert 'id="themeSelect"' in settings_html
    assert 'href="/">Home</a>' in settings_html


def test_settings_exposes_themes_and_languages(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    payload = client.get("/api/settings").json()

    assert payload["ui_theme"] == "dark"
    assert payload["active_ai_provider"] == "openai"
    assert "Serbian" in payload["supported_languages"]


def test_github_models_endpoint_uses_catalog(monkeypatch, test_settings) -> None:
    test_settings.ai_provider = "github"
    client = build_client(monkeypatch, test_settings)

    response = client.get("/api/settings/models?provider=github")

    payload = response.json()
    assert payload["source"] == "live"
    assert payload["models"] == ["openai/gpt-4o", "openai/gpt-test"]


def test_ai_probe_uses_selected_unsaved_model(monkeypatch, test_settings) -> None:
    test_settings.ai_provider = "github"
    client = build_client(monkeypatch, test_settings)
    client.get("/api/settings/models?provider=github")

    response = client.post(
        "/api/settings/ai-probe",
        json={"active_ai_provider": "github", "active_model": "openai/gpt-test"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert FakeGitHubModelsClient.instances[0].calls[-1]["model"] == "openai/gpt-test"


def test_translation_success_saves_history(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.post(
        "/api/translate",
        json={
            "source_text": "Hello",
            "source_language": "English",
            "target_language": "German",
            "translation_context": "Medicine",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["translated_text"] == "German: Hello"
    assert payload["translation_context"] == "Medicine"
    assert isinstance(payload["translation_seconds"], float)
    assert payload["translation_seconds"] >= 0
    assert FakeOpenAIClient.instances[0].calls[-1]["translation_context"] == "Medicine"
    history = client.get("/api/history").json()
    assert len(history) == 1
    assert history[0]["source_text"] == "Hello"
    assert history[0]["translation_context"] == "Medicine"
    assert isinstance(history[0]["translation_seconds"], float)


def test_empty_input_skips_ai(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.post(
        "/api/translate",
        json={"source_text": "  ", "source_language": "English", "target_language": "German"},
    )

    assert response.json()["status"] == "empty"
    assert FakeOpenAIClient.instances[0].calls == []


def test_same_language_translation_returns_original_without_ai(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.post(
        "/api/translate",
        json={"source_text": "Hello", "source_language": "English", "target_language": "English"},
    )

    payload = response.json()
    assert payload["status"] == "copied"
    assert payload["translated_text"] == "Hello"
    assert isinstance(payload["translation_seconds"], float)
    assert FakeOpenAIClient.instances[0].calls == []


def test_unsupported_language_returns_422(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.post(
        "/api/translate",
        json={"source_text": "Hello", "source_language": "Klingon", "target_language": "English"},
    )

    assert response.status_code == 422


def test_failed_ai_response_returns_clear_error(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)
    FakeOpenAIClient.instances[0].fail = True

    response = client.post(
        "/api/translate",
        json={"source_text": "Hello", "source_language": "English", "target_language": "German"},
    )

    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error"] == "provider unavailable"
    assert isinstance(payload["translation_seconds"], float)
    assert client.get("/api/history").json() == []


def test_history_retention_is_enforced(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    for index in range(5):
        client.post(
            "/api/translate",
            json={
                "source_text": f"Hello {index}",
                "source_language": "English",
                "target_language": "German",
            },
        )

    history = client.get("/api/history").json()
    assert len(history) == 3
    assert history[0]["source_text"] == "Hello 4"
    assert history[-1]["source_text"] == "Hello 2"


def test_settings_update_validates_model(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.put(
        "/api/settings",
        json={"active_ai_provider": "openai", "active_model": "missing", "ui_theme": "dark_green"},
    )

    assert response.status_code == 400


def test_settings_update_persists_theme(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)

    response = client.put(
        "/api/settings",
        json={"active_ai_provider": "openai", "active_model": "gpt-4o", "ui_theme": "dark_brown"},
    )

    assert response.status_code == 200
    assert response.json()["ui_theme"] == "dark_brown"
    assert 'data-theme="dark_brown"' in client.get("/").text


def test_ai_probe_reports_failure(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)
    FakeOpenAIClient.instances[0].fail = True

    response = client.post("/api/settings/ai-probe")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_clear_history(monkeypatch, test_settings) -> None:
    client = build_client(monkeypatch, test_settings)
    client.post(
        "/api/translate",
        json={"source_text": "Hello", "source_language": "English", "target_language": "German"},
    )

    response = client.delete("/api/history")

    assert response.json()["status"] == "cleared"
    assert client.get("/api/history").json() == []
