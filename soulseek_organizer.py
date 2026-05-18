#!/usr/bin/env python3

import shutil
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = Path("/Users/alemendes/soulseek downloads/complete")
DEST_ROOT = Path.home() / "Music"
MUSIC_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".ogg", ".wav", ".aiff", ".aif",
    ".aac", ".wma", ".ape", ".opus", ".alac", ".dsf", ".dff",
}
# Seconds the file size must remain unchanged before we consider it fully written
STABILITY_SECS = 5
STABILITY_POLL = 1.0
STABILITY_TIMEOUT = 300  # bail after 5 min if file never stabilises


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(
            Path.home() / "Library/Logs/soulseek-organizer.log"
        ),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def dest_folder() -> Path:
    now = datetime.now()
    return DEST_ROOT / f"Music downloaded {now.day}-{now.month}"


def backlog_folder() -> Path:
    now = datetime.now()
    return DEST_ROOT / f"Music downloaded before {now.day}-{now.month}"


def wait_until_stable(path: Path) -> bool:
    """Poll file size until stable for STABILITY_SECS. Returns False on timeout."""
    deadline = time.time() + STABILITY_TIMEOUT
    last_size = -1
    stable_since: float | None = None

    while time.time() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False  # file vanished (e.g. Soulseek deleted/moved it)

        if size == last_size:
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= STABILITY_SECS:
                return True
        else:
            stable_since = None

        last_size = size
        time.sleep(STABILITY_POLL)

    log.warning("Stability timeout for %s", path.name)
    return False


def unique_dest(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 1
    while dest.exists():
        dest = dest_dir / f"{stem} ({i}){suffix}"
        i += 1
    return dest


def move_file(src: Path, dest_dir: Path | None = None) -> None:
    if not src.exists():
        return

    if dest_dir is None:
        dest_dir = dest_folder()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_dest(dest_dir, src.name)

    try:
        shutil.move(str(src), str(dest))
        log.info("Moved: %s → %s", src.name, dest)
    except OSError as exc:
        log.error("Move failed for %s: %s", src, exc)
        return

    # Remove empty ancestor dirs up to (but not including) the watch root
    parent = src.parent
    while parent != WATCH_DIR:
        try:
            next(parent.iterdir())
            break  # not empty
        except StopIteration:
            try:
                parent.rmdir()
                log.info("Removed empty dir: %s", parent)
            except OSError:
                break
        parent = parent.parent


def process_file(path: Path) -> None:
    """Thread target: wait for file to be fully written, then move it."""
    if not wait_until_stable(path):
        return
    move_file(path)


def scan_existing() -> None:
    """Move any music files already in the watch dir into the backlog folder."""
    dest_dir = backlog_folder()
    found = 0
    for path in WATCH_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS and not path.name.startswith("."):
            move_file(path, dest_dir)
            found += 1
    if found:
        log.info("Startup scan: moved %d existing file(s) to %s", found, dest_dir)
    else:
        log.info("Startup scan: no existing music files found")


class MusicHandler(FileSystemEventHandler):
    def _schedule(self, path_str: str) -> None:
        path = Path(path_str)
        # Ignore tmp/partial files and hidden files
        if path.suffix.lower() not in MUSIC_EXTENSIONS:
            return
        if path.name.startswith("."):
            return
        threading.Thread(target=process_file, args=(path,), daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_moved(self, event):
        # Soulseek renames foo.mp3.tmp → foo.mp3 when download completes
        if not event.is_directory:
            self._schedule(event.dest_path)


def main() -> None:
    if not WATCH_DIR.exists():
        log.error("Watch directory does not exist: %s", WATCH_DIR)
        raise SystemExit(1)

    log.info("Watching %s", WATCH_DIR)
    observer = Observer()
    observer.schedule(MusicHandler(), str(WATCH_DIR), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
