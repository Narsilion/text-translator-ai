from __future__ import annotations

import pytest

from text_translator_ai.ai_client import AIClientError, _parse_translation_response, _translation_chat_payload


def test_parse_translation_response() -> None:
    result = _parse_translation_response(
        {"choices": [{"message": {"content": '{"translated_text":"Hallo"}'}}]},
        provider_name="test",
    )

    assert result.translated_text == "Hallo"


def test_parse_translation_response_rejects_missing_field() -> None:
    with pytest.raises(AIClientError):
        _parse_translation_response(
            {"choices": [{"message": {"content": '{"text":"Hallo"}'}}]},
            provider_name="test",
        )


def test_translation_payload_includes_context() -> None:
    payload = _translation_chat_payload(
        model="gpt-test",
        source_text="bol u grudima",
        source_language="Serbian",
        target_language="Russian",
        translation_context="Medicine",
    )

    user_message = payload["messages"][1]["content"]
    assert "Translation context/domain: Medicine." in user_message
