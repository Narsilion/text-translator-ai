from __future__ import annotations

import time

from text_translator_ai.ai_client import AIClientError, RoutingAIClient
from text_translator_ai.db import Database, utc_now_iso
from text_translator_ai.schemas import TranslationRecord, TranslationRequest, TranslationResponse


class TranslationService:
    def __init__(
        self,
        *,
        db: Database,
        client: RoutingAIClient,
        active_provider,
        active_model,
        history_limit: int,
    ) -> None:
        self.db = db
        self.client = client
        self.active_provider = active_provider
        self.active_model = active_model
        self.history_limit = history_limit

    def translate(self, payload: TranslationRequest) -> TranslationResponse:
        started_at = time.perf_counter()
        source_text = payload.source_text.strip()
        provider = self.active_provider()
        model = self.active_model()
        created_at = utc_now_iso()
        if not source_text:
            translation_seconds = time.perf_counter() - started_at
            return TranslationResponse(
                source_text=payload.source_text,
                translated_text="",
                source_language=payload.source_language,
                target_language=payload.target_language,
                provider=provider,
                model=model,
                status="empty",
                created_at=created_at,
                translation_seconds=translation_seconds,
                translation_context=payload.translation_context,
            )
        if payload.source_language == payload.target_language:
            translation_seconds = time.perf_counter() - started_at
            return TranslationResponse(
                source_text=payload.source_text,
                translated_text=payload.source_text,
                source_language=payload.source_language,
                target_language=payload.target_language,
                provider=provider,
                model=model,
                status="copied",
                created_at=created_at,
                translation_seconds=translation_seconds,
                translation_context=payload.translation_context,
            )
        try:
            result = self.client.translate(
                model=model,
                source_text=payload.source_text,
                source_language=payload.source_language,
                target_language=payload.target_language,
                translation_context=payload.translation_context,
            )
        except AIClientError as exc:
            translation_seconds = time.perf_counter() - started_at
            return TranslationResponse(
                source_text=payload.source_text,
                translated_text="",
                source_language=payload.source_language,
                target_language=payload.target_language,
                provider=provider,
                model=model,
                status="failed",
                created_at=created_at,
                translation_seconds=translation_seconds,
                translation_context=payload.translation_context,
                error=str(exc),
            )
        translation_seconds = time.perf_counter() - started_at
        response = TranslationResponse(
            source_text=payload.source_text,
            translated_text=result.translated_text,
            source_language=payload.source_language,
            target_language=payload.target_language,
            provider=provider,
            model=model,
            status="success",
            created_at=created_at,
            translation_seconds=translation_seconds,
            translation_context=payload.translation_context,
        )
        self.db.create_translation(
            TranslationRecord(
                source_text=response.source_text,
                translated_text=response.translated_text,
                source_language=response.source_language,
                target_language=response.target_language,
                provider=response.provider,
                model=response.model,
                status=response.status,
                created_at=response.created_at,
                translation_seconds=response.translation_seconds,
                translation_context=response.translation_context,
            ),
            retention_limit=self.history_limit,
        )
        return response
