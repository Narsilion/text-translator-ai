#!/bin/zsh

set -e

PROJECT_DIR="/Users/darkcreation/Documents/git_repos/text-translator-ai"
APP_DIR="${HOME}/Applications/Text Translator AI.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
LAUNCHER_SCRIPT="${PROJECT_DIR}/scripts/launch_text_translator_ai.sh"
APP_EXECUTABLE="${MACOS_DIR}/Text Translator AI"
PLIST_FILE="${CONTENTS_DIR}/Info.plist"

mkdir -p "${MACOS_DIR}"

cat > "${PLIST_FILE}" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Text Translator AI</string>
  <key>CFBundleDisplayName</key>
  <string>Text Translator AI</string>
  <key>CFBundleIdentifier</key>
  <string>local.text-translator-ai.launcher</string>
  <key>CFBundleVersion</key>
  <string>1.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleExecutable</key>
  <string>Text Translator AI</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
</dict>
</plist>
PLIST

cat > "${APP_EXECUTABLE}" <<APP
#!/bin/zsh
exec "${LAUNCHER_SCRIPT}"
APP

chmod +x "${LAUNCHER_SCRIPT}" "${APP_EXECUTABLE}"

echo "Installed ${APP_DIR}"
echo "Open it from Spotlight by searching for: Text Translator AI"
