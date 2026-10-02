# @steered SNARE-1 2026-09-18
import json
import time
from pathlib import Path

TAIL_CHUNK_BYTES = 50 * 1024  # 50 KB — enough for hundreds of recent events


class EventReader:
    """Reads and filters events from log file."""

    def __init__(self, file_path, max_age_days=7):
        self.file_path = file_path
        self.max_age_days = max_age_days

    def read_recent(self, window_seconds=30):
        """Read events from the last N seconds using a tail-read to avoid O(n) full scans."""
        cutoff_ts = int(time.time() * 1000) - (window_seconds * 1000)
        events = []

        try:
            path = Path(self.file_path)
            file_size = path.stat().st_size

            with open(self.file_path, "rb") as f:
                if file_size <= TAIL_CHUNK_BYTES:
                    # File small enough to read fully
                    raw = f.read().decode("utf-8", errors="replace")
                else:
                    # Seek to tail chunk; skip first (possibly partial) line
                    f.seek(-TAIL_CHUNK_BYTES, 2)
                    raw = f.read().decode("utf-8", errors="replace")
                    # Drop the first line which may be cut mid-record
                    newline_pos = raw.find("\n")
                    if newline_pos != -1:
                        raw = raw[newline_pos + 1:]

            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if event.get("server_ts", 0) >= cutoff_ts:
                        events.append(event)
                except json.JSONDecodeError:
                    continue

        except FileNotFoundError:
            pass

        return events

    def cleanup_old_logs(self):
        """Remove log entries older than max_age_days."""
        path = Path(self.file_path)
        if not path.exists():
            return 0

        cutoff_ts = int(time.time() * 1000) - (self.max_age_days * 24 * 60 * 60 * 1000)
        kept_events = []
        removed_count = 0

        with open(self.file_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get("server_ts", 0) >= cutoff_ts:
                        kept_events.append(line)
                    else:
                        removed_count += 1
                except json.JSONDecodeError:
                    continue

        if removed_count > 0:
            with open(self.file_path, "w") as f:
                f.writelines(kept_events)

        return removed_count
