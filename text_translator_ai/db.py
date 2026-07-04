from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from text_translator_ai.schemas import SettingsUpdateRequest, TranslationRecord


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class Database:
    db_path: Path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS translation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_language TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    translation_seconds REAL,
                    translation_context TEXT NOT NULL DEFAULT ''
                );
                """
            )
            history_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(translation_history)").fetchall()
            }
            if "translation_seconds" not in history_columns:
                connection.execute("ALTER TABLE translation_history ADD COLUMN translation_seconds REAL")
            if "translation_context" not in history_columns:
                connection.execute("ALTER TABLE translation_history ADD COLUMN translation_context TEXT NOT NULL DEFAULT ''")
            connection.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES('schema_version', '1')"
            )

    @contextmanager
    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def get_app_setting(self, key: str, default: str | None = None) -> str | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                return default
            return str(row["value"])

    def set_app_setting(self, key: str, value: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO app_settings(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_active_model(self, default_model: str) -> str:
        return self.get_app_setting("active_model", default_model) or default_model

    def get_active_ai_provider(self, default_provider: str) -> str:
        return self.get_app_setting("active_ai_provider", default_provider) or default_provider

    def get_ui_theme(self) -> str:
        theme = self.get_app_setting("ui_theme", "dark") or "dark"
        if theme not in {"dark", "dark_green", "dark_brown"}:
            return "dark"
        return theme

    def update_settings(self, payload: SettingsUpdateRequest) -> None:
        self.set_app_setting("active_ai_provider", payload.active_ai_provider)
        self.set_app_setting("active_model", payload.active_model)
        self.set_app_setting("ui_theme", payload.ui_theme)

    def create_translation(self, record: TranslationRecord, *, retention_limit: int) -> TranslationRecord:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO translation_history(
                    source_text,
                    translated_text,
                    source_language,
                    target_language,
                    provider,
                    model,
                    status,
                    created_at,
                    translation_seconds,
                    translation_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.source_text,
                    record.translated_text,
                    record.source_language,
                    record.target_language,
                    record.provider,
                    record.model,
                    record.status,
                    record.created_at,
                    record.translation_seconds,
                    record.translation_context,
                ),
            )
            self._trim_history(connection, retention_limit)
            return TranslationRecord(id=cursor.lastrowid, **record.model_dump(exclude={"id"}))

    def list_history(self, limit: int = 20) -> list[TranslationRecord]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, source_text, translated_text, source_language, target_language, provider, model, status, created_at, translation_seconds, translation_context
                FROM translation_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [self._row_to_translation(row) for row in rows]

    def clear_history(self) -> None:
        with self.connection() as connection:
            connection.execute("DELETE FROM translation_history")

    def _trim_history(self, connection: sqlite3.Connection, retention_limit: int) -> None:
        if retention_limit <= 0:
            connection.execute("DELETE FROM translation_history")
            return
        connection.execute(
            """
            DELETE FROM translation_history
            WHERE id NOT IN (
                SELECT id FROM translation_history ORDER BY id DESC LIMIT ?
            )
            """,
            (retention_limit,),
        )

    def _row_to_translation(self, row: sqlite3.Row) -> TranslationRecord:
        return TranslationRecord(
            id=row["id"],
            source_text=row["source_text"],
            translated_text=row["translated_text"],
            source_language=row["source_language"],
            target_language=row["target_language"],
            provider=row["provider"],
            model=row["model"],
            status=row["status"],
            created_at=row["created_at"],
            translation_seconds=row["translation_seconds"],
            translation_context=row["translation_context"],
        )
