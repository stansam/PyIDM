/**
 * PyIDM Browser Content Script
 * Discovers video players in DOM, attaches isolated floating overlays, and listens for streams.
 */

(function () {
  const activeOverlays = new WeakMap();

  function onDownloadSelected(option) {
    chrome.runtime.sendMessage({
      action: "START_DOWNLOAD",
      payload: {
        url: option.url,
        title: option.title,
        container: option.container,
        quality: option.quality,
        page_url: window.location.href,
      },
    });
  }

  function handleVideo(videoEl) {
    if (activeOverlays.has(videoEl)) {
      return;
    }

    const overlay = new PyIDMVideoOverlay(videoEl, onDownloadSelected);
    activeOverlays.set(videoEl, overlay);

    // When metadata loads, populate resolutions
    videoEl.addEventListener("loadedmetadata", () => {
      overlay.updatePosition();
      overlay.populateMenu();
    });

    // Check if background script already detected streams for this tab
    chrome.runtime.sendMessage({ action: "QUERY_TAB_STREAMS" }, (response) => {
      if (response && response.variants && response.variants.length > 0) {
        overlay.setVariants(response.variants);
      }
    });
  }

  function scanForVideos(rootNode = document) {
    const videos = rootNode.querySelectorAll("video");
    for (const v of videos) {
      handleVideo(v);
    }
  }

  // Initial scan
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => scanForVideos());
  } else {
    scanForVideos();
  }

  // Dynamic DOM observation for SPAs (YouTube, Twitter, TikTok, etc.)
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          if (node.tagName === "VIDEO") {
            handleVideo(node);
          } else if (node.querySelectorAll) {
            scanForVideos(node);
          }
        }
      }
    }
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "STREAM_VARIANTS_UPDATED" && message.variants) {
      const allVideos = document.querySelectorAll("video");
      for (const v of allVideos) {
        const overlay = activeOverlays.get(v);
        if (overlay) {
          overlay.setVariants(message.variants);
        }
      }
    }
  });
})();
