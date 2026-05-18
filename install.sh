#!/usr/bin/env bash
set -euo pipefail

PLIST_NAME="com.ale.soulseek-organizer.plist"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/$PLIST_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"
LABEL="com.ale.soulseek-organizer"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV/bin/python3"

echo "==> Installing Soulseek Music Organizer"

# 1. Create venv if needed and install watchdog
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "==> Creating virtual environment..."
    /opt/homebrew/bin/python3 -m venv "$VENV"
fi
echo "==> Installing watchdog..."
"$VENV/bin/pip" install --quiet watchdog

# 3. Copy plist
echo "==> Installing launchd agent..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DEST"

# 4. Unload existing instance if running, then load
if launchctl list | grep -q "$LABEL" 2>/dev/null; then
    echo "==> Stopping existing agent..."
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
fi

launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"

echo ""
echo "Done! Agent '$LABEL' is running."
echo "Logs: ~/Library/Logs/soulseek-organizer.log"
echo ""
echo "To check status:  launchctl list $LABEL"
echo "To stop:          launchctl bootout gui/\$(id -u)/$LABEL"
echo "To start:         launchctl bootstrap gui/\$(id -u) $PLIST_DEST"
