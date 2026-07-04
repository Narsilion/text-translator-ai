# Text Translator AI Specification

## Product Summary

Build `text-translator-ai`, a locally hosted text translation web app modeled after Google Translate's core text workflow. The user manually selects a source language and target language, types text into the source panel, and receives an AI-generated translation automatically in the output panel.

The app is text-only. It does not support file translation, OCR, speech, image input, browser extensions, accounts, cloud sync, or multi-user features.

## Stack And Hosting

- New repo: `/Users/darkcreation/Documents/git_repos/text-translator-ai`
- Package: `text_translator_ai`
- Console script: `text-translator-ai`
- Stack copied from `prompt-study-notifier`:
  - Python 3.14+
  - FastAPI
  - Uvicorn
  - Pydantic v2
  - SQLite
  - server-rendered HTML with embedded CSS/JS
  - raw `urllib` AI provider clients
- Default local URL: `http://127.0.0.1:8770`

## Languages

Supported source and target languages:

- Russian
- Serbian
- English
- German
- French
- Spanish
- Italian
- Swedish

Source language is manual-only. No auto-detect.

## Core Translation Behavior

- User selects source language and target language.
- User types or pastes text into the source textarea.
- Frontend waits briefly after input stops, then calls the translation API automatically.
- Empty input clears the output and does not call AI.
- Same source and target language returns the original text locally without calling AI.
- Stale responses must not overwrite newer translations.
- Output is read-only and copyable.
- Translation should preserve:
  - meaning
  - tone/register
  - paragraph breaks
  - line breaks
  - lists
  - punctuation
  - names and proper nouns unless translation is clearly appropriate

## AI Integration

- Copy the provider pattern from `prompt-study-notifier`.
- Supported providers:
  - OpenAI
  - GitHub Models
- Default provider: GitHub Models.
- Default model setting: `openai/gpt-4o`.
- GitHub Models fallback defaults: `openai/gpt-4o`, `openai/gpt-4o-mini`, `mistral-ai/mistral-small-2503`, `mistral-ai/mistral-medium-2505`, `mistral-ai/ministral-3b`.
- GitHub Models dropdown can be refreshed from the GitHub catalog. Because catalog entries can be unavailable to the current token at inference time, the settings page must let the user probe the selected provider/model before saving it.
- Use strict JSON schema output with one required field:
  - `translated_text: string`
- Provider/model settings are persisted in SQLite.
- The app should expose enough provider diagnostics to make local setup issues visible without checking logs.

## API

- `GET /`
  - Main translator UI.
- `GET /settings`
  - Settings UI for provider, model, theme, model refresh, and AI probe.
- `GET /api/health`
  - Returns app health and current timestamp.
- `GET /api/settings`
  - Returns active provider/model/theme and available options.
- `PUT /api/settings`
  - Updates active provider/model/theme.
- `GET /api/settings/models`
  - Lists models for selected or active provider.
- `POST /api/settings/ai-probe`
  - Sends a minimal test request to the active provider/model.
- `POST /api/translate`
  - Request: source text, source language, target language.
  - Response: translated text, provider, model, status, timestamp, optional error.
- `GET /api/history`
  - Returns recent successful translations.
- `DELETE /api/history`
  - Clears local translation history.

## Persistence

SQLite stores:

- active provider
- active model
- UI theme
- recent successful translations

Default history retention: 100 successful translations. Failed translations are not stored.

## UI Requirements

- Main page has:
  - top app bar
  - provider/model status
  - Settings link
  - source language selector
  - target language selector
  - swap-language button
  - source textarea
  - translated output panel
  - copy output button
  - compact recent history list
- Desktop layout: source and output panels side by side.
- Mobile layout: panels stacked.
- Settings page has:
  - same relevant settings pattern as `prompt-study-notifier`
  - provider selector
  - model selector
  - theme selector
  - refresh models button
  - AI probe button
  - provider diagnostics block
  - save status and validation errors
- Visual style should be practical and app-like, aligned with the local dashboard feel of `prompt-study-notifier`, but simpler.

## Settings Page Requirements

The settings page should be implemented similarly to the relevant parts of `/Users/darkcreation/Documents/git_repos/prompt-study-notifier`:

- Route: `GET /settings`.
- Active settings are loaded from `GET /api/settings`.
- Settings are saved through `PUT /api/settings`.
- Supported AI providers:
  - `openai`
  - `github`
- Provider selection updates the model list shown in the model selector.
- Model selector uses the available model list for the selected provider.
- Refresh models button calls `GET /api/settings/models?provider=<provider>` and updates the selector.
- AI probe button calls `POST /api/settings/ai-probe` and displays success or failure details.
- Theme selector supports the same theme set as `prompt-study-notifier`:
  - `dark`
  - `dark_green`
  - `dark_brown`
- Theme choice is persisted in SQLite as `ui_theme`.
- The selected theme applies to both `/` and `/settings`.
- The settings page must not include notifier-only settings:
  - scheduler interval
  - retention limit controls for generated sessions
  - templates
  - schedules
  - Telegram
  - browser notifications

Settings response shape should include:

- configured default model
- active model
- active AI provider
- available AI providers
- UI theme
- available models for the active provider
- available models by provider
- host
- port

Settings update request should include:

- active model
- active AI provider
- UI theme

Provider diagnostics should include:

- active AI provider
- active model
- whether the GitHub Models token is configured
- GitHub token source, when available
- short token fingerprint, when available
- whether the active GitHub model is present in configured GitHub model fallbacks
- configured GitHub fallback model count

## Environment

Use `TTA_` prefix for this app:

- `TTA_HOST`, default `127.0.0.1`
- `TTA_PORT`, default `8770`
- `TTA_DB_PATH`, default `./.data/text-translator-ai.db`
- `TTA_AI_PROVIDER`, default `github`
- `TTA_MODEL`, default `openai/gpt-4o`
- `TTA_GITHUB_MODELS`, default `openai/gpt-4o,openai/gpt-4o-mini,mistral-ai/mistral-small-2503,mistral-ai/mistral-medium-2505,mistral-ai/ministral-3b`
- `TTA_HISTORY_LIMIT`, default `100`
- `OPENAI_API_KEY`
- `GITHUB_MODELS_TOKEN` or `GITHUB_TOKEN`

## Test Requirements

- Settings defaults and environment overrides.
- Health endpoint.
- Main page and settings page render.
- Translation succeeds with fake AI client.
- Empty input skips AI.
- Same-language translation returns original text without AI.
- Unsupported language returns HTTP 400.
- Failed AI response returns a clear API error.
- Successful translations are saved to history.
- History retention limit is enforced.
- Settings update validates provider/model.
- AI probe handles success and provider failure.

## Explicit Non-Goals

- No file upload.
- No OCR.
- No speech input or text-to-speech.
- No user accounts.
- No external database.
- No deployment packaging beyond local FastAPI/Uvicorn.
- No automatic source-language detection.
