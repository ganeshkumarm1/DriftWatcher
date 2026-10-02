# @steered SNARE-1 2026-09-18
import json
import time
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse
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
                
                state_manager = StateManager()
                state = state_manager.load()
                
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
                
                heartbeat_ts = state.get("agent_heartbeat_ts", 0)
                agent_stale = (heartbeat_ts == 0) or ((time.time() - heartbeat_ts) > 180)

                return jsonify({
                    "goal": state.get("goal", "No goal set"),
                    "focus_state": state.get("focus_state", "UNKNOWN"),
                    "confidence": state.get("confidence", 0.0),
                    "drift_count": state.get("drift_count", 0),
                    "session_minutes": session_minutes,
                    "last_check": last_check,
                    "last_check_ts": state.get("last_check_ts", 0),
                    "relevant_percent": state.get("relevant_percent", 0.0),
                    "irrelevant_percent": state.get("irrelevant_percent", 0.0),
                    "reason": state.get("reason", ""),
                    "agent_running": not agent_stale,
                    "paused_until": state.get("paused_until", 0),
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

        @self.app.route("/api/goal", methods=["POST"])
        def set_goal():
            try:
                data = request.get_json(force=True)
                goal = data.get("goal", "").strip()
                if not goal:
                    return jsonify({"error": "goal is required"}), 400
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                state_manager.reset_logs_on_goal_change(goal)
                return jsonify({"status": "ok", "goal": goal}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/session/end", methods=["POST"])
        def end_session():
            try:
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                state = state_manager.load()
                state_manager.archive_session(state)
                state["goal"] = "No goal set"
                state["focus_state"] = "FOCUSED"
                state["drift_count"] = 0
                state["recent_states"] = []
                state["session_start_ts"] = 0
                state_manager.save(state)
                return jsonify({"status": "ok"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/recent-activity", methods=["GET"])
        def get_recent_activity():
            try:
                events = []
                try:
                    file_size = self.events_file.stat().st_size
                    chunk = min(51200, file_size)
                    with self.events_file.open("r") as f:
                        if chunk < file_size:
                            f.seek(file_size - chunk)
                            f.readline()
                        for line in f:
                            try:
                                events.append(json.loads(line))
                            except Exception:
                                continue
                except FileNotFoundError:
                    pass

                pages = {}
                for e in events:
                    raw_url = e.get("url", "")
                    if not raw_url:
                        continue
                    p = urlparse(raw_url)
                    norm_url = urlunparse((p.scheme, p.netloc, p.path, '', '', ''))
                    if norm_url not in pages:
                        pages[norm_url] = {
                            "title": e.get("title", norm_url),
                            "url": norm_url,
                            "duration_min": 0.0,
                            "scroll_count": 0,
                            "key_count": 0,
                            "last_seen_ts": 0,
                        }
                    pages[norm_url]["duration_min"] += e.get("durationMs", 5000) / 60000
                    pages[norm_url]["scroll_count"] += e.get("scrollCount", 0)
                    pages[norm_url]["key_count"] += e.get("keyCount", 0)
                    pages[norm_url]["last_seen_ts"] = max(
                        pages[norm_url]["last_seen_ts"], e.get("server_ts", 0)
                    )

                def infer_type(url):
                    if "youtube.com/watch" in url or "youtu.be" in url:
                        return "video"
                    if "youtube.com" in url:
                        return "video_browse"
                    if "twitter.com" in url or "x.com" in url:
                        return "social"
                    if any(d in url for d in ["linkedin.com", "facebook.com", "instagram.com", "reddit.com"]):
                        return "social"
                    if "taskei.amazon.com" in url or "sim.amazon.com" in url:
                        return "ticket"
                    if "w.amazon.com" in url or "wiki.amazon" in url:
                        return "wiki_internal"
                    if "code.amazon.com" in url:
                        return "code_internal"
                    if "amazon.com" in url:
                        return "work_internal"
                    if "github.com" in url or "gitlab.com" in url:
                        return "code"
                    if "stackoverflow.com" in url or "docs." in url or "developer." in url:
                        return "docs"
                    return "webpage"

                result = sorted(pages.values(), key=lambda x: x["last_seen_ts"], reverse=True)[:10]
                for item in result:
                    item["page_type"] = infer_type(item["url"])
                    item["duration_min"] = round(item["duration_min"], 2)

                return jsonify({"pages": result}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/pause", methods=["POST"])
        def pause_agent():
            try:
                data = request.get_json(force=True) or {}
                minutes = int(data.get("minutes", 15))
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                state = state_manager.load()
                state["paused_until"] = time.time() + (minutes * 60)
                state_manager.save(state)
                return jsonify({"status": "paused", "minutes": minutes, "until": state["paused_until"]}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/resume", methods=["POST"])
        def resume_agent():
            try:
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                state = state_manager.load()
                state["paused_until"] = 0
                state_manager.save(state)
                return jsonify({"status": "resumed"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/drift-log", methods=["GET"])
        def get_drift_log():
            try:
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                state = state_manager.load()
                drift_log = state.get("drift_log", [])
                drift_log_sorted = sorted(drift_log, key=lambda x: x.get("ts", 0), reverse=True)
                return jsonify({"drifts": drift_log_sorted}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/weekly", methods=["GET"])
        def get_weekly():
            try:
                from ..core.state_manager import StateManager
                state_manager = StateManager()
                history = state_manager.load_history()
                now = time.time()
                week_ago = now - 7 * 86400
                recent = [s for s in history if s.get("end_ts", 0) >= week_ago]
                # Group by day
                days = {}
                for s in recent:
                    day = time.strftime("%a", time.localtime(s["end_ts"]))
                    if day not in days:
                        days[day] = {"sessions": 0, "drifts": 0, "focused_min": 0}
                    dur = (s.get("end_ts", 0) - s.get("start_ts", 0)) / 60
                    days[day]["sessions"] += 1
                    days[day]["drifts"] += s.get("drift_count", 0)
                    days[day]["focused_min"] += round(dur * s.get("final_confidence", 0.5))
                return jsonify({"days": days, "total_sessions": len(recent),
                                "total_drifts": sum(s.get("drift_count",0) for s in recent)}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self, debug=False):
        """Start the server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=debug,
            threaded=True
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
