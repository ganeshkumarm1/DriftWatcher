import json
import time
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory


class EventServer:
    """Flask server for receiving browser events."""
    
    def __init__(self, events_file="events.log", host="127.0.0.1", port=3333):
        self.events_file = Path(events_file)
        self.events_file.touch(exist_ok=True)
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route("/event", methods=["POST"])
        def receive_event():
            try:
                event = request.get_json(force=True)
                event["server_ts"] = int(time.time() * 1000)
                
                with self.events_file.open("a") as f:
                    f.write(json.dumps(event) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                
                return jsonify({"status": "ok"}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        
        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "running"}), 200
        
        @self.app.route("/dashboard", methods=["GET"])
        def dashboard():
            """Serve dashboard HTML."""
            dashboard_dir = Path(__file__).parent.parent / "dashboard"
            return send_from_directory(dashboard_dir, "index.html")
        
        @self.app.route("/dashboard.js", methods=["GET"])
        def dashboard_js():
            """Serve dashboard JavaScript."""
            dashboard_dir = Path(__file__).parent.parent / "dashboard"
            return send_from_directory(dashboard_dir, "dashboard.js")
        
        @self.app.route("/dashboard.css", methods=["GET"])
        def dashboard_css():
            """Serve dashboard CSS."""
            dashboard_dir = Path(__file__).parent.parent / "dashboard"
            return send_from_directory(dashboard_dir, "dashboard.css")
        
        @self.app.route("/api/stats", methods=["GET"])
        def get_stats():
            """Get current stats for dashboard."""
            try:
                from ..core.state_manager import StateManager
                from ..tracking.event_reader import EventReader
                from ..tracking.activity_processor import ActivityProcessor
                
                # Load current state
                state_manager = StateManager()
                state = state_manager.load()
                
                # Get recent activity
                event_reader = EventReader(str(self.events_file))
                recent_events = event_reader.read_recent(300)  # Last 5 minutes
                
                # Calculate activity breakdown
                activity_breakdown = {}
                if recent_events:
                    processor = ActivityProcessor()
                    summary = processor.aggregate(recent_events)
                    activity_breakdown = summary.get("breakdown", {})
                
                # Calculate session time
                session_minutes = 0
                if state.get("session_start_ts") and state.get("session_start_ts") > 0:
                    session_minutes = max(0, int((time.time() - state["session_start_ts"]) / 60))
                
                # Format last check time
                last_check = "Never"
                if state.get("last_check_ts") and state.get("last_check_ts") > 0:
                    seconds_ago = max(0, int(time.time() - state["last_check_ts"]))
                    if seconds_ago < 60:
                        last_check = f"{seconds_ago}s"
                    elif seconds_ago < 3600:
                        last_check = f"{seconds_ago // 60}m"
                    else:
                        last_check = f"{seconds_ago // 3600}h"
                
                return jsonify({
                    "goal": state.get("goal", "No goal set"),
                    "focus_state": state.get("focus_state", "UNKNOWN"),
                    "confidence": state.get("confidence", 0.0),
                    "drift_count": state.get("drift_count", 0),
                    "session_minutes": session_minutes,
                    "last_check": last_check,
                    "activity_breakdown": activity_breakdown
                }), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/api/history", methods=["GET"])
        def get_history():
            """Get session history."""
            try:
                from ..core.state_manager import StateManager
                
                state_manager = StateManager()
                history = state_manager.load_history()
                
                # Sort by end time descending
                history.sort(key=lambda x: x.get("end_ts", 0), reverse=True)
                
                return jsonify({"sessions": history}), 200
            
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def run(self, debug=False):
        """Start the server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=debug
        )


def main(config_file="config.json"):
    """Entry point for server."""
    from ..config import Config
    
    config = Config(config_file)
    server = EventServer(
        host=config.server_host,
        port=config.server_port
    )
    print(f"🌐 Event server starting on {config.server_host}:{config.server_port}")
    server.run()


if __name__ == "__main__":
    main()
