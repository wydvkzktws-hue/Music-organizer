# Session Context — Soulseek Music Organizer

Read this file at the start of a new session to restore full context.

---

## What this project is

macOS background agent that watches `/Users/alemendes/soulseek downloads/complete` (Soulseek P2P app's finished downloads folder) and automatically moves music files to `~/Music/Music downloaded DD-M/` (e.g. `Music downloaded 18-5`). Empty source subfolders are deleted after each move.

---

## Files in the repo (`/Users/alemendes/Music organizer/Music-organizer/`)

| File | Purpose |
|------|---------|
| `soulseek_organizer.py` | Main watcher script (watchdog-based) |
| `com.ale.soulseek-organizer.plist` | launchd agent config |
| `install.sh` | One-shot installer |
| `CLAUDE.md` | Project reference doc |
| `restore_files.py` | One-shot script used to restore files from first accidental scan (keep for reference, do not re-run) |
| `restore2.py` | Second restore script used after launchd conflict (keep for reference, do not re-run) |
| `.venv/` | Python venv with watchdog installed |

---

## Key paths (all hardcoded)

- **python3**: `/opt/homebrew/bin/python3` (Apple Silicon Homebrew, Python 3.14.4)
- **venv python**: `/Users/alemendes/Music organizer/Music-organizer/.venv/bin/python3`
- **Watch dir**: `/Users/alemendes/soulseek downloads/complete`
- **Dest root**: `~/Music`
- **Dest folder format**: `Music downloaded {day}-{month}` — e.g. `Music downloaded 18-5` (no year, no leading zeros)
- **Logs**: `~/Library/Logs/soulseek-organizer.log` and `…-error.log`
- **plist install location**: `~/Library/LaunchAgents/com.ale.soulseek-organizer.plist`

---

## How the watcher works

- Uses `watchdog` library's `FileSystemEventHandler`
- Triggers on `on_created` and `on_moved` events (Soulseek renames `.tmp` → final name on completion)
- Each file gets a daemon thread that polls size stability (5s unchanged, 300s timeout) before moving
- After move, walks up parent dirs and deletes empty ones (stops at watch root)
- Name collision handling: appends ` (1)`, ` (2)` etc.

---

## launchd agent

Label: `com.ale.soulseek-organizer`  
`KeepAlive: true` — launchd auto-restarts on crash or kill.

```bash
# Install and start
bash install.sh

# Check status
launchctl list com.ale.soulseek-organizer

# Stop (temporary — launchd will restart)
pkill -f soulseek_organizer.py

# Stop permanently (unload from launchd)
launchctl bootout "gui/$(id -u)/com.ale.soulseek-organizer"

# Reload after unload
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ale.soulseek-organizer.plist
```

---

## Current state (end of session)

- All 82 previously downloaded files are restored to their **exact original soulseek paths** with full subfolder structure intact
- `/Users/alemendes/soulseek downloads/complete` folder exists and is populated correctly
- The launchd agent is **NOT currently running** (was unloaded during recovery)
- `~/Music/Music downloaded 18-5` folder was cleaned up and deleted
- `scan_existing()` function exists in the script but is **NOT called from `main()`** — startup scan was removed because the DJ software (rekordbox) stores file paths and moving pre-existing files breaks those references

---

## Critical lessons from this session

### 1. Never run scan_existing() again
`scan_existing()` was originally added to move pre-existing files on startup. It was removed from `main()` after it broke rekordbox's file path references. The function still exists in the code but must not be re-enabled.

### 2. launchd KeepAlive restarts the watcher on kill
`pkill` alone does NOT stop the agent permanently. `launchctl bootout` is required. If you need to do any file restoration or bulk moves, **always unload launchd first**:
```bash
launchctl bootout "gui/$(id -u)/com.ale.soulseek-organizer"
```

### 3. Homebrew Python is externally managed
`pip install` fails without `--break-system-packages`. The project uses a `.venv` at the repo root. Always use `.venv/bin/python3` to run scripts, not `/opt/homebrew/bin/python3` directly.

### 4. Folder name uses dashes not slashes
`Music downloaded 18-5` not `18/05/2026`. Python's `Path` API interprets `/` as directory separators. Slashes in folder names are impossible to create programmatically on macOS.

### 5. DJ software (rekordbox) owns the soulseek/complete folder
The user's DJ software manages files in `/Users/alemendes/soulseek downloads/complete`. The organizer should only move **newly completed** downloads (via watchdog events), never bulk-scan or touch existing files.

---

## What's next / not done yet

- The launchd agent has been installed but is currently **unloaded**. Run `bash install.sh` to re-enable it.
- No git commits have been made yet — all files are untracked.
- The `restore_files.py` and `restore2.py` scripts are one-shot recovery tools and can be deleted once confirmed everything is stable.
