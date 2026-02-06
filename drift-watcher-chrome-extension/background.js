let activeTabId = null;
let sessionStart = null;
let interactionBuffer = {};
let contentBuffer = {};

function sendEvent(event) {
  fetch("http://localhost:3333/event", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event)
  }).catch(() => {});
}

function endCurrentSession() {
  if (!activeTabId || !sessionStart) return;
  
  chrome.tabs.get(activeTabId, tab => {
    if (chrome.runtime.lastError) return;
    
    sendEvent({
      type: "PAGE_SESSION",
      title: tab.title,
      url: tab.url,
      content: contentBuffer[activeTabId] || "",
      durationMs: Date.now() - sessionStart,
      scrollCount: interactionBuffer[activeTabId]?.scroll || 0,
      keyCount: interactionBuffer[activeTabId]?.key || 0,
      timestamp: Date.now()
    });
  });
}

// Track tab activation
chrome.tabs.onActivated.addListener(({ tabId }) => {
  endCurrentSession();
  
  activeTabId = tabId;
  sessionStart = Date.now();
});

// Handle messages from content script
chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "INTERACTION_UPDATE") {
    interactionBuffer[activeTabId] = {
      scroll: msg.scrollCount,
      key: msg.keyCount
    };
    
    // Store content if provided
    if (msg.content) {
      contentBuffer[activeTabId] = msg.content;
    }
  } else if (msg.type === "URL_CHANGED") {
    // End current session and start new one for SPA navigation
    endCurrentSession();
    sessionStart = Date.now();
    
    // Reset interaction counts for new page
    interactionBuffer[activeTabId] = {
      scroll: 0,
      key: 0
    };
    
    // Store new content
    if (msg.content) {
      contentBuffer[activeTabId] = msg.content;
    }
  }
});

// Track tab close
chrome.tabs.onRemoved.addListener(tabId => {
  if (tabId === activeTabId && sessionStart) {
    sendEvent({
      type: "PAGE_SESSION",
      content: contentBuffer[tabId] || "",
      durationMs: Date.now() - sessionStart,
      timestamp: Date.now()
    });
    
    delete interactionBuffer[tabId];
    delete contentBuffer[tabId];
    activeTabId = null;
    sessionStart = null;
  }
});
