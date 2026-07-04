from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


SUPPORTED_LANGUAGES = (
    "Russian",
    "Serbian",
    "English",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Swedish",
)

ThemeName = Literal["dark", "dark_green", "dark_brown"]


def validate_language(value: str) -> str:
    if value not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {value}")
    return value


class TranslationRequest(BaseModel):
    source_text: str = Field(default="")
    source_language: str
    target_language: str
    translation_context: str = Field(default="", max_length=120)

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_supported_language(cls, value: str) -> str:
        return validate_language(value)

    @field_validator("translation_context")
    @classmethod
    def normalize_translation_context(cls, value: str) -> str:
        return " ".join(value.strip().split())


class TranslationRecord(BaseModel):
    id: int | None = None
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    model: str
    status: str
    created_at: str
    translation_seconds: float | None = None
    translation_context: str = ""


class TranslationResponse(BaseModel):
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    model: str
    status: str
    created_at: str
    translation_seconds: float | None = None
    translation_context: str = ""
    error: str | None = None


class SettingsRecord(BaseModel):
    model: str
    active_model: str
    active_ai_provider: str = "openai"
    available_ai_providers: list[str] = Field(default_factory=lambda: ["openai", "github"])
    ui_theme: ThemeName = "dark"
    available_models: list[str] = Field(default_factory=list)
    available_models_by_provider: dict[str, list[str]] = Field(default_factory=dict)
    host: str
    port: int
    supported_languages: list[str] = Field(default_factory=lambda: list(SUPPORTED_LANGUAGES))


class SettingsUpdateRequest(BaseModel):
    active_model: str
    active_ai_provider: str = "openai"
    ui_theme: ThemeName = "dark"


class AIProbeRequest(BaseModel):
    active_model: str | None = None
    active_ai_provider: str | None = None


class ModelListResponse(BaseModel):
    provider: str
    models: list[str] = Field(default_factory=list)
    source: str = "configured"
    detail: str | None = None


class AIDiagnosticsResponse(BaseModel):
    active_ai_provider: str
    active_model: str
    github_token_configured: bool
    github_token_source: str | None = None
    github_token_fingerprint: str | None = None
    active_model_in_configured_github_models: bool
    configured_github_model_count: int


class AIProbeResponse(BaseModel):
    provider: str
    model: str
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    now: datetime


class StatusResponse(BaseModel):
    status: str
