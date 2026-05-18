# Soulseek Music Organizer

A macOS background agent that automatically moves finished Soulseek downloads into dated folders in `~/Music`.

## What it does

Watches your Soulseek downloads folder and moves completed music files into dated folders in `~/Music`.

**First run:** moves all existing files in the downloads folder into a folder named after today's date (e.g. `Music downloaded 18-5`). This only happens once — a flag file at `~/.soulseek-organizer-initialized` marks it done.

**Every run after:** only newly completed downloads are moved, into a folder named after the date they arrive (e.g. `Music downloaded 19-5`, `Music downloaded 25-5`).

Source folder structure inside the Soulseek downloads directory is never deleted — only the music files are moved.

Runs silently in the background via launchd — starts on login, restarts if it crashes.

## Requirements

- macOS (Apple Silicon)
- [Soulseek (Nicotine+)](https://nicotine-plus.org/) with download folder set to `~/soulseek downloads/complete`
- Python 3 (via Homebrew: `brew install python3`)

## Install

```bash
bash install.sh
```

That's it. The organizer starts immediately and runs on every login.

## Manage the agent

```bash
# Check if running
launchctl list com.ale.soulseek-organizer

# Stop permanently
launchctl bootout "gui/$(id -u)/com.ale.soulseek-organizer"

# Start again
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ale.soulseek-organizer.plist
```

## Logs

```
~/Library/Logs/soulseek-organizer.log
~/Library/Logs/soulseek-organizer-error.log
```

## Supported formats

`.mp3` `.flac` `.m4a` `.ogg` `.wav` `.aiff` `.aif` `.aac` `.wma` `.ape` `.opus` `.alac` `.dsf` `.dff`

## How it works

- Uses Python's `watchdog` library to monitor the downloads folder
- Waits for each file to finish writing (size stable for 5s) before moving
- Deletes empty source subfolders after each move
- Handles filename collisions by appending `(1)`, `(2)`, etc.
