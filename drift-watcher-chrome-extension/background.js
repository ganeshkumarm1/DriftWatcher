// @steered SNARE-1 2026-09-18
let activeTabId = null;
let sessionStart = null;
let interactionBuffer = {};
let contentBuffer = {};
let tabInfoBuffer = {};  // stores { title, url } per tabId so onRemoved has it

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

    // Update tabInfoBuffer with latest known title/url
    tabInfoBuffer[activeTabId] = { title: tab.title, url: tab.url };

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

  // Snapshot tab info immediately so onRemoved has it even without a full session
  chrome.tabs.get(tabId, tab => {
    if (chrome.runtime.lastError) return;
    tabInfoBuffer[tabId] = { title: tab.title, url: tab.url };
  });
});

// Handle messages from content script
chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "INTERACTION_UPDATE") {
    interactionBuffer[activeTabId] = {
      scroll: msg.scrollCount,
      key: msg.keyCount
    };

    // Keep longest non-empty content seen for this tab
    if (msg.content && msg.content.length > (contentBuffer[activeTabId] || "").length) {
      contentBuffer[activeTabId] = msg.content;
    }

    // Keep tabInfoBuffer current with latest title/url from content script
    if (msg.title && msg.url) {
      tabInfoBuffer[activeTabId] = { title: msg.title, url: msg.url };
    }
  } else if (msg.type === "URL_CHANGED") {
    endCurrentSession();
    sessionStart = Date.now();

    interactionBuffer[activeTabId] = { scroll: 0, key: 0 };
    // Reset content buffer on URL change — new page, fresh content incoming
    contentBuffer[activeTabId] = "";

    if (msg.content && msg.content.length > 0) {
      contentBuffer[activeTabId] = msg.content;
    }
    if (msg.title && msg.url) {
      tabInfoBuffer[activeTabId] = { title: msg.title, url: msg.url };
    }
  }
});

// Track tab close — use tabInfoBuffer so title/url are always present
chrome.tabs.onRemoved.addListener(tabId => {
  if (tabId === activeTabId && sessionStart) {
    const info = tabInfoBuffer[tabId] || {};
    sendEvent({
      type: "PAGE_SESSION",
      title: info.title || "",
      url: info.url || "",
      content: contentBuffer[tabId] || "",
      durationMs: Date.now() - sessionStart,
      scrollCount: interactionBuffer[tabId]?.scroll || 0,
      keyCount: interactionBuffer[tabId]?.key || 0,
      timestamp: Date.now()
    });

    delete interactionBuffer[tabId];
    delete contentBuffer[tabId];
    delete tabInfoBuffer[tabId];
    activeTabId = null;
    sessionStart = null;
  }
});
