# @steered SNARE-1 2026-09-18
import json
import subprocess
import time
from pathlib import Path

NOTIFIER_STATE_FILE = "notifier_state.json"


class Notifier:
    """Handles system notifications with cooldown, persisted across restarts."""

    def __init__(self, cooldown_seconds=120):
        self.cooldown_seconds = cooldown_seconds
        self._focused_cooldown_seconds = 300  # longer cooldown for positive alerts
        self._last_notify_ts = 0
        self._last_focused_ts = 0
        self._load_state()

    def _load_state(self):
        try:
            data = json.loads(Path(NOTIFIER_STATE_FILE).read_text())
            self._last_notify_ts = data.get("last_notify_ts", 0)
            self._last_focused_ts = data.get("last_focused_ts", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_state(self):
        try:
            Path(NOTIFIER_STATE_FILE).write_text(json.dumps({
                "last_notify_ts": self._last_notify_ts,
                "last_focused_ts": self._last_focused_ts,
            }))
        except Exception:
            pass

    def _send(self, title: str, message: str):
        message = message.replace('\\', '\\\\').replace('"', '\\"')
        script = f'display notification "{message}" with title "{title}" sound name "default"'
        try:
            subprocess.run(["osascript", "-e", script], timeout=5)
        except Exception as e:
            print(f"⚠️ Notification error: {e}")

    def notify_drift(self, goal: str, confidence: float, reason: str = ""):
        """Send drift notification if cooldown has passed."""
        now = time.time()
        time_since_last = now - self._last_notify_ts

        if time_since_last < self.cooldown_seconds:
            remaining = int(self.cooldown_seconds - time_since_last)
            print(f"🔕 Notification cooldown: {remaining}s remaining")
            return

        message = f"You may be drifting from: {goal}"
        if reason:
            message += f"\n{reason}"

        self._send("⚠️ Drift Alert", message)
        print(f"🔔 Drift notification sent! (Confidence: {confidence:.2f})")
        self._last_notify_ts = now
        self._save_state()

    def notify_focused(self, goal: str):
        """Send back-on-track notification if cooldown has passed."""
        now = time.time()
        if now - self._last_focused_ts < self._focused_cooldown_seconds:
            return

        self._send("✅ Back on Track", f"You're focused on: {goal}")
        print("🎯 Back-on-track notification sent!")
        self._last_focused_ts = now
        self._save_state()
