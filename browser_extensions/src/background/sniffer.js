/**
 * PyIDM Media Stream Sniffer
 * Intercepts .m3u8 (HLS) and .mpd (DASH) requests and correlates them with active tabs.
 */

const STREAM_PATTERNS = [
  /\.(m3u8)(\?.*)?$/i,
  /\.(mpd)(\?.*)?$/i,
];

// In-memory tab stream cache (persisted in chrome.storage.session when available)
const tabStreamMap = new Map();

function initStreamSniffer(onStreamDetectedCallback) {
  if (!chrome.webRequest || !chrome.webRequest.onBeforeRequest) {
    return;
  }

  chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
      if (details.tabId < 0) return;

      const url = details.url;
      const isStream = STREAM_PATTERNS.some((pat) => pat.test(url));
      if (!isStream) return;

      const streamType = /\.m3u8/i.test(url) ? "HLS" : "DASH";
      const existing = tabStreamMap.get(details.tabId) || [];
      if (!existing.some((s) => s.url === url)) {
        existing.push({ url, type: streamType });
        tabStreamMap.set(details.tabId, existing);

        if (onStreamDetectedCallback) {
          onStreamDetectedCallback(details.tabId, url, streamType);
        }
      }
    },
    { urls: ["<all_urls>"] }
  );

  chrome.tabs.onRemoved.addListener((tabId) => {
    tabStreamMap.delete(tabId);
  });
}

function getTabStreams(tabId) {
  return tabStreamMap.get(tabId) || [];
}

