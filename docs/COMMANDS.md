# Command Reference

## Main Agent

```bash
# Run with goal (auto-starts server)
drift-watcher --goal "Learn Python programming"

# Run with existing goal
drift-watcher

# Custom config file
drift-watcher --config /path/to/config.json

# Don't auto-start server
drift-watcher --no-server

# Keep server running after agent stops
drift-watcher --keep-server

# Test notifications
drift-watcher --test-notification
```

## Goal Management

```bash
# View current goal
drift-watcher-goal

# Set new goal
drift-watcher-goal --set "Learn machine learning"
```

Output:
```
============================================================
Current Focus Goal
============================================================

🎯 Learn Python programming

State: FOCUSED
Confidence: 0.7
============================================================
```

## Server

```bash
# Start server manually
drift-watcher-server

# Custom host/port
drift-watcher-server --host 127.0.0.1 --port 3333
```

## Switching LLM Provider

Edit `~/.drift-watcher/config.json`:

**Ollama (local):**
```json
{
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5:latest",
    "base_url": "http://localhost:11434"
  }
}
```

**AWS Bedrock:**
```json
{
  "llm": {
    "provider": "bedrock",
    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "region_name": "us-east-1"
  }
}
```

## Typical Workflow

1. Set your goal and start:
   ```bash
   drift-watcher --goal "Learn Python programming"
   ```

2. Change goal:
   ```bash
   drift-watcher-goal --set "Build a web application"
   drift-watcher
   ```

3. Switch provider: edit `~/.drift-watcher/config.json` and restart.
