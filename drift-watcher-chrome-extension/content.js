let scrollCount = 0;
let keyCount = 0;
let lastUrl = location.href;

function contextAlive() {
  return !!(chrome && chrome.runtime && chrome.runtime.id);
}

function safeSendMessage(payload) {
  if (!contextAlive()) return;
  try {
    chrome.runtime.sendMessage(payload);
  } catch (_) {
    // Extension context invalidated
  }
}

function extractPageContent() {
  // Extract meaningful text content from the page
  const body = document.body;
  if (!body) return "";
  
  // Remove script, style, and other non-content elements
  const clone = body.cloneNode(true);
  const unwanted = clone.querySelectorAll('script, style, nav, header, footer, iframe, noscript');
  unwanted.forEach(el => el.remove());
  
  // Get text content
  let text = clone.innerText || clone.textContent || "";
  
  // Clean up whitespace
  text = text.replace(/\s+/g, ' ').trim();
  
  // Limit to first 500 characters for efficiency
  return text.substring(0, 500);
}

// Track scroll events
window.addEventListener("scroll", () => {
  scrollCount++;
}, { passive: true });

// Track keyboard events
window.addEventListener("keydown", () => {
  keyCount++;
}, { passive: true });

// Send interaction updates and check for URL changes
function sendInteractionUpdate() {
  if (!contextAlive()) return;

  // Check for URL changes (SPA navigation like YouTube Shorts)
  const urlChanged = location.href !== lastUrl;
  if (urlChanged) {
    lastUrl = location.href;
    
    safeSendMessage({
      type: "URL_CHANGED",
      title: document.title,
      url: location.href,
      content: extractPageContent(),
      timestamp: Date.now()
    });
  }

  safeSendMessage({
    type: "INTERACTION_UPDATE",
    scrollCount,
    keyCount,
    title: document.title,
    url: location.href,
    content: urlChanged ? extractPageContent() : undefined,
    timestamp: Date.now()
  });

  scrollCount = 0;
  keyCount = 0;

  setTimeout(sendInteractionUpdate, 5000);
}

// Start tracking
sendInteractionUpdate();
