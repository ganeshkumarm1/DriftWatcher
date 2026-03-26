# Troubleshooting Guide

## Notifications Not Working

### Quick Test

```bash
drift-watcher --test-notification
```

### Common Issues

#### 1. Notifications Disabled for Terminal

1. Open **System Settings** → **Notifications**
2. Find **Terminal** (or iTerm)
3. Enable **Allow Notifications**, set style to **Banners** or **Alerts**

#### 2. Do Not Disturb Mode

System Settings → Focus → Do Not Disturb → turn off

#### 3. Notification Cooldown

Default cooldown is 2 minutes. Check agent output:
```
🔕 Notification cooldown: 60s remaining
```

#### 4. Confidence Threshold Too High

Default threshold is 0.7. Check agent output:
```
⚠️ Drifting but confidence too low: 0.65 < 0.7
```

Lower it in `~/.drift-watcher/config.json`:
```json
{ "agent": { "drift_confidence_threshold": 0.6 } }
```

#### 5. No Drift Detected

Check agent output:
```
🧭 State: FOCUSED | Confidence: 0.8 | Reason: ...
```

If state is FOCUSED, no notification is sent.

---

## Extension Not Tracking

1. Go to `chrome://extensions/` → verify **Drift Watcher** is enabled
2. Check server is running:
   ```bash
   curl http://localhost:3333/health
   ```
   Should return: `{"status":"running"}`
3. Open browser DevTools (F12) → Console → look for errors
4. Reload extension and refresh tabs

---

## Agent Not Detecting Activity

Check events are being logged:
```bash
tail -f ~/.drift-watcher/events.log
```

If empty: extension not installed, server not running, or extension can't reach server.

When running correctly you should see:
```
🔍 Events in window: 5
🧭 State: FOCUSED | Confidence: 0.85 | Relevant: 80.0% | Reason: ...
```

---

## LLM Errors

### Ollama

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start if needed
ollama serve

# Pull model if missing
ollama pull qwen2.5:latest
```

### AWS Bedrock

```bash
# Test credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

---

## Getting Help

Include this when reporting issues:
- macOS version, Python version (`python --version`)
- Agent output (last 20 lines)
- Extension console errors
- `~/.drift-watcher/config.json` (remove API keys)
