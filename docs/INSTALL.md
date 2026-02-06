# Installation Guide

## System-Wide Installation

Install Drift Watcher globally on your system:

```bash
# Clone the repository
git clone https://github.com/yourusername/drift-watcher.git
cd drift-watcher

# Install dependencies first
pip install -r requirements.txt

# Install the package (fast method)
pip install --no-build-isolation --no-deps .

# Or install in editable mode for development
pip install --no-build-isolation --no-deps -e .
```

### Verify Installation

```bash
# Check if commands are available
drift-watcher --help
drift-watcher-server --help
drift-watcher-goal
drift-watcher-switch --help
```

## Usage After Installation

### Run Drift Watcher (Server Auto-Starts!)

```bash
# Start with a goal (server starts automatically)
drift-watcher --goal "Learn Python programming"

# Press Ctrl+C to stop
# You'll be asked if you want to stop the server too
```

The agent will:
- Auto-start the event server if not running
- Store data in `~/.drift-watcher/`
- Monitor browser activity and notify on drift

### Manual Server Control (Optional)

If you prefer to manage the server separately:

```bash
# Start server manually
drift-watcher-server

# In another terminal, run agent without auto-start
drift-watcher --no-server --goal "Your goal"
```

### 3. Manage Your Goal

```bash
# View current goal
drift-watcher-goal

# Set new goal
drift-watcher-goal --set "Build a web application"
```

### 4. Switch LLM Provider

```bash
# Switch to Ollama (local)
drift-watcher-switch ollama

# Switch to OpenAI
drift-watcher-switch openai

# Switch to Anthropic
drift-watcher-switch anthropic

# Switch back to Bedrock
drift-watcher-switch bedrock
```

## Data Directory

All data is stored in `~/.drift-watcher/`:

```
~/.drift-watcher/
├── config.json          # Configuration
├── agent_state.json     # Current state
├── events.log           # Browser events
└── activity_cache.json  # Activity cache
```

## Configuration

Edit `~/.drift-watcher/config.json`:

```json
{
  "llm": {
    "provider": "bedrock",
    "config": {
      "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "region_name": "us-east-1"
    }
  },
  "agent": {
    "window_seconds": 30,
    "drift_confidence_threshold": 0.7
  },
  "server": {
    "host": "127.0.0.1",
    "port": 3333
  }
}
```

## Uninstallation

```bash
pip uninstall drift-watcher
```

To remove all data:

```bash
rm -rf ~/.drift-watcher
```

## Development Mode

For development, install in editable mode:

```bash
pip install -e .
```

Changes to the code will be reflected immediately without reinstalling.

## Troubleshooting

### Command not found

If commands aren't found after installation:

```bash
# Check if pip bin directory is in PATH
python -m site --user-base

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### Permission errors

Use `--user` flag:

```bash
pip install --user .
```

### Import errors

Ensure you're using the correct Python version:

```bash
python3 --version  # Should be 3.8+
pip3 install .
```
