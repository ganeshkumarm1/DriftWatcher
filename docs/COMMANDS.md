# Command Reference

## Main Commands

### Start with Goal
```bash
python main.py --goal "Learn Python programming"
```

### Start with Existing Goal
```bash
python main.py
```

### Custom Configuration
```bash
python main.py --config custom_config.json
```

### Combined Options
```bash
python main.py --goal "Build web app" --config custom.json
```

### Help
```bash
python main.py --help
```

## Goal Management

### View Current Goal
```bash
python manage_goal.py
```
Output:
```
============================================================
Current Focus Goal
============================================================

🎯 Learn Python programming

State: EXPLORING
Confidence: 0.7
============================================================
```

### Set New Goal
```bash
python manage_goal.py --set "Learn machine learning"
```

### Help
```bash
python manage_goal.py --help
```

## Provider Switching

### Switch to Ollama (Local)
```bash
python switch_provider.py ollama
```

### Switch to OpenAI
```bash
python switch_provider.py openai
# Don't forget to add API key in config.json
```

### Switch to Anthropic
```bash
python switch_provider.py anthropic
# Don't forget to add API key in config.json
```

### Switch to AWS Bedrock
```bash
python switch_provider.py bedrock
```

### List Available Providers
```bash
python switch_provider.py
```

## Event Server

### Start Server (Default: localhost:3333)
```bash
python run_server.py
```

## Examples

### Custom Provider Example
```bash
python examples/custom_provider.py
```

### Model Switching Example
```bash
python examples/switch_models.py
```

## Typical Workflow

1. **Start the server:**
   ```bash
   python run_server.py
   ```

2. **In another terminal, set your goal and start Drift Watcher:**
   ```bash
   python main.py --goal "Learn Python programming"
   ```

3. **Change goal later:**
   ```bash
   # Stop Drift Watcher (Ctrl+C)
   python manage_goal.py --set "Build a web application"
   python main.py
   ```

4. **Switch LLM provider:**
   ```bash
   # Stop Drift Watcher (Ctrl+C)
   python switch_provider.py ollama
   python main.py
   ```
