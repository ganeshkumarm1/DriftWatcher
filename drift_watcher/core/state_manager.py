# @steered SNARE-1 2026-09-18
import json
import time
from pathlib import Path


class StateManager:
    """Manages Drift Watcher state persistence."""

    def __init__(self, state_file="agent_state.json", history_file="session_history.json"):
        self.state_file = state_file
        self.history_file = history_file

    def load(self):
        """Load state from file."""
        try:
            with open(self.state_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_state()

    def save(self, state):
        """Save state to file."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _default_state(self):
        return {
            "goal": "No goal set",
            "focus_state": "FOCUSED",
            "confidence": 0.5,
            "drift_count": 0,
            "check_interval_min": 20,
            "recent_states": [],
            "last_check_ts": 0,
            "session_start_ts": time.time()
        }

    def push_recent_state(self, state: dict, focus_state: str, confidence: float) -> dict:
        """Append the latest assessment to recent_states, keeping the last 5."""
        recent = state.get("recent_states", [])
        recent.append({"state": focus_state, "confidence": confidence, "ts": time.time()})
        state["recent_states"] = recent[-5:]
        return state

    def consecutive_drifts(self, state: dict, threshold: float, required: int = 2) -> bool:
        """Return True if the last `required` assessments are all DRIFTING above threshold."""
        recent = state.get("recent_states", [])
        if len(recent) < required:
            return False
        tail = recent[-required:]
        return all(
            r["state"] == "DRIFTING" and r["confidence"] >= threshold
            for r in tail
        )

    def load_history(self):
        """Load session history."""
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_history(self, history):
        """Save session history."""
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def archive_session(self, state):
        """Archive current session to history."""
        if not state.get("goal") or state["goal"] == "No goal set":
            return

        history = self.load_history()

        session = {
            "goal": state["goal"],
            "start_ts": state.get("session_start_ts", time.time()),
            "end_ts": time.time(),
            "drift_count": state.get("drift_count", 0),
            "final_state": state.get("focus_state", "UNKNOWN"),
            "final_confidence": state.get("confidence", 0.0)
        }

        history.append(session)
        if len(history) > 100:
            history = history[-100:]
        self.save_history(history)

    def reset_logs_on_goal_change(self, new_goal, events_log="events.log", activity_cache="activity_cache.json"):
        """Reset logs when goal changes."""
        state = self.load()
        old_goal = state.get("goal", "")

        if old_goal and old_goal != new_goal:
            self.archive_session(state)

            events_path = Path(events_log)
            if events_path.exists():
                events_path.unlink()
                print(f"🗑️  Cleared old events log")

            cache_path = Path(activity_cache)
            if cache_path.exists():
                cache_path.unlink()
                print(f"🗑️  Cleared activity cache")

        state["goal"] = new_goal
        state["drift_count"] = 0
        state["recent_states"] = []
        state["session_start_ts"] = time.time()
        state["focus_state"] = "UNKNOWN"
        state["confidence"] = 0.0
        state["reason"] = ""
        state["relevant_percent"] = 0.0
        state["irrelevant_percent"] = 0.0
        state["last_check_ts"] = 0
        state["drift_log"] = []
        self.save(state)
        return state
