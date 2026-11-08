/**
 * PyIDM Floating Video Overlay Manager
 * Encapsulated inside a closed Shadow DOM to avoid host CSS pollution.
 */

class PyIDMVideoOverlay {
  constructor(videoElement, onDownloadOptionSelected) {
    this.video = videoElement;
    this.onSelect = onDownloadOptionSelected;
    this.variants = [];
    this.media = [];
    this.isMenuOpen = false;

    this.hostElement = document.createElement("div");
    this.hostElement.className = "pyidm-overlay-root";
    this.shadow = this.hostElement.attachShadow({ mode: "closed" });

    this.pillBtn = null;
    this.menuEl = null;

    this.render();
    this.attachEvents();
    this.updatePosition();
  }

  render() {
    this.shadow.innerHTML = `
      <style>
        :host {
          all: initial;
          position: absolute;
          z-index: 2147483647;
          pointer-events: auto;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          user-select: none;
        }
        .pyidm-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: linear-gradient(135deg, #1e293b, #0f172a);
          color: #f8fafc;
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.1);
          border: none;
          outline: none;
          transition: all 0.2s ease;
        }
        .pyidm-pill:hover {
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          box-shadow: 0 6px 16px rgba(37,99,235,0.4), 0 0 0 1px rgba(255,255,255,0.2);
          transform: translateY(-1px);
        }
        .pyidm-pill.success {
          background: linear-gradient(135deg, #059669, #047857);
        }
        .pyidm-menu {
          position: absolute;
          top: calc(100% + 6px);
          right: 0;
          min-width: 320px;
          max-width: 440px;
          max-height: 380px;
          overflow-y: auto;
          overflow-x: hidden;
          background: #181825;
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.12);
          padding: 6px;
          display: none;
          flex-direction: column;
          gap: 4px;
        }
        .pyidm-menu::-webkit-scrollbar {
          width: 6px;
        }
        .pyidm-menu::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 3px;
        }
        .pyidm-menu.open {
          display: flex;
        }
        .pyidm-menu-header {
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          color: #94a3b8;
          padding: 6px 8px;
          border-bottom: 1px solid rgba(255,255,255,0.08);
          margin-bottom: 2px;
          letter-spacing: 0.5px;
        }
        .pyidm-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 10px;
          border-radius: 5px;
          color: #e2e8f0;
          cursor: pointer;
          font-size: 12px;
          transition: background 0.15s ease;
        }
        .pyidm-row:hover {
          background: #2563eb;
          color: #ffffff;
        }
        .pyidm-left {
          display: flex;
          align-items: center;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 230px;
        }
        .pyidm-q {
          font-weight: 700;
          color: #60a5fa;
          margin-right: 6px;
        }
        .pyidm-row:hover .pyidm-q {
          color: #ffffff;
        }
        .pyidm-fmt {
          font-size: 10px;
          text-transform: uppercase;
          background: rgba(255,255,255,0.1);
          padding: 2px 5px;
          border-radius: 3px;
          margin-right: 8px;
        }
        .pyidm-meta {
          font-size: 11px;
          color: #94a3b8;
          white-space: nowrap;
          margin-left: 8px;
        }
        .pyidm-row:hover .pyidm-meta {
          color: #e2e8f0;
        }
      </style>
      <button class="pyidm-pill" id="pyidm-main-btn">
        <span>📥 Download Video</span>
        <span id="pyidm-chevron">▼</span>
      </button>
      <div class="pyidm-menu" id="pyidm-dropdown">
        <div class="pyidm-menu-header">Available Download Options</div>
        <div id="pyidm-options-container"></div>
      </div>
    `;

    document.body.appendChild(this.hostElement);

    this.pillBtn = this.shadow.getElementById("pyidm-main-btn");
    this.menuEl = this.shadow.getElementById("pyidm-dropdown");
    this.optionsContainer = this.shadow.getElementById("pyidm-options-container");
    this.chevron = this.shadow.getElementById("pyidm-chevron");
  }

  attachEvents() {
    this.pillBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleMenu();
    });

    document.addEventListener("click", () => {
      if (this.isMenuOpen) {
        this.closeMenu();
      }
    });

    const update = () => this.updatePosition();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });

    if (window.ResizeObserver) {
      this.resizeObserver = new ResizeObserver(update);
      this.resizeObserver.observe(this.video);
    }

    document.addEventListener("fullscreenchange", update);
  }

  setVariants(variants) {
    if (Array.isArray(variants) && variants.length > 0) {
      this.variants = variants;
      this.populateMenu();
    }
  }

  setMedia(media) {
    if (Array.isArray(media)) {
      this.media = media;
      this.populateMenu();
    }
  }

  getCleanPageTitle() {
    const title = document.title || "Video";
    return title.split(" - YouTube")[0].split(" | ")[0].trim() || "Video";
  }

  populateMenu() {
    this.optionsContainer.innerHTML = "";
    const seenResolutions = new Set();
    const seenUrls = new Set();
    let optionsCount = 0;
    const maxOptions = 8;

    // 1. Manifest Quality Variants (HLS / DASH)
    if (this.variants && this.variants.length > 0) {
      for (const v of this.variants) {
        if (optionsCount >= maxOptions) break;
        const resKey = v.quality_label || v.resolution || v.id;
        if (seenResolutions.has(resKey) || seenUrls.has(v.url)) continue;
        seenResolutions.add(resKey);
        seenUrls.add(v.url);
        optionsCount++;

        let label = v.quality_label || "Auto";
        if (label === "1080p") label = "1080p Full HD";
        else if (label === "720p") label = "720p HD";
        else if (label === "480p") label = "480p SD";

        this.addOptionRow({
          quality: label,
          format: (v.container || "MP4").toUpperCase(),
          meta: v.resolution || (v.bitrate_bps ? `${Math.round(v.bitrate_bps / 1000)} kbps` : ""),
          url: v.url,
          title: `${this.getCleanPageTitle()} (${v.quality_label || "video"})`,
          variantData: v,
        });
      }
    }

    // 2. Standalone Media Files (.mp4, .webm) from Sniffer
    if (this.media && this.media.length > 0) {
      for (const m of this.media) {
        if (optionsCount >= maxOptions) break;
        if (seenUrls.has(m.url)) continue;
        seenUrls.add(m.url);
        optionsCount++;

        const label = m.title || (this.video.videoHeight ? `${this.video.videoHeight}p` : "Direct Video");
        this.addOptionRow({
          quality: label,
          format: (m.format || "MP4").toUpperCase(),
          meta: m.sizeStr || "Full Video",
          url: m.url,
          title: this.getCleanPageTitle(),
        });
      }
    }

    // 3. Child <source> Elements
    const sources = this.video.querySelectorAll("source");
    for (const s of sources) {
      if (optionsCount >= maxOptions) break;
      const sUrl = s.src || s.getAttribute("src");
      if (sUrl && !sUrl.startsWith("blob:") && !seenUrls.has(sUrl)) {
        seenUrls.add(sUrl);
        optionsCount++;

        const ext = sUrl.split(".").pop().split("?")[0] || "mp4";
        const res = this.video.videoHeight ? `${this.video.videoHeight}p` : "Source";

        this.addOptionRow({
          quality: res,
          format: ext.toUpperCase(),
          meta: "HTML5 Source",
          url: sUrl,
          title: this.getCleanPageTitle(),
        });
      }
    }

    // 4. Video.currentSrc / Video.src (Direct Progressive)
    const currentSrc = this.video.currentSrc || this.video.src || this.video.getAttribute("src");
    if (currentSrc && !currentSrc.startsWith("blob:") && !seenUrls.has(currentSrc)) {
      if (optionsCount < maxOptions) {
        seenUrls.add(currentSrc);
        optionsCount++;

        const ext = currentSrc.split(".").pop().split("?")[0] || "mp4";
        const res = this.video.videoHeight ? `${this.video.videoHeight}p` : "Standard";

        this.addOptionRow({
          quality: res,
          format: ext.toUpperCase(),
          meta: "Direct Media",
          url: currentSrc,
          title: this.getCleanPageTitle(),
        });
      }
    }

    // 5. Fallback for MSE / Blob players when direct URL is inaccessible
    if (optionsCount === 0) {
      const res = this.video.videoHeight ? `${this.video.videoHeight}p HD` : "Detected Video";
      this.addOptionRow({
        quality: res,
        format: "MP4",
        meta: "Stream URL",
        url: window.location.href,
        title: this.getCleanPageTitle(),
      });
    }
  }

  addOptionRow({ quality, format, meta, url, title, variantData }) {
    const row = document.createElement("div");
    row.className = "pyidm-row";
    row.innerHTML = `
      <div class="pyidm-left">
        <span class="pyidm-q">${quality}</span>
        <span class="pyidm-fmt">${format}</span>
      </div>
      <div class="pyidm-meta">${meta}</div>
    `;

    row.addEventListener("click", (e) => {
      e.stopPropagation();
      this.closeMenu();
      this.showSuccess();
      if (this.onSelect) {
        this.onSelect({
          url: url,
          title: title || this.getCleanPageTitle(),
          container: format.toLowerCase(),
          quality: quality,
          size_str: meta,
          variant: variantData,
        });
      }
    });

    this.optionsContainer.appendChild(row);
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    if (this.isMenuOpen) {
      chrome.runtime.sendMessage({ action: "QUERY_TAB_STREAMS" }, (response) => {
        if (response) {
          if (Array.isArray(response.variants) && response.variants.length > 0) {
            this.variants = response.variants;
          }
          if (Array.isArray(response.media) && response.media.length > 0) {
            this.media = response.media;
          }
        }
        this.populateMenu();
      });

      this.populateMenu();
      this.menuEl.classList.add("open");
      this.chevron.innerText = "▲";
    } else {
      this.closeMenu();
    }
  }

  closeMenu() {
    this.isMenuOpen = false;
    this.menuEl.classList.remove("open");
    this.chevron.innerText = "▼";
  }

  showSuccess() {
    const oldHtml = this.pillBtn.innerHTML;
    this.pillBtn.classList.add("success");
    this.pillBtn.innerHTML = `<span>Sent to PyIDM ✓</span>`;
    setTimeout(() => {
      this.pillBtn.classList.remove("success");
      this.pillBtn.innerHTML = oldHtml;
      this.chevron = this.shadow.getElementById("pyidm-chevron");
    }, 2500);
  }

  updatePosition() {
    if (!this.video || !document.contains(this.video)) {
      this.destroy();
      return;
    }

    const rect = this.video.getBoundingClientRect();
    if (rect.width < 120 || rect.height < 90 || rect.bottom < 0 || rect.top > window.innerHeight) {
      this.hostElement.style.display = "none";
      return;
    }

    this.hostElement.style.display = "block";
    const top = window.scrollY + rect.top + 12;
    const left = window.scrollX + rect.right - 150;

    this.hostElement.style.top = `${top}px`;
    this.hostElement.style.left = `${Math.max(window.scrollX + rect.left + 10, left)}px`;
  }

  destroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.hostElement && this.hostElement.parentNode) {
      this.hostElement.parentNode.removeChild(this.hostElement);
    }
  }
}

if (typeof window !== "undefined") {
  window.PyIDMVideoOverlay = PyIDMVideoOverlay;
}
