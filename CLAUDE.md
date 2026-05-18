# Soulseek Music Organizer

macOS background agent that auto-moves finished Soulseek downloads into dated Music folders.

## What it does

Watches `/Users/alemendes/soulseek downloads/complete` via `watchdog`.  
On music file events, waits for size to stabilise (file fully written), then moves to:
```
~/Music/Music downloaded DD-MM-YYYY/
```
Empty source subdirs are deleted after the move.

## Files

| File | Purpose |
|------|---------|
| `soulseek_organizer.py` | Main watcher script |
| `com.ale.soulseek-organizer.plist` | launchd agent config |
| `install.sh` | One-shot installer |

## Key paths (hardcoded)

- **python3**: `/opt/homebrew/bin/python3` (Apple Silicon Homebrew)
- **Watch dir**: `/Users/alemendes/soulseek downloads/complete`
- **Dest root**: `~/Music`
- **Logs**: `~/Library/Logs/soulseek-organizer.log` and `…-error.log`
- **plist**: `~/Library/LaunchAgents/com.ale.soulseek-organizer.plist`

## Install / run

```bash
bash install.sh
```

## launchd commands

```bash
# Status
launchctl list com.ale.soulseek-organizer

# Stop
launchctl bootout "gui/$(id -u)/com.ale.soulseek-organizer"

# Start
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ale.soulseek-organizer.plist
```

## Design decisions

- **Folder name uses dashes** (`18-05-2026`): macOS filesystem rejects `/` in paths via Python's `Path`. Finder-displayed slashes are stored as colons internally and can't be created programmatically.
- **Stability check** (5 s unchanged size, 300 s timeout): guards against moving files Soulseek is still writing. Soulseek renames `.tmp` → final name on completion, so `on_moved` is the primary trigger; `on_created` handles edge cases.
- **Thread per file**: each file gets its own daemon thread for the stability wait — keeps the watcher non-blocking.
- **`KeepAlive: true`** in plist: launchd restarts the agent if it crashes.

## Dependencies

- Python 3 (tested on 3.14.x)
- `watchdog` (installed by install.sh via pip)

## Supported extensions

`.mp3 .flac .m4a .ogg .wav .aiff .aif .aac .wma .ape .opus .alac .dsf .dff`
