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
FIRST_RUN_FLAG = Path.home() / ".soulseek-organizer-initialized"
MUSIC_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".ogg", ".wav", ".aiff", ".aif",
    ".aac", ".wma", ".ape", ".opus", ".alac", ".dsf", ".dff",
}
STABILITY_SECS = 5
STABILITY_POLL = 1.0
STABILITY_TIMEOUT = 300


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


def wait_until_stable(path: Path) -> bool:
    deadline = time.time() + STABILITY_TIMEOUT
    last_size = -1
    stable_since: float | None = None

    while time.time() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False

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


def first_run_date() -> str | None:
    try:
        return FIRST_RUN_FLAG.read_text().strip()
    except FileNotFoundError:
        return None


def copy_file(src: Path, dest_dir: Path | None = None) -> None:
    if not src.exists():
        return

    if dest_dir is None:
        dest_dir = dest_folder()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_dest(dest_dir, src.name)

    try:
        shutil.copy2(str(src), str(dest))
        log.info("Copied: %s → %s", src.name, dest)
    except OSError as exc:
        log.error("Copy failed for %s: %s", src, exc)
        return

    today = datetime.now().strftime("%Y-%m-%d")
    if first_run_date() != today:
        try:
            src.unlink()
            log.info("Deleted original: %s", src.name)
        except OSError as exc:
            log.error("Delete failed for %s: %s", src, exc)


def process_file(path: Path) -> None:
    if not wait_until_stable(path):
        return
    copy_file(path)


def already_organized() -> set[str]:
    organized = set()
    for folder in DEST_ROOT.glob("Music downloaded *"):
        if folder.is_dir():
            for f in folder.iterdir():
                if f.is_file():
                    organized.add(f.name)
    return organized


def scan_existing() -> None:
    dest_dir = dest_folder()
    known = already_organized()
    found = skipped = 0
    for path in WATCH_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in MUSIC_EXTENSIONS and not path.name.startswith("."):
            if path.name in known:
                skipped += 1
                continue
            copy_file(path, dest_dir)
            found += 1
    if found:
        log.info("Startup scan: copied %d new file(s) to %s (skipped %d already organized)", found, dest_dir, skipped)
    else:
        log.info("Startup scan: no new music files found (skipped %d already organized)", skipped)
    if not FIRST_RUN_FLAG.exists():
        FIRST_RUN_FLAG.write_text(datetime.now().strftime("%Y-%m-%d"))


class MusicHandler(FileSystemEventHandler):
    def _schedule(self, path_str: str) -> None:
        path = Path(path_str)
        if path.suffix.lower() not in MUSIC_EXTENSIONS:
            return
        if path.name.startswith("."):
            return
        threading.Thread(target=process_file, args=(path,), daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(str(event.src_path))

    def on_moved(self, event):
        # Soulseek renames foo.mp3.tmp → foo.mp3 when download completes
        if not event.is_directory:
            self._schedule(str(event.dest_path))


def main() -> None:
    if not WATCH_DIR.exists():
        log.error("Watch directory does not exist: %s", WATCH_DIR)
        raise SystemExit(1)

    log.info("Scanning existing files on startup")
    scan_existing()

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
