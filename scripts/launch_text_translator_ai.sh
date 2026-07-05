#!/bin/zsh

set -e

PROJECT_DIR="/Users/darkcreation/Documents/git_repos/text-translator-ai"
PYTHON_BIN="/usr/local/bin/python3"
APP_URL="http://127.0.0.1:8770"
HEALTH_URL="${APP_URL}/api/health"
DATA_DIR="${PROJECT_DIR}/.data"
LAUNCHER_LOG="${DATA_DIR}/launcher.log"
SERVER_LOG="${DATA_DIR}/server.log"

mkdir -p "${DATA_DIR}"
exec >> "${LAUNCHER_LOG}" 2>&1

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

health_ok() {
  /usr/bin/curl -fsS --max-time 2 "${HEALTH_URL}" >/dev/null
}

wait_for_health() {
  local attempt
  for attempt in {1..30}; do
    if health_ok; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

log "Launcher invoked"

if [[ -f "${HOME}/.zshrc" ]]; then
  log "Sourcing ${HOME}/.zshrc"
  set +e
  source "${HOME}/.zshrc"
  set -e
fi

cd "${PROJECT_DIR}"

if health_ok; then
  log "Server already running"
  log "Opening ${APP_URL}"
  /usr/bin/open "${APP_URL}"
  exit 0
fi

if [[ ! -x ".venv/bin/text-translator-ai" ]]; then
  log "Creating/updating project virtual environment"
  "${PYTHON_BIN}" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
fi

log "Starting Text Translator AI server"
nohup .venv/bin/text-translator-ai > "${SERVER_LOG}" 2>&1 &
if ! wait_for_health; then
  log "Server did not become healthy; see ${SERVER_LOG}"
  exit 1
fi

log "Opening ${APP_URL}"
/usr/bin/open "${APP_URL}"
