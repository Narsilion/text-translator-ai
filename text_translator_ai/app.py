from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response

from text_translator_ai.ai_client import AIClientError, GitHubModelsClient, OpenAIClient, RoutingAIClient
from text_translator_ai.db import Database
from text_translator_ai.schemas import (
    AIDiagnosticsResponse,
    AIProbeRequest,
    AIProbeResponse,
    HealthResponse,
    ModelListResponse,
    SettingsRecord,
    SettingsUpdateRequest,
    StatusResponse,
    TranslationRecord,
    TranslationRequest,
    TranslationResponse,
)
from text_translator_ai.settings import DEFAULT_GITHUB_MODELS, Settings
from text_translator_ai.translation import TranslationService
from text_translator_ai.ui import render_settings_page, render_translator_page


def create_app(settings: Settings) -> FastAPI:
    openai_models = [
        "gpt-4o",
        "gpt-5-mini",
        "gpt-5.4-mini",
        "gpt-5",
        "gpt-5.4",
    ]
    available_ai_providers = ["openai", "github"]
    default_ai_provider = settings.ai_provider if settings.ai_provider in available_ai_providers else "openai"
    github_models = settings.github_models or DEFAULT_GITHUB_MODELS
    available_models_by_provider = {
        "openai": openai_models,
        "github": list(dict.fromkeys(github_models)),
    }
    if (
        settings.model not in available_models_by_provider[default_ai_provider]
        and (default_ai_provider != "github" or "/" in settings.model)
    ):
        available_models_by_provider[default_ai_provider].insert(0, settings.model)

    db = Database(settings.db_path)
    db.initialize()
    if db.get_app_setting("active_ai_provider") is None:
        db.set_app_setting("active_ai_provider", default_ai_provider)
    if db.get_app_setting("active_model") is None:
        db.set_app_setting("active_model", settings.model)

    openai_client = OpenAIClient(settings.openai_api_key)
    github_models_client = GitHubModelsClient(settings.github_models_token)

    def active_ai_provider() -> str:
        provider = db.get_active_ai_provider(default_ai_provider)
        return provider if provider in available_ai_providers else default_ai_provider

    def available_models_for_provider(provider: str) -> list[str]:
        return available_models_by_provider.get(provider, [])

    def available_models_for_active_provider() -> list[str]:
        return available_models_for_provider(active_ai_provider())

    def active_model() -> str:
        stored_model = db.get_active_model(settings.model)
        models = available_models_for_active_provider()
        return stored_model if stored_model in models else models[0]

    provider_models_cache_ttl = 300
    provider_models_cache_ts: dict[str, float] = {}

    def refresh_provider_models(provider: str, force: bool = False) -> ModelListResponse:
        if provider not in available_ai_providers:
            raise HTTPException(status_code=400, detail="That AI provider is not supported.")
        fallback_models = available_models_by_provider[provider]
        now = time.monotonic()
        last_fetch = provider_models_cache_ts.get(provider, 0.0)
        if not force and (now - last_fetch) < provider_models_cache_ttl:
            return ModelListResponse(provider=provider, models=fallback_models, source="live")
        try:
            models = github_models_client.list_models() if provider == "github" else openai_client.list_models()
        except AIClientError as exc:
            return ModelListResponse(provider=provider, models=fallback_models, source="fallback", detail=str(exc))
        if not models:
            return ModelListResponse(
                provider=provider,
                models=fallback_models,
                source="fallback",
                detail="Provider returned no text generation models.",
            )
        available_models_by_provider[provider] = models
        provider_models_cache_ts[provider] = now
        return ModelListResponse(provider=provider, models=models, source="live")

    client = RoutingAIClient(
        active_provider=active_ai_provider,
        openai_client=openai_client,
        github_client=github_models_client,
    )
    translation_service = TranslationService(
        db=db,
        client=client,
        active_provider=active_ai_provider,
        active_model=active_model,
        history_limit=settings.history_limit,
    )

    def build_settings_record() -> SettingsRecord:
        return SettingsRecord(
            model=settings.model,
            active_model=active_model(),
            active_ai_provider=active_ai_provider(),
            available_ai_providers=available_ai_providers,
            ui_theme=db.get_ui_theme(),
            available_models=available_models_for_active_provider(),
            available_models_by_provider=available_models_by_provider,
            host=settings.host,
            port=settings.port,
        )

    def build_ai_diagnostics() -> AIDiagnosticsResponse:
        token = settings.github_models_token
        token_fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12] if token else None
        configured_github_models = available_models_by_provider["github"]
        return AIDiagnosticsResponse(
            active_ai_provider=active_ai_provider(),
            active_model=active_model(),
            github_token_configured=bool(token),
            github_token_source=settings.github_models_token_source,
            github_token_fingerprint=token_fingerprint,
            active_model_in_configured_github_models=active_model() in configured_github_models,
            configured_github_model_count=len(configured_github_models),
        )

    app = FastAPI(title="Text Translator AI")
    app.state.settings = settings
    app.state.db = db
    app.state.translation_service = translation_service

    @app.get("/", response_class=HTMLResponse)
    async def translator_page() -> str:
        return render_translator_page(build_settings_record(), db.list_history(limit=10))

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page() -> str:
        return render_settings_page(build_settings_record())

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        return Response(status_code=204)

    @app.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(now=datetime.now(UTC))

    @app.get("/api/settings", response_model=SettingsRecord)
    async def get_settings() -> SettingsRecord:
        return build_settings_record()

    @app.put("/api/settings", response_model=SettingsRecord)
    async def update_settings(payload: SettingsUpdateRequest) -> SettingsRecord:
        if payload.active_ai_provider not in available_ai_providers:
            raise HTTPException(status_code=400, detail="That AI provider is not supported.")
        if payload.active_model not in available_models_for_provider(payload.active_ai_provider):
            raise HTTPException(
                status_code=400,
                detail="That model is not in the available model list. Pick one from the menu.",
            )
        db.update_settings(payload)
        return build_settings_record()

    @app.get("/api/settings/models", response_model=ModelListResponse)
    async def list_provider_models(provider: str | None = None) -> ModelListResponse:
        return refresh_provider_models(provider or active_ai_provider(), force=True)

    @app.get("/api/settings/ai-diagnostics", response_model=AIDiagnosticsResponse)
    async def get_ai_diagnostics() -> AIDiagnosticsResponse:
        return build_ai_diagnostics()

    @app.post("/api/settings/ai-probe", response_model=AIProbeResponse)
    async def probe_ai_model(payload: AIProbeRequest | None = None) -> AIProbeResponse:
        provider = payload.active_ai_provider if payload and payload.active_ai_provider else active_ai_provider()
        model = payload.active_model if payload and payload.active_model else active_model()
        if provider not in available_ai_providers:
            return AIProbeResponse(provider=provider, model=model, status="failed", detail="That AI provider is not supported.")
        if model not in available_models_for_provider(provider):
            return AIProbeResponse(
                provider=provider,
                model=model,
                status="failed",
                detail="That model is not in the available model list. Refresh models before probing.",
            )
        try:
            probe_client = (
                github_models_client.translate
                if provider == "github"
                else openai_client.translate
            )
            probe_client(
                model=model,
                source_text="Hello",
                source_language="English",
                target_language="Serbian",
            )
        except AIClientError as exc:
            return AIProbeResponse(provider=provider, model=model, status="failed", detail=str(exc))
        return AIProbeResponse(provider=provider, model=model, status="ok")

    @app.post("/api/translate", response_model=TranslationResponse)
    async def translate(payload: TranslationRequest) -> TranslationResponse:
        return translation_service.translate(payload)

    @app.get("/api/history", response_model=list[TranslationRecord])
    async def list_history(limit: int = 20) -> list[TranslationRecord]:
        return db.list_history(limit=limit)

    @app.delete("/api/history", response_model=StatusResponse)
    async def clear_history() -> StatusResponse:
        db.clear_history()
        return StatusResponse(status="cleared")

    return app
