// Background service worker for PyIDM Chrome / Firefox Extension
const PYIDM_API_URL = "http://127.0.0.1:8743/api/v1/downloads";
const API_KEY = "pyidm-local-dev-secret-key-256";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "pyidm_download_link",
    title: "Download with PyIDM",
    contexts: ["link"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "pyidm_download_link" && info.linkUrl) {
    sendDownloadToPyIDM(info.linkUrl);
  }
});

async function sendDownloadToPyIDM(url) {
  try {
    const response = await fetch(PYIDM_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-PyIDM-Key": API_KEY
      },
      body: JSON.stringify({ url: url })
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Enqueued to PyIDM:", data);
    } else {
      console.error("PyIDM rejected request:", response.status);
    }
  } catch (err) {
    console.error("PyIDM application appears to be offline.", err);
  }
}

