/**
 * PyIDM Floating Video Overlay Manager
 * Encapsulated inside a closed Shadow DOM to avoid host CSS pollution.
 */

class PyIDMVideoOverlay {
  constructor(videoElement, onDownloadOptionSelected) {
    this.video = videoElement;
    this.onSelect = onDownloadOptionSelected;
    this.variants = [];
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
          min-width: 280px;
          background: #181825;
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.12);
          padding: 6px;
          display: none;
          flex-direction: column;
          gap: 4px;
        }
        .pyidm-menu.open {
          display: flex;
        }
        .pyidm-menu-header {
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          color: #94a3b8;
          padding: 4px 8px;
          border-bottom: 1px solid rgba(255,255,255,0.08);
          margin-bottom: 2px;
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

    // Close menu when clicking outside
    document.addEventListener("click", () => {
      if (this.isMenuOpen) {
        this.closeMenu();
      }
    });

    // Tracking positions
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
    this.variants = variants;
    this.populateMenu();
  }

  populateMenu() {
    this.optionsContainer.innerHTML = "";

    if (!this.variants || this.variants.length === 0) {
      // Fallback single progressive option
      const src = this.video.currentSrc || this.video.src;
      if (src && !src.startsWith("blob:")) {
        const ext = src.split(".").pop().split("?")[0] || "mp4";
        const res = this.video.videoWidth ? `${this.video.videoWidth}x${this.video.videoHeight}` : "Standard";
        this.addOptionRow({
          quality: res,
          format: ext.toUpperCase(),
          meta: "Direct Stream",
          url: src,
        });
      }
      return;
    }

    for (const v of this.variants) {
      this.addOptionRow({
        quality: v.quality_label || "Auto",
        format: (v.container || "MP4").toUpperCase(),
        meta: v.resolution || (v.bitrate_bps ? `${Math.round(v.bitrate_bps / 1000)} kbps` : ""),
        url: v.url,
        variantData: v,
      });
    }
  }

  addOptionRow({ quality, format, meta, url, variantData }) {
    const row = document.createElement("div");
    row.className = "pyidm-row";
    row.innerHTML = `
      <div>
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
          title: document.title || "Video Download",
          container: format.toLowerCase(),
          quality: quality,
          variant: variantData,
        });
      }
    });

    this.optionsContainer.appendChild(row);
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    if (this.isMenuOpen) {
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
    const oldText = this.pillBtn.innerHTML;
    this.pillBtn.classList.add("success");
    this.pillBtn.innerHTML = `<span>Sent to PyIDM ✓</span>`;
    setTimeout(() => {
      this.pillBtn.classList.remove("success");
      this.pillBtn.innerHTML = oldText;
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
    const left = window.scrollX + rect.right - 150; // Align near upper right

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
