# 🎯 Drift Watcher

**A personal focus monitoring system that tracks browser activity and detects when you drift from your goals**

## Features

- 🔄 **Federated LLM Support** - Plug-and-play model switching between providers
- 🤖 **Multiple Providers** - AWS Bedrock, OpenAI, Anthropic, Ollama (local)
- 📊 **Activity Classification** - Automatic categorization of browser activity
- 🎯 **Focus State Detection** - ALIGNED, EXPLORING, or DRIFTING states
- 🔔 **Smart Notifications** - macOS notifications when you drift from goals
- 🔌 **Chrome Extension** - Seamless browser activity tracking

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the event server
python run_server.py

# 3. In another terminal, run Drift Watcher with your goal
python main.py --goal "Learn Python programming"
```

That's it! Drift Watcher will monitor your browser activity and notify you if you drift.

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- AWS account (for Bedrock) OR OpenAI/Anthropic API key OR Ollama (local)

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/drift-watcher.git
cd drift-watcher

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **"Load unpacked"**
4. Select the `drift-watcher-extension/` folder
5. Extension is now installed

### Step 3: Configure AWS Credentials (for Bedrock)

If you're using AWS Bedrock (default provider), configure your AWS credentials:

```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure credentials
aws configure
```

### Step 4: Run Drift Watcher

```bash
# Start the event server
python run_server.py

# In another terminal, run Drift Watcher
python main.py --goal "Learn Python programming"
```

## Switching LLM Providers
### Use Ollama (Local, Free)
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2

# Switch to Ollama
python switch_provider.py ollama

# Run Drift Watcher
python main.py --goal "Your goal"
```

### Use OpenAI
```bash
# Switch to OpenAI
python switch_provider.py openai

# Edit config.json and add your API key
# Then run Drift Watcher
python main.py --goal "Your goal"
```

### Use Anthropic
```bash
# Switch to Anthropic
python switch_provider.py anthropic

# Edit config.json and add your API key
# Then run Drift Watcher
python main.py --goal "Your goal"
```

## Managing Your Goal

**View current goal:**
```bash
python manage_goal.py
```

**Change goal:**
```bash
python manage_goal.py --set "Build a web application"
```

## Configuration

Edit `config.json` to customize:
- LLM provider and model
- Monitoring window (default: 30 seconds)
- Drift confidence threshold (default: 0.7)
- Server host and port

## Troubleshooting

**Drift Watcher not detecting activity:**
- Make sure the Chrome extension is installed and enabled
- Check that the event server is running
- Verify the extension can reach `http://localhost:3333`

**LLM errors:**
- Check your API keys in `config.json`
- Verify AWS credentials for Bedrock
- For Ollama, ensure the service is running: `ollama serve`

**No notifications:**
- macOS: Grant notification permissions to Terminal/iTerm
- Check that drift confidence threshold is met (default: 0.7)

## Next Steps

- Customize your configuration in `config.json`
- Try different LLM providers
- Adjust the monitoring window and thresholds
- Create custom LLM providers (see `examples/custom_provider.py`)
