from __future__ import annotations

import json

from text_translator_ai.schemas import SUPPORTED_LANGUAGES, SettingsRecord, TranslationRecord


CONTEXT_TOPICS = (
    "General",
    "News / journalism",
    "Medicine",
    "Pregnancy & childbirth",
    "Legal",
    "Technology",
    "Finance",
    "Business",
    "Travel",
    "Education",
    "Literature",
    "Marketing",
    "Customer support",
    "Government",
    "Science",
    "Software",
    "Informal conversation",
    "Custom",
)


def _shared_styles() -> str:
    return """
      :root {
        --bg-top: #0c1220;
        --bg-bottom: #04070d;
        --surface: rgba(17, 24, 39, 0.88);
        --surface-strong: rgba(25, 34, 52, 0.94);
        --ink: #edf2f7;
        --muted: #9aa8bd;
        --accent: #48b2ff;
        --accent-strong: #1b75d0;
        --line: rgba(154, 168, 189, 0.2);
        --input-bg: rgba(6, 10, 18, 0.9);
        --source-bg: rgba(7, 14, 28, 0.98);
        --translation-line: rgba(72, 178, 255, 0.28);
        --danger: #ff7a7a;
        --success: #60d394;
        --shadow: 0 18px 60px rgba(0, 0, 0, 0.34);
      }
      body[data-theme="dark_green"] {
        --bg-top: #071812;
        --bg-bottom: #020906;
        --surface: rgba(8, 28, 20, 0.88);
        --surface-strong: rgba(13, 43, 30, 0.94);
        --ink: #eef8f2;
        --muted: #9db7aa;
        --accent: #41c982;
        --accent-strong: #208f5d;
        --line: rgba(157, 183, 170, 0.22);
        --input-bg: rgba(2, 12, 8, 0.9);
        --source-bg: rgba(2, 13, 9, 0.98);
        --translation-line: rgba(65, 201, 130, 0.3);
      }
      body[data-theme="dark_brown"] {
        --bg-top: #19100a;
        --bg-bottom: #090402;
        --surface: rgba(35, 22, 14, 0.88);
        --surface-strong: rgba(51, 32, 20, 0.94);
        --ink: #f7efe7;
        --muted: #c0a996;
        --accent: #d18a4f;
        --accent-strong: #9c5f32;
        --line: rgba(192, 169, 150, 0.22);
        --input-bg: rgba(16, 8, 4, 0.9);
        --source-bg: rgba(17, 8, 4, 0.98);
        --translation-line: rgba(209, 138, 79, 0.32);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        color: var(--ink);
        font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
        font-size: 14px;
        line-height: 1.45;
        background:
          radial-gradient(circle at top left, rgba(72, 178, 255, 0.12), transparent 30%),
          linear-gradient(160deg, var(--bg-top), var(--bg-bottom));
        min-height: 100vh;
      }
      button, select, textarea {
        font: inherit;
      }
      .page {
        width: min(1180px, calc(100vw - 28px));
        margin: 18px auto 40px;
      }
      .nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding: 14px 16px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(5, 9, 16, 0.72);
        box-shadow: var(--shadow);
      }
      .brand {
        display: grid;
        gap: 2px;
      }
      .brand strong {
        font-size: 18px;
      }
      .brand span, .status, .hint {
        color: var(--muted);
        font-size: 12px;
      }
      .nav-actions {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      a, .link-button {
        color: var(--ink);
        text-decoration: none;
      }
      .button, button, .link-button {
        border: 1px solid var(--line);
        border-radius: 7px;
        background: var(--surface-strong);
        color: var(--ink);
        padding: 9px 12px;
        cursor: pointer;
      }
      .button-primary {
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        border-color: transparent;
        color: white;
      }
      .toolbar {
        margin-top: 16px;
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
        gap: 12px;
        align-items: end;
      }
      .context-toolbar {
        margin-top: 12px;
        display: grid;
        grid-template-columns: minmax(220px, 320px) minmax(260px, 1fr);
        gap: 12px;
        align-items: end;
      }
      .context-status {
        margin-top: 8px;
        min-height: 18px;
        color: var(--muted);
        font-size: 12px;
      }
      .context-status strong {
        color: var(--ink);
        font-weight: 700;
      }
      label {
        display: grid;
        gap: 7px;
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      select, textarea {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--input-bg);
        color: var(--ink);
        outline: none;
      }
      select {
        padding: 10px 12px;
      }
      input {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--input-bg);
        color: var(--ink);
        outline: none;
        padding: 10px 12px;
        font: inherit;
      }
      textarea {
        min-height: 360px;
        resize: vertical;
        padding: 16px;
        line-height: 1.55;
        font-size: 16px;
      }
      textarea[readonly] {
        color: var(--ink);
      }
      .panels {
        margin-top: 14px;
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .panel, .history, .settings-grid > section {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        box-shadow: var(--shadow);
      }
      .panel-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        border-bottom: 1px solid var(--line);
      }
      .panel-title {
        font-weight: 700;
      }
      .panel-body {
        padding: 0;
      }
      .panel-body textarea {
        border: 0;
        border-radius: 0 0 8px 8px;
        background: transparent;
      }
      #sourceText {
        background: var(--source-bg);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
      }
      #translatedText {
        background: var(--source-bg);
        border-top: 1px solid var(--translation-line);
        color: var(--ink);
      }
      .history {
        margin-top: 14px;
        padding: 16px;
      }
      .history h2, .settings-grid h2 {
        margin: 0 0 12px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--muted);
      }
      .history-list {
        display: grid;
        gap: 10px;
      }
      .history-list[hidden] {
        display: none;
      }
      .history-item {
        display: grid;
        gap: 4px;
        padding: 12px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface-strong);
      }
      .history-langs {
        color: var(--muted);
        font-size: 12px;
      }
      .settings-grid {
        margin-top: 16px;
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(320px, 0.75fr);
        gap: 14px;
      }
      .settings-grid > section {
        padding: 16px;
      }
      .form-grid {
        display: grid;
        gap: 14px;
      }
      .form-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .message {
        margin-top: 12px;
        min-height: 20px;
        color: var(--muted);
      }
      .message[data-kind="error"] { color: var(--danger); }
      .message[data-kind="success"] { color: var(--success); }
      pre {
        white-space: pre-wrap;
        word-break: break-word;
        color: var(--muted);
        margin: 0;
      }
      @media (max-width: 760px) {
        .nav, .toolbar, .context-toolbar, .panels, .settings-grid {
          grid-template-columns: 1fr;
          display: grid;
        }
        .nav-actions {
          justify-content: flex-start;
        }
        textarea {
          min-height: 260px;
        }
      }
    """


def _language_options(selected: str) -> str:
    return "\n".join(
        f'<option value="{language}"{" selected" if language == selected else ""}>{language}</option>'
        for language in SUPPORTED_LANGUAGES
    )


def _context_topic_options(selected: str = "General") -> str:
    return "\n".join(
        f'<option value="{_escape(topic)}"{" selected" if topic == selected else ""}>{_escape(topic)}</option>'
        for topic in CONTEXT_TOPICS
    )


def render_translator_page(settings: SettingsRecord, history: list[TranslationRecord]) -> str:
    state = {
        "settings": settings.model_dump(mode="json"),
        "history": [record.model_dump(mode="json") for record in history],
    }
    history_markup = _render_history(history)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Text Translator AI</title>
    <style>{_shared_styles()}</style>
  </head>
  <body data-theme="{settings.ui_theme}">
    <div class="page">
      <nav class="nav">
        <div class="brand">
          <strong>Text Translator AI</strong>
          <span>{settings.active_ai_provider} / {settings.active_model}</span>
        </div>
        <div class="nav-actions">
          <span class="status" id="statusText">Ready</span>
          <a class="button" href="/settings">Settings</a>
        </div>
      </nav>

      <div class="toolbar">
        <label>Source language
          <select id="sourceLanguage">{_language_options("Russian")}</select>
        </label>
        <button id="swapButton" title="Swap languages" aria-label="Swap languages">⇄</button>
        <label>Target language
          <select id="targetLanguage">{_language_options("Serbian")}</select>
        </label>
      </div>

      <div class="context-toolbar">
        <label>Translation context
          <select id="contextTopic">{_context_topic_options()}</select>
        </label>
        <label id="customContextLabel" hidden>Custom topic
          <input id="customContext" type="text" maxlength="120" placeholder="Enter translation topic">
        </label>
      </div>
      <div class="context-status" id="contextStatus" aria-live="polite"></div>

      <main class="panels">
        <section class="panel">
          <div class="panel-head">
            <span class="panel-title">Source</span>
            <button id="clearButton">Clear</button>
          </div>
          <div class="panel-body">
            <textarea id="sourceText" placeholder="Enter text to translate"></textarea>
          </div>
        </section>
        <section class="panel">
          <div class="panel-head">
            <span class="panel-title">Translation</span>
            <button id="copyButton">Copy</button>
          </div>
          <div class="panel-body">
            <textarea id="translatedText" readonly placeholder="Translation appears here"></textarea>
          </div>
        </section>
      </main>

      <section class="history">
        <div class="panel-head" style="padding:0 0 12px;border-bottom:0;">
          <h2>Recent history</h2>
          <div class="nav-actions">
            <button id="toggleHistoryButton" aria-expanded="false">Show History</button>
            <button id="clearHistoryButton">Clear History</button>
          </div>
        </div>
        <div class="history-list" id="historyList" hidden>{history_markup}</div>
      </section>
    </div>
    <script id="app-state" type="application/json">{json.dumps(state)}</script>
    <script>
      const sourceLanguage = document.querySelector('#sourceLanguage');
      const targetLanguage = document.querySelector('#targetLanguage');
      const sourceText = document.querySelector('#sourceText');
      const translatedText = document.querySelector('#translatedText');
      const contextTopic = document.querySelector('#contextTopic');
      const customContext = document.querySelector('#customContext');
      const customContextLabel = document.querySelector('#customContextLabel');
      const contextStatus = document.querySelector('#contextStatus');
      const statusText = document.querySelector('#statusText');
      const historyList = document.querySelector('#historyList');
      const toggleHistoryButton = document.querySelector('#toggleHistoryButton');
      const draftStorageKey = 'text-translator-ai:draft-v2';
      let debounceTimer = null;
      let requestId = 0;

      function setStatus(text) {{
        statusText.textContent = text;
      }}

      function saveDraft() {{
        localStorage.setItem(draftStorageKey, JSON.stringify({{
          sourceText: sourceText.value,
          translatedText: translatedText.value,
          sourceLanguage: sourceLanguage.value,
          targetLanguage: targetLanguage.value,
          contextTopic: contextTopic.value,
          customContext: customContext.value
        }}));
      }}

      function restoreDraft() {{
        const rawDraft = localStorage.getItem(draftStorageKey);
        if (!rawDraft) return;
        try {{
          const draft = JSON.parse(rawDraft);
          if (draft.sourceLanguage) sourceLanguage.value = draft.sourceLanguage;
          if (draft.targetLanguage) targetLanguage.value = draft.targetLanguage;
          if (draft.contextTopic) contextTopic.value = draft.contextTopic;
          if (typeof draft.customContext === 'string') customContext.value = draft.customContext;
          updateCustomContextVisibility();
          if (typeof draft.sourceText === 'string') sourceText.value = draft.sourceText;
          if (typeof draft.translatedText === 'string') translatedText.value = draft.translatedText;
          if (sourceText.value || translatedText.value) setStatus('Draft restored');
        }} catch (error) {{
          localStorage.removeItem(draftStorageKey);
        }}
      }}

      function clearDraft() {{
        localStorage.removeItem(draftStorageKey);
      }}

      function activeTranslationContext() {{
        if (contextTopic.value === 'General') return '';
        return contextTopic.value === 'Custom' ? customContext.value.trim() : contextTopic.value;
      }}

      function updateCustomContextVisibility() {{
        const isCustom = contextTopic.value === 'Custom';
        customContextLabel.hidden = !isCustom;
        customContext.disabled = !isCustom;
        if (!isCustom) customContext.value = '';
        updateContextStatus();
      }}

      function updateContextStatus() {{
        const activeContext = activeTranslationContext();
        if (!activeContext) {{
          contextStatus.innerHTML = 'Active context: <strong>General</strong>';
          return;
        }}
        contextStatus.innerHTML = `Active context: <strong>${{escapeHtml(activeContext)}}</strong>`;
      }}

      function renderHistory(items) {{
        if (!items.length) {{
          historyList.innerHTML = '<div class="hint">No translations yet.</div>';
          return;
        }}
        historyList.innerHTML = items.map(item => `
          <article class="history-item">
            <div class="history-langs">${{item.source_language}} → ${{item.target_language}} · ${{item.model}}${{formatSeconds(item.translation_seconds)}}</div>
            ${{item.translation_context ? `<div class="history-langs">Context: ${{escapeHtml(item.translation_context)}}</div>` : ''}}
            <strong>${{escapeHtml(item.source_text).slice(0, 180)}}</strong>
            <div>${{escapeHtml(item.translated_text).slice(0, 240)}}</div>
          </article>
        `).join('');
      }}

      function formatSeconds(value) {{
        return typeof value === 'number' ? ` · ${{value.toFixed(2)}}s` : '';
      }}

      function escapeHtml(value) {{
        return String(value).replace(/[&<>"']/g, char => ({{
          '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }}[char]));
      }}

      async function refreshHistory() {{
        const response = await fetch('/api/history');
        if (response.ok) {{
          renderHistory(await response.json());
        }}
      }}

      async function translateNow() {{
        const text = sourceText.value;
        const currentId = ++requestId;
        if (!text.trim()) {{
          translatedText.value = '';
          saveDraft();
          setStatus('Ready');
          return;
        }}
        setStatus('Translating...');
        const response = await fetch('/api/translate', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{
            source_text: text,
            source_language: sourceLanguage.value,
            target_language: targetLanguage.value,
            translation_context: activeTranslationContext()
          }})
        }});
        if (currentId !== requestId) return;
        const payload = await response.json();
        if (!response.ok || payload.status === 'failed') {{
          translatedText.value = '';
          setStatus(payload.error || payload.detail || 'Translation failed');
          return;
        }}
        translatedText.value = payload.translated_text;
        saveDraft();
        const timing = formatSeconds(payload.translation_seconds);
        setStatus(payload.status === 'copied' ? `Copied source text${{timing}}` : `Translated${{timing}}`);
        if (payload.status === 'success') refreshHistory();
      }}

      function queueTranslate() {{
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(translateNow, 650);
      }}

      function queueContextRetranslate() {{
        saveDraft();
        if (sourceText.value.trim()) setStatus('Context changed, retranslating...');
        queueTranslate();
      }}

      restoreDraft();
      updateCustomContextVisibility();
      sourceText.addEventListener('input', () => {{
        saveDraft();
        queueTranslate();
      }});
      sourceLanguage.addEventListener('change', () => {{
        saveDraft();
        queueTranslate();
      }});
      targetLanguage.addEventListener('change', () => {{
        saveDraft();
        queueTranslate();
      }});
      contextTopic.addEventListener('change', () => {{
        updateCustomContextVisibility();
        if (contextTopic.value === 'Custom') {{
          saveDraft();
          customContext.focus();
          setStatus(sourceText.value.trim() ? 'Enter a custom topic to retranslate' : 'Ready');
          return;
        }}
        queueContextRetranslate();
      }});
      customContext.addEventListener('input', () => {{
        updateContextStatus();
        if (!customContext.value.trim()) {{
          saveDraft();
          setStatus(sourceText.value.trim() ? 'Enter a custom topic to retranslate' : 'Ready');
          return;
        }}
        queueContextRetranslate();
      }});
      document.querySelector('#swapButton').addEventListener('click', () => {{
        const oldSource = sourceLanguage.value;
        sourceLanguage.value = targetLanguage.value;
        targetLanguage.value = oldSource;
        const oldText = sourceText.value;
        sourceText.value = translatedText.value;
        translatedText.value = oldText;
        saveDraft();
        queueTranslate();
      }});
      document.querySelector('#clearButton').addEventListener('click', () => {{
        sourceText.value = '';
        translatedText.value = '';
        clearDraft();
        setStatus('Ready');
        requestId++;
        sourceText.focus();
      }});
      document.querySelector('#copyButton').addEventListener('click', async () => {{
        await navigator.clipboard.writeText(translatedText.value);
        setStatus('Copied');
      }});
      toggleHistoryButton.addEventListener('click', () => {{
        const isCollapsed = historyList.hidden;
        historyList.hidden = !isCollapsed;
        toggleHistoryButton.setAttribute('aria-expanded', String(isCollapsed));
        toggleHistoryButton.textContent = isCollapsed ? 'Hide History' : 'Show History';
      }});
      document.querySelector('#clearHistoryButton').addEventListener('click', async () => {{
        await fetch('/api/history', {{method: 'DELETE'}});
        renderHistory([]);
      }});
    </script>
  </body>
</html>"""


def render_settings_page(settings: SettingsRecord) -> str:
    state = {"settings": settings.model_dump(mode="json")}
    provider_options = "\n".join(
        f'<option value="{provider}"{" selected" if provider == settings.active_ai_provider else ""}>{provider}</option>'
        for provider in settings.available_ai_providers
    )
    theme_options = "\n".join(
        f'<option value="{theme}"{" selected" if theme == settings.ui_theme else ""}>{theme}</option>'
        for theme in ("dark", "dark_green", "dark_brown")
    )
    model_options = "\n".join(
        f'<option value="{model}"{" selected" if model == settings.active_model else ""}>{model}</option>'
        for model in settings.available_models
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Settings · Text Translator AI</title>
    <style>{_shared_styles()}</style>
  </head>
  <body data-theme="{settings.ui_theme}">
    <div class="page">
      <nav class="nav">
        <div class="brand">
          <strong>Settings</strong>
          <span>Text Translator AI</span>
        </div>
        <div class="nav-actions">
          <a class="button" href="/">Home</a>
        </div>
      </nav>

      <main class="settings-grid">
        <section>
          <h2>AI Settings</h2>
          <div class="form-grid">
            <label>Provider
              <select id="providerSelect">{provider_options}</select>
            </label>
            <label>Model
              <select id="modelSelect">{model_options}</select>
            </label>
            <div class="form-actions">
              <button class="button-primary" id="saveButton">Save</button>
              <button id="refreshModelsButton">Refresh Models</button>
              <button id="probeButton">AI Probe</button>
            </div>
            <div class="message" id="settingsMessage"></div>
          </div>
        </section>
        <section>
          <h2>Appearance</h2>
          <div class="form-grid">
            <label>Theme
              <select id="themeSelect">{theme_options}</select>
            </label>
            <div class="hint">Theme changes preview immediately and are saved with the main Save button.</div>
          </div>
        </section>
      </main>
    </div>
    <script id="app-state" type="application/json">{json.dumps(state)}</script>
    <script>
      const initialState = JSON.parse(document.querySelector('#app-state').textContent);
      const providerSelect = document.querySelector('#providerSelect');
      const modelSelect = document.querySelector('#modelSelect');
      const themeSelect = document.querySelector('#themeSelect');
      const settingsMessage = document.querySelector('#settingsMessage');
      let modelsByProvider = initialState.settings.available_models_by_provider;

      function setMessage(text, kind = '') {{
        settingsMessage.textContent = text;
        settingsMessage.dataset.kind = kind;
      }}

      function fillModels(provider, selected = null) {{
        const models = modelsByProvider[provider] || [];
        modelSelect.innerHTML = models.map(model => `<option value="${{model}}">${{model}}</option>`).join('');
        if (selected && models.includes(selected)) modelSelect.value = selected;
      }}

      function refreshButtonLabel() {{
        document.querySelector('#refreshModelsButton').textContent = 'Refresh Models';
      }}

      providerSelect.addEventListener('change', () => {{
        fillModels(providerSelect.value);
        refreshButtonLabel();
      }});
      themeSelect.addEventListener('change', () => {{
        document.body.dataset.theme = themeSelect.value;
      }});
      document.querySelector('#refreshModelsButton').addEventListener('click', async () => {{
        setMessage('Refreshing models...');
        const response = await fetch(`/api/settings/models?provider=${{encodeURIComponent(providerSelect.value)}}`);
        const payload = await response.json();
        modelsByProvider[payload.provider] = payload.models;
        fillModels(payload.provider, payload.models[0]);
        setMessage(payload.detail || `Loaded ${{payload.models.length}} models from ${{payload.source}}.`, payload.source === 'fallback' ? 'error' : 'success');
      }});
      document.querySelector('#saveButton').addEventListener('click', async () => {{
        setMessage('Saving...');
        const response = await fetch('/api/settings', {{
          method: 'PUT',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{
            active_ai_provider: providerSelect.value,
            active_model: modelSelect.value,
            ui_theme: themeSelect.value
          }})
        }});
        const payload = await response.json();
        if (!response.ok) {{
          setMessage(payload.detail || 'Settings were not saved.', 'error');
          return;
        }}
        modelsByProvider = payload.available_models_by_provider;
        setMessage('Settings saved.', 'success');
      }});
      document.querySelector('#probeButton').addEventListener('click', async () => {{
        setMessage('Probing selected model...');
        const response = await fetch('/api/settings/ai-probe', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{
            active_ai_provider: providerSelect.value,
            active_model: modelSelect.value
          }})
        }});
        const payload = await response.json();
        setMessage(payload.detail || `Probe ${{payload.status}} for ${{payload.provider}} / ${{payload.model}}.`, payload.status === 'ok' ? 'success' : 'error');
      }});
      refreshButtonLabel();
    </script>
  </body>
</html>"""


def _render_history(history: list[TranslationRecord]) -> str:
    if not history:
        return '<div class="hint">No translations yet.</div>'
    items = []
    for record in history:
        context_markup = (
            f"<div class=\"history-langs\">Context: {_escape(record.translation_context)}</div>"
            if record.translation_context
            else ""
        )
        items.append(
            "<article class=\"history-item\">"
            f"<div class=\"history-langs\">{record.source_language} -> {record.target_language} · {record.model}{_format_seconds(record.translation_seconds)}</div>"
            f"{context_markup}"
            f"<strong>{_escape(record.source_text[:180])}</strong>"
            f"<div>{_escape(record.translated_text[:240])}</div>"
            "</article>"
        )
    return "\n".join(items)


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


def _format_seconds(value: float | None) -> str:
    if value is None:
        return ""
    return f" · {value:.2f}s"
