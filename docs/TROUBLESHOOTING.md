# Troubleshooting Guide

## Notifications Not Working

### Quick Test

Run the notification test:
```bash
python main.py --test-notification
```

Or use the dedicated test script:
```bash
python test_notification.py
```

### Common Issues

#### 1. Notifications Disabled for Terminal

**macOS Ventura/Sonoma:**
1. Open **System Settings**
2. Go to **Notifications**
3. Find **Terminal** (or **iTerm** if you use that)
4. Enable **Allow Notifications**
5. Set alert style to **Banners** or **Alerts**

**macOS Monterey and earlier:**
1. Open **System Preferences**
2. Go to **Notifications & Focus**
3. Find **Terminal** in the list
4. Enable notifications

#### 2. Do Not Disturb Mode

Check if Do Not Disturb is enabled:
- Click the Control Center icon in menu bar
- Make sure **Focus** is off
- Or go to System Settings → Focus → Do Not Disturb

#### 3. Notification Cooldown

Notifications have a 5-minute cooldown by default to avoid spam.

Check the agent output:
```
🔕 Notification cooldown: 120s remaining
```

To change cooldown, edit `config.json`:
```json
{
  "agent": {
    "notification_cooldown_seconds": 60
  }
}
```

#### 4. Confidence Threshold Too High

Default threshold is 0.7. If drift confidence is lower, no notification is sent.

Check agent output:
```
⚠️ Drifting but confidence too low: 0.65 < 0.7
```

To lower threshold, edit `config.json`:
```json
{
  "agent": {
    "drift_confidence_threshold": 0.6
  }
}
```

#### 5. No Drift Detected

The agent might not be detecting drift. Check the output:
```
🧭 State: ALIGNED | Confidence: 0.8 | Reason: ...
```

If state is ALIGNED or EXPLORING, no notification is sent.

### Debug Output

When drift is detected, you should see:
```
⚠️ DRIFT DETECTED! Confidence: 0.85 >= 0.7
🔔 Notification sent! (Confidence: 0.85)
```

If you see:
```
⚠️ Notification failed: ...
```

Check the error message for details.

## Extension Not Tracking

### Check Extension Status

1. Go to `chrome://extensions/`
2. Find **Drift Watcher**
3. Make sure it's **enabled**
4. Check for any errors

### Check Server Connection

1. Make sure server is running:
   ```bash
   python run_server.py
   ```

2. You should see:
   ```
   🌐 Event server starting on 127.0.0.1:3333
   ```

3. Test server health:
   ```bash
   curl http://localhost:3333/health
   ```

   Should return: `{"status":"running"}`

### Check Browser Console

1. Open any webpage
2. Press F12 to open DevTools
3. Go to **Console** tab
4. Look for errors related to Drift Watcher

### Reload Extension

After making changes:
1. Go to `chrome://extensions/`
2. Click the **reload** icon on Drift Watcher
3. Refresh your browser tabs

## Agent Not Detecting Activity

### Check Events File

```bash
tail -f events.log
```

You should see events being logged when browsing.

If empty:
- Extension not installed or disabled
- Server not running
- Extension can't reach server

### Check Agent Output

When running, you should see:
```
🔍 Events in window: 5
📊 Activity summary: {...}
🎯 Relevance: RELATED | ...
🧭 State: ALIGNED | ...
```

If you see:
```
… no events in last window
```

The extension isn't sending events.

## LLM Errors

### AWS Bedrock

```bash
# Test credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### OpenAI

Check API key in `config.json`:
```json
{
  "llm": {
    "provider": "openai",
    "config": {
      "api_key": "sk-..."
    }
  }
}
```

### Ollama

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

## Getting Help

If issues persist:

1. Check agent output for error messages
2. Run notification test: `python test_notification.py`
3. Check events are being logged: `tail -f events.log`
4. Verify extension is loaded and enabled
5. Check server is running and accessible

Include this information when reporting issues:
- Operating system and version
- Python version: `python --version`
- Agent output (last 20 lines)
- Extension console errors (if any)
- Config file (remove API keys)
