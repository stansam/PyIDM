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
        size_str: option.size_str,
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

    const refreshStreams = () => {
      chrome.runtime.sendMessage({ action: "QUERY_TAB_STREAMS" }, (response) => {
        if (response) {
          if (Array.isArray(response.variants) && response.variants.length > 0) {
            overlay.setVariants(response.variants);
          }
          if (Array.isArray(response.media) && response.media.length > 0) {
            overlay.setMedia(response.media);
          }
        }
      });
    };

    videoEl.addEventListener("loadedmetadata", () => {
      overlay.updatePosition();
      refreshStreams();
    });

    videoEl.addEventListener("play", () => {
      refreshStreams();
    });

    refreshStreams();
  }

  function scanForVideos(rootNode = document) {
    const videos = rootNode.querySelectorAll("video");
    for (const v of videos) {
      handleVideo(v);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => scanForVideos());
  } else {
    scanForVideos();
  }

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

  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "STREAM_VARIANTS_UPDATED" && message.variants) {
      const allVideos = document.querySelectorAll("video");
      for (const v of allVideos) {
        const overlay = activeOverlays.get(v);
        if (overlay) {
          overlay.setVariants(message.variants);
        }
      }
    } else if (message.action === "MEDIA_SNIFFED" && message.mediaItem) {
      const allVideos = document.querySelectorAll("video");
      for (const v of allVideos) {
        const overlay = activeOverlays.get(v);
        if (overlay) {
          const current = overlay.media || [];
          if (!current.some((m) => m.url === message.mediaItem.url)) {
            overlay.setMedia([message.mediaItem, ...current]);
          }
        }
      }
    }
  });
})();
