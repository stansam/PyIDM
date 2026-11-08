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
