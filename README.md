# Soulseek Music Organizer

A macOS tool that automatically moves finished Soulseek downloads into dated folders in `~/Music`.

## What it does

Watches your Soulseek downloads folder and organizes completed music files into dated folders in `~/Music`.

**First run:** copies all existing files into a folder named after today's date (e.g. `Music downloaded 18-5`). Originals stay in the Soulseek folder — DJ software like rekordbox keeps its file path references intact. The first-run date is saved to `~/.soulseek-organizer-initialized`.

**Same day as first run:** new downloads are copied to the dated folder, originals kept.

**Any day after first run:** new downloads are copied to that day's folder, then the original is deleted from the Soulseek folder — keeping it clean going forward.

## Usage

A desktop icon controls the organizer:

- **Click once** — starts the organizer, shows a notification
- **Click again** — prompts to stop it

Does not start on login or restart automatically. Only runs when you start it.

## Install

```bash
bash install.sh
```

Then double-click **Soulseek Organizer** on your Desktop to start.

## Requirements

- macOS (Apple Silicon)
- [Soulseek (Nicotine+)](https://nicotine-plus.org/) with download folder set to `~/soulseek downloads/complete`
- Python 3 (via Homebrew: `brew install python3`)

## Logs

```
~/Library/Logs/soulseek-organizer.log
~/Library/Logs/soulseek-organizer-error.log
```

## Supported formats

`.mp3` `.flac` `.m4a` `.ogg` `.wav` `.aiff` `.aif` `.aac` `.wma` `.ape` `.opus` `.alac` `.dsf` `.dff`

## How it works

- Uses Python's `watchdog` library to monitor the downloads folder
- Waits for each file to finish writing (size stable for 5s) before copying
- Copies files — originals remain in the Soulseek download folder
- Handles filename collisions by appending `(1)`, `(2)`, etc.
