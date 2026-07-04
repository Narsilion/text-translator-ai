from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_API_URL = "https://api.openai.com/v1/models"
GITHUB_MODELS_API_URL = "https://models.github.ai/inference/chat/completions"
GITHUB_MODELS_CATALOG_API_URL = "https://models.github.ai/catalog/models"
GITHUB_MODELS_API_VERSION = "2026-03-10"


class AIClientError(RuntimeError):
    """Raised when an AI provider request fails."""


class OpenAIClientError(AIClientError):
    """Raised when the OpenAI request fails."""


@dataclass(slots=True)
class TranslationAIResult:
    translated_text: str


class OpenAIClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    def list_models(self) -> list[str]:
        if not self.api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not configured")
        request = Request(
            OPENAI_MODELS_API_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise OpenAIClientError(f"OpenAI models request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OpenAIClientError(f"OpenAI models request failed: {exc.reason}") from exc
        models = body.get("data") if isinstance(body, dict) else None
        if not isinstance(models, list):
            raise OpenAIClientError(f"Unexpected OpenAI models response shape: {body}")
        ids = [str(model.get("id") or "").strip() for model in models if isinstance(model, dict)]
        return sorted({model_id for model_id in ids if _is_openai_text_generation_model(model_id)})

    def translate(
        self,
        *,
        model: str,
        source_text: str,
        source_language: str,
        target_language: str,
        translation_context: str = "",
    ) -> TranslationAIResult:
        if not self.api_key:
            raise OpenAIClientError("OPENAI_API_KEY is not configured")
        payload = _translation_chat_payload(
            model=model,
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
            translation_context=translation_context,
        )
        request = Request(
            OPENAI_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise OpenAIClientError(f"OpenAI request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OpenAIClientError(f"OpenAI request failed: {exc.reason}") from exc
        return _parse_translation_response(body, provider_name="OpenAI")


class GitHubModelsClient:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def list_models(self) -> list[str]:
        if not self.token:
            raise AIClientError("GITHUB_MODELS_TOKEN is not configured")
        request = Request(
            GITHUB_MODELS_CATALOG_API_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_MODELS_API_VERSION,
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise AIClientError(f"GitHub Models catalog request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AIClientError(f"GitHub Models catalog request failed: {exc.reason}") from exc
        if not isinstance(body, list):
            raise AIClientError(f"Unexpected GitHub Models catalog response shape: {body}")
        ids: list[str] = []
        for model in body:
            if not isinstance(model, dict):
                continue
            inputs = model.get("supported_input_modalities")
            outputs = model.get("supported_output_modalities")
            if not isinstance(inputs, list) or not isinstance(outputs, list):
                continue
            if "text" not in inputs or "text" not in outputs:
                continue
            model_id = str(model.get("id") or "").strip()
            if model_id:
                ids.append(model_id)
        return sorted(set(ids))

    def translate(
        self,
        *,
        model: str,
        source_text: str,
        source_language: str,
        target_language: str,
        translation_context: str = "",
    ) -> TranslationAIResult:
        if not self.token:
            raise AIClientError("GITHUB_MODELS_TOKEN is not configured")
        payload = _translation_chat_payload(
            model=model,
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
            translation_context=translation_context,
        )
        request = Request(
            GITHUB_MODELS_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_MODELS_API_VERSION,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            if exc.code == 403 and "No access to model" in detail:
                raise AIClientError(
                    f"GitHub Models denied access to {model}. Choose another GitHub model in Settings, "
                    "or set TTA_GITHUB_MODELS to models available to this GitHub account."
                ) from exc
            raise AIClientError(f"GitHub Models request failed with status {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AIClientError(f"GitHub Models request failed: {exc.reason}") from exc
        return _parse_translation_response(body, provider_name="GitHub Models")


class RoutingAIClient:
    def __init__(
        self,
        *,
        active_provider,
        openai_client: OpenAIClient,
        github_client: GitHubModelsClient,
    ) -> None:
        self.active_provider = active_provider
        self.openai_client = openai_client
        self.github_client = github_client

    def translate(
        self,
        *,
        model: str,
        source_text: str,
        source_language: str,
        target_language: str,
        translation_context: str = "",
    ) -> TranslationAIResult:
        provider = self.active_provider()
        if provider == "openai":
            return self.openai_client.translate(
                model=model,
                source_text=source_text,
                source_language=source_language,
                target_language=target_language,
                translation_context=translation_context,
            )
        if provider == "github":
            return self.github_client.translate(
                model=model,
                source_text=source_text,
                source_language=source_language,
                target_language=target_language,
                translation_context=translation_context,
            )
        raise AIClientError(f"Unknown AI provider: {provider}")


def _translation_schema() -> dict[str, object]:
    return {
        "name": "translation_payload",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "translated_text": {"type": "string"},
            },
            "required": ["translated_text"],
        },
        "strict": True,
    }


def _translation_chat_payload(
    *,
    model: str,
    source_text: str,
    source_language: str,
    target_language: str,
    translation_context: str = "",
) -> dict[str, object]:
    system_prompt = (
        "You are a precise professional translator. Translate only the user's text. "
        "Preserve meaning, tone, register, names, paragraph breaks, line breaks, lists, and punctuation. "
        "Return JSON only."
    )
    context_line = (
        f"Translation context/domain: {translation_context}.\n"
        if translation_context
        else "Translation context/domain: general.\n"
    )
    user_prompt = (
        f"Translate from {source_language} to {target_language}.\n\n"
        f"{context_line}"
        "Use the context only to choose accurate terminology; do not add explanations or extra content.\n\n"
        "Text:\n"
        f"{source_text}\n\n"
        "Return the translation in translated_text."
    )
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": _translation_schema(),
        },
    }


def _parse_translation_response(body: object, *, provider_name: str) -> TranslationAIResult:
    try:
        content = body["choices"][0]["message"]["content"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIClientError(f"Unexpected {provider_name} response shape: {body}") from exc
    try:
        payload = json.loads(str(content))
    except json.JSONDecodeError as exc:
        raise AIClientError(f"{provider_name} response was not valid JSON") from exc
    translated_text = payload.get("translated_text") if isinstance(payload, dict) else None
    if not isinstance(translated_text, str):
        raise AIClientError(f"{provider_name} response did not include translated_text")
    return TranslationAIResult(translated_text=translated_text)


def _is_openai_text_generation_model(model_id: str) -> bool:
    if not model_id:
        return False
    excluded_prefixes = (
        "text-embedding",
        "dall-e",
        "tts",
        "whisper",
        "omni-moderation",
        "babbage",
        "davinci",
    )
    if model_id.startswith(excluded_prefixes):
        return False
    included_prefixes = ("gpt-", "chatgpt-", "o1", "o3", "o4")
    return model_id.startswith(included_prefixes)
