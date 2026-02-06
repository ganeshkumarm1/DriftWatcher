import json
import time
from pathlib import Path


class EventReader:
    """Reads and filters events from log file."""
    
    def __init__(self, file_path, max_age_days=7):
        self.file_path = file_path
        self.max_age_days = max_age_days
    
    def read_recent(self, window_seconds=30):
        """Read events from the last N seconds."""
        cutoff_ts = int(time.time() * 1000) - (window_seconds * 1000)
        events = []
        
        try:
            with open(self.file_path, "r") as f:
                for line in f:
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
        
        # Rewrite file with only recent events
        if removed_count > 0:
            with open(self.file_path, "w") as f:
                f.writelines(kept_events)
        
        return removed_count
