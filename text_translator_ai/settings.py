from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_GITHUB_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "mistral-ai/mistral-small-2503",
    "mistral-ai/mistral-medium-2505",
    "mistral-ai/ministral-3b",
]


@dataclass(slots=True)
class Settings:
    project_root: Path
    db_path: Path
    host: str
    port: int
    openai_api_key: str | None
    model: str
    history_limit: int
    ai_provider: str = "github"
    github_models_token: str | None = None
    github_models_token_source: str | None = None
    github_models: list[str] | None = None


def resolve_project_root() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists() and (cwd / "text_translator_ai").exists():
        return cwd
    return Path(__file__).resolve().parents[1]


def load_settings() -> Settings:
    project_root = resolve_project_root()
    db_path = Path(os.environ.get("TTA_DB_PATH", "./.data/text-translator-ai.db")).expanduser()
    if not db_path.is_absolute():
        db_path = project_root / db_path
    github_models = [
        model.strip()
        for model in os.environ.get("TTA_GITHUB_MODELS", ",".join(DEFAULT_GITHUB_MODELS)).split(",")
        if model.strip()
    ]
    return Settings(
        project_root=project_root,
        db_path=db_path,
        host=os.environ.get("TTA_HOST", "127.0.0.1"),
        port=int(os.environ.get("TTA_PORT", "8770")),
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        model=os.environ.get("TTA_MODEL", "openai/gpt-4o"),
        history_limit=int(os.environ.get("TTA_HISTORY_LIMIT", "100")),
        ai_provider=os.environ.get("TTA_AI_PROVIDER", "github").strip().lower() or "github",
        github_models_token=os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN"),
        github_models_token_source=(
            "GITHUB_MODELS_TOKEN"
            if os.environ.get("GITHUB_MODELS_TOKEN")
            else ("GITHUB_TOKEN" if os.environ.get("GITHUB_TOKEN") else None)
        ),
        github_models=github_models or DEFAULT_GITHUB_MODELS,
    )
