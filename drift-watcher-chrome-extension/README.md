# Drift Watcher Chrome Extension

Browser extension that tracks your activity and sends events to the Drift Watcher server.

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select the `drift-watcher-extension` folder
5. Extension is now installed and tracking

## What It Tracks

- **Tab Switches**: When you switch between tabs
- **Page Sessions**: Time spent on each page
- **SPA Navigation**: URL changes within single-page apps (YouTube Shorts, etc.)
- **Scroll Activity**: Number of scroll events
- **Keyboard Activity**: Number of key presses

## How It Works

### Background Script (`background.js`)
- Monitors tab activation and closure
- Tracks session duration for each tab
- Buffers interaction data (scroll/key counts)
- Sends `PAGE_SESSION` events to local server

### Content Script (`content.js`)
- Runs on every webpage
- Counts scroll and keyboard events
- Detects URL changes for SPA navigation (YouTube Shorts, etc.)
- Sends interaction updates every 5 seconds
- Handles extension context invalidation gracefully

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select this directory (`drift-watcher-extension/`)

## Events Sent

### PAGE_SESSION
Sent when switching tabs or closing a tab:
```json
{
  "type": "PAGE_SESSION",
  "title": "Page Title",
  "url": "https://example.com",
  "durationMs": 45000,
  "scrollCount": 12,
  "keyCount": 150,
  "timestamp": 1234567890
}
```

### URL_CHANGED
Sent when URL changes within a page (SPA navigation):
```json
{
  "type": "URL_CHANGED",
  "title": "New Page Title",
  "url": "https://youtube.com/shorts/xyz",
  "timestamp": 1234567890
}
```

### INTERACTION_UPDATE
Sent every 5 seconds from active page:
```json
{
  "type": "INTERACTION_UPDATE",
  "scrollCount": 3,
  "keyCount": 25,
  "title": "Page Title",
  "url": "https://example.com",
  "timestamp": 1234567890
}
```

## Server Endpoint

Events are sent to: `http://localhost:3333/event`

Make sure the Drift Watcher server is running:
```bash
python run_server.py
```

## Privacy

- All data stays local (sent to localhost only)
- No external servers or analytics
- No data collection or storage by the extension
- You control all data through the Drift Watcher server

## Troubleshooting

**Extension not tracking:**
- Check that Developer mode is enabled
- Verify the extension is enabled in `chrome://extensions/`
- Reload the extension after code changes

**Events not reaching server:**
- Ensure server is running: `python run_server.py`
- Check server is on port 3333
- Look for CORS or network errors in browser console (F12)

**High CPU usage:**
- Extension uses passive event listeners
- Minimal performance impact
- Events are batched and sent every 5 seconds
