# Installation Guide

## Prerequisites

- **Python 3.8+**
- **Google Chrome**
- **Claude Code CLI** — `claude` must be on your PATH. Install from https://claude.ai/code

Verify Claude Code is available:
```bash
claude --version
```

---

## Install the Package

From the repo root:

```bash
pip3 install .
```

On Homebrew Python (macOS), you may need:

```bash
pip3 install . --break-system-packages
```

If pip itself errors with a `PermissionError` on `os.getcwd()`, run from your home directory:

```bash
cd ~ && pip3 install /path/to/drift-watcher --break-system-packages
```

Verify the install:

```bash
drift-watcher --help
```

---

## Load the Chrome Extension

1. Open `chrome://extensions/` in Chrome
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked**
4. Select the `drift-watcher-chrome-extension/` directory from this repo

The extension will appear as "Drift Watcher" in your extensions list and start capturing browser activity automatically.

---

## First Run

```bash
drift-watcher
```

This starts both the event server and the agent loop. Then:

1. Open **http://127.0.0.1:3333/dashboard**
2. Click **🎯 Start a New Goal**
3. Describe what you're working on — be specific
4. DriftWatcher begins monitoring on the next loop tick (within 60 seconds)

Press `Ctrl+C` to stop.

---

## Configuration

Config is created automatically at `~/.drift-watcher/config.json` on first run. Default:

```json
{
  "llm": {
    "provider": "claude-cli",
    "model": "claude-haiku-4-5-20251001"
  },
  "agent": {
    "window_seconds": 60,
    "drift_confidence_threshold": 0.7,
    "log_retention_days": 7
  },
  "server": {
    "host": "127.0.0.1",
    "port": 3333
  }
}
```

> **For demos:** Set `window_seconds: 15` to trigger drift detection in ~30 seconds instead of ~2 minutes.

---

## Switching LLM Providers

Edit `~/.drift-watcher/config.json` and restart `drift-watcher`.

### Claude CLI (default)
Uses your existing Claude Code login. Supports internal MCP tools (Taskei, wiki, etc.) configured in your Claude Code settings.

```json
{
  "llm": {
    "provider": "claude-cli",
    "model": "claude-haiku-4-5-20251001"
  }
}
```

### Ollama (local)
Requires [Ollama](https://ollama.ai) running locally.

```json
{
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5:latest",
    "base_url": "http://localhost:11434"
  }
}
```

### AWS Bedrock
Requires AWS credentials configured (`aws configure`).

```json
{
  "llm": {
    "provider": "bedrock",
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "region_name": "us-east-1"
  }
}
```

---

## Data Directory

All runtime data is stored in `~/.drift-watcher/`:

```
~/.drift-watcher/
├── config.json           # Configuration
├── agent_state.json      # Current session state
├── session_history.json  # Past sessions
├── events.log            # Browser events
└── notifier_state.json   # Notification cooldown state
```

---

## Uninstall

```bash
pip3 uninstall drift-watcher
```

To remove all data:

```bash
rm -rf ~/.drift-watcher
```
