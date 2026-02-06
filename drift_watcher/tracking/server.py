import json
import time
import os
from pathlib import Path
from flask import Flask, request, jsonify


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
