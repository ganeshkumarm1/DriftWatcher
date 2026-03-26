import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for Drift Watcher."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        try:
            return json.loads(self.config_file.read_text())
        except Exception as e:
            raise ValueError(f"Error loading config: {e}")

    def save(self):
        self.config_file.write_text(json.dumps(self._config, indent=2))

    @property
    def llm_config(self) -> Dict[str, Any]:
        return self._config["llm"]

    @property
    def window_seconds(self) -> int:
        return self._config["agent"]["window_seconds"]

    @property
    def drift_threshold(self) -> float:
        return self._config["agent"]["drift_confidence_threshold"]

    @property
    def log_retention_days(self) -> int:
        return self._config["agent"].get("log_retention_days", 7)

    @property
    def server_host(self) -> str:
        return self._config["server"]["host"]

    @property
    def server_port(self) -> int:
        return self._config["server"]["port"]
