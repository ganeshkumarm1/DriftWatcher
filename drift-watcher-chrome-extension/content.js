let scrollCount = 0;
let keyCount = 0;
let lastUrl = location.href;
let pendingContentExtraction = null;

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
  const body = document.body;
  if (!body) return "";

  // Try semantic containers first — avoids nav/header junk at top of body
  const semanticSelectors = ['main', '[role="main"]', 'article', '.content', '#content', '#main'];
  let sourceEl = null;
  for (const sel of semanticSelectors) {
    const el = document.querySelector(sel);
    if (el) { sourceEl = el; break; }
  }

  // Fall back to full body if no semantic element found
  const clone = (sourceEl || body).cloneNode(true);
  const unwanted = clone.querySelectorAll('script, style, nav, header, footer, iframe, noscript');
  unwanted.forEach(el => el.remove());

  // Prefer h1 + first paragraphs as a denser signal
  const h1 = clone.querySelector('h1');
  const paragraphs = Array.from(clone.querySelectorAll('p')).slice(0, 5);
  let priorityText = '';
  if (h1) priorityText += (h1.innerText || h1.textContent || '') + ' ';
  paragraphs.forEach(p => { priorityText += (p.innerText || p.textContent || '') + ' '; });

  let text = priorityText.trim() || (clone.innerText || clone.textContent || '');
  text = text.replace(/\s+/g, ' ').trim();
  return text.substring(0, 500);
}

function extractAndSendContent(isUrlChange = false) {
  // Delay 2s so SPAs have time to render dynamic content
  if (pendingContentExtraction) clearTimeout(pendingContentExtraction);
  pendingContentExtraction = setTimeout(() => {
    const content = extractPageContent();
    safeSendMessage({
      type: "INTERACTION_UPDATE",
      scrollCount: 0,
      keyCount: 0,
      title: document.title,
      url: location.href,
      content,
      timestamp: Date.now()
    });
    pendingContentExtraction = null;
  }, 2000);
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

  const urlChanged = location.href !== lastUrl;
  if (urlChanged) {
    lastUrl = location.href;

    safeSendMessage({
      type: "URL_CHANGED",
      title: document.title,
      url: location.href,
      content: "",  // content will arrive via delayed extraction below
      timestamp: Date.now()
    });

    // Trigger delayed content extraction for new SPA page
    extractAndSendContent(true);
  }

  safeSendMessage({
    type: "INTERACTION_UPDATE",
    scrollCount,
    keyCount,
    title: document.title,
    url: location.href,
    timestamp: Date.now()
    // no content here — content sent separately via extractAndSendContent
  });

  scrollCount = 0;
  keyCount = 0;

  setTimeout(sendInteractionUpdate, 5000);
}

// Initial delayed content extraction on page load
extractAndSendContent();

// Start interaction tracking
sendInteractionUpdate();
