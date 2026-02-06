import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for Drift Watcher."""
    
    DEFAULT_CONFIG = {
        "llm": {
            "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "region_name": "us-east-1"
        },
        "agent": {
            "window_seconds": 30,
            "drift_confidence_threshold": 0.7,
            "log_retention_days": 7
        },
        "server": {
            "host": "127.0.0.1",
            "port": 3333
        }
    }
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._config = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_file.exists():
            try:
                loaded = json.loads(self.config_file.read_text())
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                self._deep_merge(config, loaded)
                return config
            except Exception as e:
                print(f"⚠️ Error loading config: {e}. Using defaults.")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _deep_merge(self, base: dict, update: dict):
        """Deep merge update into base."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save(self):
        """Save current configuration to file."""
        self.config_file.write_text(json.dumps(self._config, indent=2))
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self._config["llm"]
    
    @property
    def window_seconds(self) -> int:
        """Get monitoring window in seconds."""
        return self._config["agent"]["window_seconds"]
    
    @property
    def drift_threshold(self) -> float:
        """Get drift confidence threshold."""
        return self._config["agent"]["drift_confidence_threshold"]
    
    @property
    def log_retention_days(self) -> int:
        """Get log retention period in days."""
        return self._config["agent"].get("log_retention_days", 7)
    
    @property
    def server_host(self) -> str:
        """Get server host."""
        return self._config["server"]["host"]
    
    @property
    def server_port(self) -> int:
        """Get server port."""
        return self._config["server"]["port"]
