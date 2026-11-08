/**
 * PyIDM Media Stream & File Sniffer
 * Intercepts media manifests (.m3u8, .mpd) and standalone media files (.mp4, .webm)
 * while filtering out fragmented 2-second streaming chunks.
 */

const MANIFEST_PATTERNS = /\.(m3u8|mpd)(\?.*)?$/i;
const STANDALONE_VIDEO_PATTERNS = /\.(mp4|webm|mkv|mov|m4v)(\?.*)?$/i;

// Patterns representing transient 2-second stream fragments or chunk ranges
const CHUNK_PATTERNS = /(\.(ts|m4s|mp4frag)(\?|$)|[?&]range=\d+-\d+|\/frag\(\d+\)|\/segment-\d+|\/seg-\d+|\/chunk-\d+|init\.(mp4|m4s))/i;

// In-memory tab media registry: tabId -> Array<{ url, type, format, sizeStr, sizeBytes, quality, title }>
const tabMediaMap = new Map();

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  let val = bytes;
  let unitIndex = 0;
  while (val >= 1024 && unitIndex < units.length - 1) {
    val /= 1024;
    unitIndex++;
  }
  return `~${val.toFixed(1)} ${units[unitIndex]}`;
}

function extractCleanFilename(url) {
  try {
    const pathname = new URL(url).pathname;
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length > 0) {
      const last = decodeURIComponent(parts[parts.length - 1]);
      if (last.length > 3 && last.includes(".")) {
        return last;
      }
    }
  } catch (e) {}
  return "";
}

function initStreamSniffer(onStreamDetectedCallback) {
  if (!chrome.webRequest) {
    return;
  }

  // 1. Observe URLs before request
  if (chrome.webRequest.onBeforeRequest) {
    chrome.webRequest.onBeforeRequest.addListener(
      (details) => {
        if (details.tabId < 0) return;
        const url = details.url;

        // Ignore stream fragments
        if (CHUNK_PATTERNS.test(url)) {
          return;
        }

        // Capture manifests (.m3u8, .mpd)
        if (MANIFEST_PATTERNS.test(url) || url.includes("/manifest/hls") || url.includes("/manifest/dash")) {
          const isHls = url.includes(".m3u8") || url.includes("/hls");
          const type = isHls ? "HLS" : "DASH";

          addMediaToTab(
            details.tabId,
            {
              url: url,
              type: type,
              format: type,
              quality: isHls ? "HLS Multi-Quality" : "DASH Multi-Quality",
              sizeStr: "Master Playlist",
              sizeBytes: 0,
              title: extractCleanFilename(url),
            },
            onStreamDetectedCallback
          );
        }
      },
      { urls: ["<all_urls>"] }
    );
  }

  // 2. Observe Response Headers for standalone media files and Content-Length
  if (chrome.webRequest.onHeadersReceived) {
    chrome.webRequest.onHeadersReceived.addListener(
      (details) => {
        if (details.tabId < 0 || !details.responseHeaders) return;

        const url = details.url;
        // Ignore chunk fragments
        if (CHUNK_PATTERNS.test(url)) {
          return;
        }

        let contentType = "";
        let contentLength = 0;

        for (const h of details.responseHeaders) {
          const name = h.name.toLowerCase();
          if (name === "content-type") {
            contentType = h.value || "";
          } else if (name === "content-length") {
            contentLength = parseInt(h.value || "0", 10) || 0;
          }
        }

        const isManifestMime =
          contentType.includes("application/x-mpegurl") ||
          contentType.includes("application/vnd.apple.mpegurl") ||
          contentType.includes("application/dash+xml");

        if (isManifestMime) {
          const isHls = contentType.includes("mpegurl") || url.includes(".m3u8");
          const type = isHls ? "HLS" : "DASH";

          addMediaToTab(
            details.tabId,
            {
              url: url,
              type: type,
              format: type,
              quality: isHls ? "HLS Multi-Quality" : "DASH Multi-Quality",
              sizeStr: "Master Playlist",
              sizeBytes: 0,
              title: extractCleanFilename(url),
            },
            onStreamDetectedCallback
          );
          return;
        }

        // For progressive media files: only capture if standalone (>= 1MB or recognized video file)
        const isVideoMime = contentType.startsWith("video/") || STANDALONE_VIDEO_PATTERNS.test(url);
        if (isVideoMime && (contentLength >= 1000000 || contentLength === 0)) {
          const ext = url.split("?")[0].split(".").pop().toUpperCase() || "MP4";
          const format = ext.length <= 4 ? ext : "MP4";

          addMediaToTab(
            details.tabId,
            {
              url: url,
              type: "PROGRESSIVE",
              format: format,
              quality: "Progressive Video",
              sizeStr: formatBytes(contentLength),
              sizeBytes: contentLength,
              title: extractCleanFilename(url),
            },
            onStreamDetectedCallback
          );
        }
      },
      { urls: ["<all_urls>"] },
      ["responseHeaders"]
    );
  }

  chrome.tabs.onRemoved.addListener((tabId) => {
    tabMediaMap.delete(tabId);
  });
}

function addMediaToTab(tabId, mediaItem, callback) {
  const existing = tabMediaMap.get(tabId) || [];
  const foundIndex = existing.findIndex((m) => m.url === mediaItem.url);

  if (foundIndex >= 0) {
    if (!existing[foundIndex].sizeStr && mediaItem.sizeStr) {
      existing[foundIndex].sizeStr = mediaItem.sizeStr;
      existing[foundIndex].sizeBytes = mediaItem.sizeBytes;
    }
  } else {
    // Keep max 10 distinct standalone streams per tab
    if (existing.length >= 10) {
      existing.shift();
    }
    existing.push(mediaItem);
    tabMediaMap.set(tabId, existing);

    if (callback) {
      callback(tabId, mediaItem.url, mediaItem.type, mediaItem);
    }
  }
}

function getTabMedia(tabId) {
  return tabMediaMap.get(tabId) || [];
}


/**
 * PyIDM Extension Background Service Worker
 * Bridges Content Scripts to Desktop App via Native Messaging (or local loopback fallback).
 */

const NATIVE_HOST_NAME = "com.pyidm.native.host";
const FALLBACK_API_URL = "http://127.0.0.1:8743/api/v1/downloads";
const FALLBACK_API_KEY = "pyidm-local-dev-secret-key-256";

let nativePort = null;
const pendingRequests = new Map();
let requestCounter = 0;

// Tab ID -> Array<MediaVariant>
const tabVariantsMap = new Map();

function connectNativePort() {
  if (nativePort) return nativePort;

  try {
    nativePort = chrome.runtime.connectNative(NATIVE_HOST_NAME);
    nativePort.onMessage.addListener(handleNativeMessage);
    nativePort.onDisconnect.addListener(() => {
      nativePort = null;
    });
  } catch (err) {
    nativePort = null;
  }
  return nativePort;
}

function handleNativeMessage(response) {
  const reqId = response.request_id;
  if (reqId && pendingRequests.has(reqId)) {
    const callback = pendingRequests.get(reqId);
    pendingRequests.delete(reqId);
    callback(response);
  }
}

function sendNativeOrFallback(message, callback) {
  const reqId = `req_${++requestCounter}`;
  message.request_id = reqId;

  // 1. Try local HTTP loopback API first (communicates directly with running GUI)
  if (message.type === "ENQUEUE_MEDIA_DOWNLOAD" || message.type === "ENQUEUE_DOWNLOAD") {
    fetch(FALLBACK_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-PyIDM-Key": FALLBACK_API_KEY,
      },
      body: JSON.stringify({
        url: message.url,
        filename: message.title ? `${message.title}.${message.container || "mp4"}` : null,
        headers: message.headers || {},
        page_url: message.page_url || "",
        size_str: message.size_str || message.quality || "",
      }),
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (callback) callback({ type: "DOWNLOAD_ACCEPTED", ...data });
      })
      .catch(() => {
        // 2. If GUI loopback API is offline, fall back to Native Messaging host
        const port = connectNativePort();
        if (port) {
          if (callback) pendingRequests.set(reqId, callback);
          try {
            port.postMessage(message);
          } catch (err) {
            nativePort = null;
            if (callback) callback({ type: "DOWNLOAD_REJECTED", reason: "Native host disconnected" });
          }
        } else if (callback) {
          callback({ type: "DOWNLOAD_REJECTED", reason: "PyIDM desktop app is not running" });
        }
      });
    return;
  }

  // For non-download messages (e.g. PARSE_MANIFEST), route via native host
  const port = connectNativePort();
  if (port) {
    if (callback) pendingRequests.set(reqId, callback);
    try {
      port.postMessage(message);
    } catch (err) {
      nativePort = null;
    }
  }
}

// Initialize stream sniffer
initStreamSniffer((tabId, url, mediaType, mediaItem) => {
  if (mediaType === "HLS" || mediaType === "DASH") {
    // Attempt fetching manifest content directly in extension context with cookies
    fetch(url)
      .then((res) => (res.ok ? res.text() : ""))
      .catch(() => "")
      .then((manifestText) => {
        sendNativeOrFallback(
          {
            type: "PARSE_MANIFEST",
            url: url,
            content: manifestText || "",
          },
          (resp) => {
            if (resp && resp.variants && resp.variants.length > 0) {
              const current = tabVariantsMap.get(tabId) || [];
              tabVariantsMap.set(tabId, resp.variants.concat(current));

              chrome.tabs
                .sendMessage(tabId, {
                  action: "STREAM_VARIANTS_UPDATED",
                  variants: resp.variants,
                })
                .catch(() => {});
            }
          }
        );
      });
  } else {
    // Progressive media file captured
    chrome.tabs
      .sendMessage(tabId, {
        action: "MEDIA_SNIFFED",
        mediaItem: mediaItem,
      })
      .catch(() => {});
  }
});

// Clean up tabs
chrome.tabs.onRemoved.addListener((tabId) => {
  tabVariantsMap.delete(tabId);
});

// Context Menu Setup
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "pyidm_download_link",
    title: "Download with PyIDM",
    contexts: ["link", "video", "audio"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const targetUrl = info.linkUrl || info.srcUrl;
  if (info.menuItemId === "pyidm_download_link" && targetUrl) {
    sendNativeOrFallback({
      type: "ENQUEUE_DOWNLOAD",
      url: targetUrl,
      page_url: tab ? tab.url : "",
    });
  }
});

// Content Script Message Handling
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "START_DOWNLOAD") {
    sendNativeOrFallback(
      {
        type: "ENQUEUE_MEDIA_DOWNLOAD",
        ...message.payload,
      },
      (res) => sendResponse(res)
    );
    return true; // Keep message channel open for async response
  } else if (message.action === "QUERY_TAB_STREAMS") {
    const tabId = sender.tab ? sender.tab.id : -1;
    const variants = tabVariantsMap.get(tabId) || [];
    const media = getTabMedia(tabId) || [];
    sendResponse({ variants, media });
  }
});
