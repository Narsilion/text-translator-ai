# Text Translator AI

Local-first AI-backed text translator with a Google Translate-style two-panel UI.

## Features

- manual source and target language selection
- automatic translation after typing pauses
- OpenAI or GitHub Models-backed translation
- local SQLite settings and recent history
- settings page with provider, model, theme, diagnostics, model refresh, and AI probe

## Requirements

- Python 3.14+
- `OPENAI_API_KEY` or `GITHUB_MODELS_TOKEN`/`GITHUB_TOKEN` for real AI translation

## Setup

```bash
cd /Users/darkcreation/Documents/git_repos/text-translator-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
export OPENAI_API_KEY="your_api_key_here"
```

GitHub Models is the default provider. Configure a token with:

```bash
export TTA_AI_PROVIDER="github"
export GITHUB_MODELS_TOKEN="your_github_models_token"
```

## Run

```bash
.venv/bin/text-translator-ai
```

Default URL: `http://127.0.0.1:8770`

## Spotlight Launcher

Install the macOS Spotlight launcher once:

```bash
scripts/install_spotlight_launcher.sh
```

After that, press Spotlight, type `Text Translator AI`, and press Enter. The launcher will:

- source `~/.zshrc` so your existing AI token settings are available
- create `.venv` and install the app if needed
- start the local server if it is not already running
- open `http://127.0.0.1:8770`

Launcher logs are written to `.data/launcher.log`. Server logs are written to `.data/server.log`.

## Environment

- `OPENAI_API_KEY` required for real OpenAI translation
- `TTA_AI_PROVIDER` default `github`; set to `openai` for OpenAI
- `GITHUB_MODELS_TOKEN` or `GITHUB_TOKEN` required for real GitHub Models translation
- `TTA_GITHUB_MODELS` comma-separated GitHub Models fallback list, default `openai/gpt-4o,openai/gpt-4o-mini,mistral-ai/mistral-small-2503,mistral-ai/mistral-medium-2505,mistral-ai/ministral-3b`
- `TTA_MODEL` default `openai/gpt-4o`
- `TTA_HOST` default `127.0.0.1`
- `TTA_PORT` default `8770`
- `TTA_DB_PATH` default `./.data/text-translator-ai.db`
- `TTA_HISTORY_LIMIT` default `100`

For GitHub Models, the model dropdown can be refreshed from the GitHub catalog. Some catalog entries can be listed globally but unavailable to a specific token at inference time, so use the AI Probe button on a selected model before saving it.

## Tests

```bash
pytest
```
