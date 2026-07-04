from __future__ import annotations

from pathlib import Path

import pytest

from text_translator_ai.settings import Settings


TEST_GITHUB_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "mistral-ai/mistral-small-2503",
]


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        project_root=tmp_path,
        db_path=tmp_path / "app.db",
        host="127.0.0.1",
        port=8770,
        openai_api_key=None,
        model="openai/gpt-4o",
        history_limit=3,
        ai_provider="openai",
        github_models_token=None,
        github_models_token_source=None,
        github_models=TEST_GITHUB_MODELS,
    )
