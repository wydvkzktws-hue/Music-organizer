# Session Context — Soulseek Music Organizer

## Project

macOS tool that organizes completed Soulseek downloads into dated `~/Music` folders.
Repo: https://github.com/wydvkzktws-hue/Music-organizer (latest: v1.3.0)

## Key paths

| What | Path |
|------|------|
| Script | `/Users/alemendes/Music organizer/Music-organizer/soulseek_organizer.py` |
| Venv python | `/Users/alemendes/Music organizer/Music-organizer/.venv/bin/python3` |
| Watch dir | `/Users/alemendes/soulseek downloads/complete` |
| Dest root | `~/Music` |
| Folder format | `Music downloaded {day}-{month}` (e.g. `Music downloaded 19-5`) |
| Logs | `~/Library/Logs/soulseek-organizer.log` / `…-error.log` |
| First-run flag | `~/.soulseek-organizer-initialized` (contains date: `YYYY-MM-DD`) |
| Desktop icon | `~/Desktop/Soulseek Organizer.app` |

## Current behavior

- **First run** (flag absent): copies all existing music files in watch dir → today's dated folder. Writes today's date to flag file.
- **Same day as first run**: new downloads copied → dated folder. Originals kept.
- **Any later day**: new downloads copied → dated folder. Originals deleted from Soulseek folder.
- Watchdog triggers on `on_created` + `on_moved` (Soulseek renames `.tmp` → final on completion).
- No auto-start on login. No keep-alive. Icon is the only way to start/stop.

## Start / stop

```bash
# Start
nohup "/Users/alemendes/Music organizer/Music-organizer/.venv/bin/python3" \
  "/Users/alemendes/Music organizer/Music-organizer/soulseek_organizer.py" \
  >> ~/Library/Logs/soulseek-organizer.log 2>> ~/Library/Logs/soulseek-organizer-error.log &

# Stop
pkill -f "soulseek_organizer.py"

# Check
pgrep -f "soulseek_organizer.py"
```

Or click `Soulseek Organizer.app` on Desktop (toggle start/stop).

## Critical rules

1. **Never call `scan_existing()` manually** — it re-copies everything and resets the flag date.
2. **Never re-enable `RunAtLoad`/`KeepAlive`** in plist — user wants manual control only.
3. **`shutil.copy2` not `shutil.move`** — files are copied, not moved (except post-first-run-day originals which are deleted after copy).
4. **rekordbox owns the soulseek/complete folder** — never bulk-delete or move pre-existing files outside of the defined behavior above.

## Files in repo

| File | Purpose |
|------|---------|
| `soulseek_organizer.py` | Main watcher |
| `com.ale.soulseek-organizer.plist` | launchd config (RunAtLoad/KeepAlive both false) |
| `install.sh` | Installer (sets up venv, installs watchdog, copies plist) |
| `CLAUDE.md` | Design reference |
| `SESSION_CONTEXT.md` | This file |

## Release history

| Version | Change |
|---------|--------|
| v1.0.0 | Initial release |
| v1.1.0 | Manual start via icon, no auto-start |
| v1.2.0 | Copy instead of move |
| v1.3.0 | Delete originals only on days after first run |
