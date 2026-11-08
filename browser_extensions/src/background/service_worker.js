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
  const port = connectNativePort();
  const reqId = `req_${++requestCounter}`;
  message.request_id = reqId;

  if (port) {
    if (callback) pendingRequests.set(reqId, callback);
    try {
      port.postMessage(message);
      return;
    } catch (err) {
      nativePort = null;
    }
  }

  // Fallback to local HTTP loopback API if Native Messaging is unavailable
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
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (callback) callback({ type: "DOWNLOAD_ACCEPTED", ...data });
      })
      .catch((err) => {
        if (callback) callback({ type: "DOWNLOAD_REJECTED", reason: err.message });
      });
  }
}

// Initialize stream sniffer
initStreamSniffer((tabId, url, streamType) => {
  // Ask native host to parse variants
  sendNativeOrFallback(
    {
      type: "PARSE_MANIFEST",
      url: url,
    },
    (resp) => {
      if (resp && resp.variants && resp.variants.length > 0) {
        chrome.tabs.sendMessage(tabId, {
          action: "STREAM_VARIANTS_UPDATED",
          variants: resp.variants,
        }).catch(() => {});
      }
    }
  );
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
    const streams = getTabStreams(tabId);
    sendResponse({ streams });
  }
});

