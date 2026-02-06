import json
from pathlib import Path


class StateManager:
    """Manages Drift Watcher state persistence."""
    
    def __init__(self, state_file="agent_state.json"):
        self.state_file = state_file
    
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
        """Return default state."""
        return {
            "goal": "No goal set",
            "focus_state": "EXPLORING",
            "confidence": 0.5,
            "check_interval_min": 20,
            "recent_states": [],
            "last_check_ts": 0
        }
    
    def reset_logs_on_goal_change(self, new_goal, events_log="events.log", activity_cache="activity_cache.json"):
        """Reset logs when goal changes."""
        state = self.load()
        old_goal = state.get("goal", "")
        
        # If goal changed, reset logs
        if old_goal and old_goal != new_goal:
            # Clear events log
            events_path = Path(events_log)
            if events_path.exists():
                events_path.unlink()
                print(f"🗑️  Cleared old events log")
            
            # Clear activity cache
            cache_path = Path(activity_cache)
            if cache_path.exists():
                cache_path.unlink()
                print(f"🗑️  Cleared activity cache")
        
        # Update goal
        state["goal"] = new_goal
        self.save(state)
        return state
