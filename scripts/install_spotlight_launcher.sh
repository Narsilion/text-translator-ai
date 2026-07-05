#!/bin/zsh

set -e

PROJECT_DIR="/Users/darkcreation/Documents/git_repos/text-translator-ai"
APP_DIR="${HOME}/Applications/Text Translator AI.app"
LAUNCHER_SCRIPT="${PROJECT_DIR}/scripts/launch_text_translator_ai.sh"

mkdir -p "${HOME}/Applications"
rm -rf "${APP_DIR}"

chmod +x "${LAUNCHER_SCRIPT}"
/usr/bin/osacompile -o "${APP_DIR}" -e "do shell script quoted form of \"${LAUNCHER_SCRIPT}\""

echo "Installed ${APP_DIR}"
echo "Open it from Spotlight by searching for: Text Translator AI"
