# Extension Changelog

## Version 1.0.0 - Cleanup & Optimization

### Removed Unnecessary Logic

#### Background Script (`background.js`)
- ❌ Removed duplicate `chrome.runtime.onMessage.addListener`
- ❌ Removed unused `URL_CHANGED` event handling
- ❌ Removed unused `TAB_VISIBLE` event handling
- ❌ Removed redundant `reason` field from events
- ✅ Added error handling for `chrome.tabs.get`
- ✅ Added cleanup of interaction buffer on tab close
- ✅ Simplified to single message listener

**Before:** 68 lines | **After:** 58 lines | **Reduction:** 15%

#### Content Script (`content.js`)
- ❌ Removed `urlLoop()` - URL changes not used by agent
- ❌ Removed `visibilityLoop()` - visibility events not used
- ❌ Removed `lastUrl` tracking - unnecessary
- ✅ Added passive event listeners for better performance
- ✅ Simplified to single interaction loop
- ✅ Clearer function naming

**Before:** 82 lines | **After:** 47 lines | **Reduction:** 43%

#### Manifest (`manifest.json`)
- ❌ Removed unused `activeTab` permission
- ❌ Removed unused `scripting` permission
- ✅ Added proper description
- ✅ Added emoji icons (🎯)
- ✅ Added `run_at: document_idle` for better performance
- ✅ Updated name to "Drift Watcher" (with space)

### Performance Improvements

1. **Passive Event Listeners**: Scroll and keyboard events use `{ passive: true }` for better performance
2. **Single Loop**: Reduced from 3 loops to 1 loop in content script
3. **Minimal Permissions**: Only requests necessary `tabs` permission
4. **Deferred Loading**: Content script runs at `document_idle`

### Code Quality

1. **Better Comments**: Clear, concise comments
2. **Consistent Naming**: `sendInteractionUpdate` instead of `interactionLoop`
3. **Error Handling**: Added `chrome.runtime.lastError` check
4. **Memory Management**: Clean up interaction buffer on tab close

### What Still Works

✅ Tab switching detection
✅ Page session tracking
✅ Scroll count tracking
✅ Keyboard activity tracking
✅ Duration measurement
✅ Extension context validation
✅ Graceful error handling

### Breaking Changes

None - All essential functionality preserved.

### Migration

No migration needed. Simply reload the extension in Chrome.
